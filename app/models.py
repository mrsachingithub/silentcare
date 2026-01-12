from datetime import datetime
from app import db


class OPDQueue(db.Model):
    __tablename__ = 'sc_opd_queue'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    department = db.Column(db.String(50), nullable=False)
    patients_waiting = db.Column(db.Integer, nullable=False)
    active_doctors = db.Column(db.Integer, nullable=False)
    avg_consultation_time = db.Column(db.Float, nullable=False) # in minutes
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'department': self.department,
            'patients_waiting': self.patients_waiting,
            'active_doctors': self.active_doctors,
            'avg_consultation_time': self.avg_consultation_time
        }

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'sc_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='patient') # admin / patient
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class SilentIssue(db.Model):
    __tablename__ = 'sc_silent_issues'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    issue_type = db.Column(db.String(50), nullable=False) # e.g., "Unexpected Congestion", "Efficiency Drop"
    severity = db.Column(db.String(20), nullable=False) # Low, Medium, High
    description = db.Column(db.String(250))
    is_resolved = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'issue_type': self.issue_type,
            'severity': self.severity,
            'description': self.description,
            'is_resolved': self.is_resolved
        }
