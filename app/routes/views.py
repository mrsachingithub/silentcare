from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, db
from datetime import datetime

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    return render_template('index.html')

@views_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('views.dashboard'))
        return redirect(url_for('views.patient_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('views.login'))
            
        login_user(user, remember=remember)
        if user.role == 'admin':
            return redirect(url_for('views.dashboard'))
        return redirect(url_for('views.patient_dashboard'))
        
    return render_template('login.html')

@views_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('views.signup'))
            
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'warning')
            return redirect(url_for('views.signup'))
            
        new_user = User(username=username, role='patient')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('views.patient_dashboard'))
        
    return render_template('signup.html')

@views_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.index'))

@views_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('views.patient_dashboard'))
    return render_template('dashboard.html', user=current_user)

@views_bp.route('/patient-dashboard')
@login_required
def patient_dashboard():
    # Pass department stats directly to template
    from app.models import OPDQueue
    from app.ml.predictor import WaitingDurationPredictor
    predictor = WaitingDurationPredictor()
    
    depts_list = ['General', 'Ortho', 'ENT', 'Cardiology', 'Pediatrics']
    departments_data = []
    
    for d_name in depts_list:
        latest = OPDQueue.query.filter_by(department=d_name).order_by(OPDQueue.timestamp.desc()).first()
        
        dept_info = {
            'name': d_name,
            'patients_waiting': 0,
            'active_doctors': 0,
            'avg_time': 0,
            'wait_time': 0,
            'crowd_status': 'Low',
            'is_crowded': False
        }
        
        if latest:
            dept_info['patients_waiting'] = latest.patients_waiting
            dept_info['active_doctors'] = latest.active_doctors
            dept_info['avg_time'] = latest.avg_consultation_time
            
            # Predict
            # Predict
            if not predictor.is_trained: predictor.train()
            wait = predictor.predict(latest.patients_waiting, latest.active_doctors)
            
            # Convert to Hours/Minutes string
            wait_min = int(round(wait))
            if wait_min >= 60:
                hrs = wait_min // 60
                mins = wait_min % 60
                if mins > 0:
                    dept_info['wait_time'] = f"{hrs} hr {mins} min"
                else:
                    dept_info['wait_time'] = f"{hrs} hr"
            else:
                dept_info['wait_time'] = f"{wait_min} min"
            
            if wait > 45: 
                dept_info['crowd_status'] = 'High'
                dept_info['is_crowded'] = True
            elif wait > 25:
                dept_info['crowd_status'] = 'Medium'
        
        # Generate random best time between 9:00 AM and 4:00 PM
        import random
        from datetime import timedelta
        
        start_hour = 9
        end_hour = 16 # 4 PM
        
        random_minutes = random.randint(0, (end_hour - start_hour) * 4) * 15
        best_time = datetime.strptime('09:00', '%H:%M') + timedelta(minutes=random_minutes)
        dept_info['best_slot'] = best_time.strftime('%I:%M %p')
        
        departments_data.append(dept_info)
        
    return render_template('patient_dashboard.html', user=current_user, departments=departments_data, now=datetime.now().strftime('%d %b, %I:%M %p'))

@views_bp.route('/patient')
def patient_view():
    # Older public view, maybe redirect to login or keep as "Quick View"
    return render_template('patient_view.html')

@views_bp.route('/data-entry')
@login_required
def data_entry():
    return render_template('data_entry.html', user=current_user)


@views_bp.route('/upload-history')
@login_required
def upload_history():
    return render_template('upload_history.html', user=current_user)

@views_bp.route('/about')
def about():
    return render_template('about.html')

@views_bp.route('/contact')
def contact():
    return render_template('contact.html')
