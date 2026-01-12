import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from app.models import OPDQueue
from datetime import datetime, timedelta

class WaitingDurationPredictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
        self.feature_columns = ['patients_waiting', 'active_doctors', 'hour', 'day_of_week']

    def train(self):
        records = OPDQueue.query.all()
        if not records:
            return False
        
        data = []
        for r in records:
            d = r.to_dict()
            # Derive features
            dt = datetime.fromisoformat(d['timestamp'])
            d['hour'] = dt.hour
            d['day_of_week'] = dt.weekday() # 0=Mon, 6=Sun
            # Target proxy
            d['estimated_wait'] = (d['patients_waiting'] * d['avg_consultation_time']) / (d['active_doctors'] if d['active_doctors'] > 0 else 1)
            data.append(d)
            
        df = pd.DataFrame(data)
        
        X = df[self.feature_columns]
        y = df['estimated_wait']
        
        self.model.fit(X, y)
        self.is_trained = True
        return True

    def predict(self, patients_waiting, active_doctors, timestamp=None):
        if not self.is_trained:
            # Fallback heuristic
            if active_doctors == 0: return 0
            return (patients_waiting * 10) / active_doctors
        
        if timestamp is None:
            timestamp = datetime.now()
            
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        
        features = pd.DataFrame([[patients_waiting, active_doctors, hour, day_of_week]], columns=self.feature_columns)
        return self.model.predict(features)[0]

    def predict_future_slots(self, department, hours=24):
        """Generates hourly wait time forecast for the next `hours`."""
        if not self.is_trained:
            self.train()
            
        forecasts = []
        current_time = datetime.now()
        # Assume constant doctors/patients for simplicity or use moving average?
        # Better: Use historical average for that specific hour/day (baseline)
        # For prototype, we'll assume 'average' load:
        # active_doctors = 3, patients_waiting = varies by hour (mocked pattern)
        
        for i in range(hours):
            future_time = current_time + timedelta(hours=i)
            hour = future_time.hour
            
            # Simulated load pattern based on hour
            mock_patients = 5
            if 9 <= hour <= 12: mock_patients = 25 # Peak
            elif 13 <= hour <= 16: mock_patients = 15
            elif 17 <= hour <= 20: mock_patients = 10
            
            # Predict
            wait_time = self.predict(mock_patients, 3, future_time)
            
            # Crowd Intensity
            intensity = "Low"
            if wait_time > 60: intensity = "High"
            elif wait_time > 30: intensity = "Medium"
            
            forecasts.append({
                'time': future_time.strftime('%I:%M %p'),
                'wait_time': round(wait_time, 1),
                'intensity': intensity,
                'is_peak': intensity == "High"
            })
            
        return forecasts
