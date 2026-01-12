from flask import Blueprint, request, jsonify
from app import db
from app.models import OPDQueue, SilentIssue
from datetime import datetime, timedelta
from app.ml.predictor import WaitingDurationPredictor
from app.ml.anomaly import SilentIssueDetector
import pandas as pd
import io

api_bp = Blueprint('api', __name__)

# Initialize ML modules
# ... (rest of init code) ...

@api_bp.route('/queue/upload', methods=['POST'])
def upload_queue_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    try:
        # Read CSV directly into dataframe
        df = pd.read_csv(file)
        
        # Validate columns
        required_cols = ['department', 'patients_waiting', 'active_doctors', 'avg_consultation_time']
        if not all(col in df.columns for col in required_cols):
            return jsonify({'error': f'Missing columns. Required: {required_cols}'}), 400
            
        count = 0
        for _, row in df.iterrows():
            new_entry = OPDQueue(
                department=row['department'],
                patients_waiting=int(row['patients_waiting']),
                active_doctors=int(row['active_doctors']),
                avg_consultation_time=float(row['avg_consultation_time'])
            )
            # Optional: Add timestamp if provided in CSV, else default to now
            if 'timestamp' in row:
                try:
                    new_entry.timestamp = datetime.fromisoformat(str(row['timestamp']))
                except:
                    pass
                    
            db.session.add(new_entry)
            count += 1
            
        db.session.commit()
        
        # Retrain model with new historical data
        predictor.train()
        
        # Trigger quick analysis on latest data point
        anomaly_detector.analyze_recent_data()
        
        return jsonify({'message': 'File processed successfully', 'count': count}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize ML modules
predictor = WaitingDurationPredictor()
# Train on startup (in real world, load pickled model)
with api_bp.open_resource('../../init_db.py') as f: # Hack to get app context? No, just do standard init
     # We can't easily train here without app context if DB is needed. 
     # We'll lazy load or train in the route for the prototype.
     pass

anomaly_detector = SilentIssueDetector()

@api_bp.route('/queue/update', methods=['POST'])
def update_queue():
    data = request.json
    try:
        # Basic validation
        if not all(k in data for k in ('department', 'patients_waiting', 'active_doctors', 'avg_consultation_time')):
            return jsonify({'error': 'Missing required fields'}), 400

        new_entry = OPDQueue(
            department=data['department'],
            patients_waiting=data['patients_waiting'],
            active_doctors=data['active_doctors'],
            avg_consultation_time=data['avg_consultation_time']
        )
        db.session.add(new_entry)
        db.session.commit()
        
        # Trigger analysis
        anomaly_detector.analyze_recent_data()
        
        return jsonify({'message': 'Queue data updated successfully', 'id': new_entry.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/prediction/wait-time', methods=['GET'])
def get_wait_time():
    dept = request.args.get('department')
    if not dept:
        return jsonify({'error': 'Department required'}), 400
    
    # Simple logic: get latest status of department to predict
    latest = OPDQueue.query.filter_by(department=dept).order_by(OPDQueue.timestamp.desc()).first()
    
    if not latest:
        return jsonify({'message': 'No data for department', 'predicted_wait_time_minutes': 0}), 200

    # Ensure model is trained (naively for demo)
    if not predictor.is_trained:
        predictor.train() # This fetches data from DB

    predicted_minutes = predictor.predict(latest.patients_waiting, latest.active_doctors)
    
    # Crowd intensity
    intensity = "Low"
    if predicted_minutes > 60: intensity = "High congestion"
    elif predicted_minutes > 30: intensity = "Medium"

    return jsonify({
        'department': dept,
        'predicted_wait_time_minutes': round(predicted_minutes, 1),
        'crowd_intensity': intensity
    })

@api_bp.route('/alerts', methods=['GET'])
def get_alerts():
    # Fetch unresolved alerts
    alerts = SilentIssue.query.filter_by(is_resolved=False).order_by(SilentIssue.timestamp.desc()).all()
    return jsonify([a.to_dict() for a in alerts])

@api_bp.route('/analytics/forecast', methods=['GET'])
def get_forecast():
    dept = request.args.get('department', 'General')
    # Train if needed
    if not predictor.is_trained:
        predictor.train() # In prod, load pre-trained
    
    forecasts = predictor.predict_future_slots(dept, hours=12)
    return jsonify(forecasts)

@api_bp.route('/analytics/heatmap', methods=['GET'])
def get_heatmap():
    # Mock aggregation for heatmap (Day vs Hour)
    # In real world: SQL Group By query
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    heatmap_data = []
    
    for day_idx, day_name in enumerate(days):
        day_row = {'name': day_name, 'data': []}
        for hour in range(9, 18): # 9 AM to 5 PM
            # Simulated "intensity" score 0-100
            intensity = 20 # Base
            if day_idx < 5: # Weekday
                if 10 <= hour <= 12: intensity = 85 # Peak
                elif 14 <= hour <= 16: intensity = 60
            else: # Weekend
                intensity = 40
                
            day_row['data'].append({
                'x': f"{hour}:00",
                'y': intensity
            })
        heatmap_data.append(day_row)
        
    return jsonify(heatmap_data)
