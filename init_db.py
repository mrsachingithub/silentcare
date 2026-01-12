
import os
from app import create_app, db
from app.models import OPDQueue, SilentIssue, User

app = create_app()

with app.app_context():

    # Create tables if they don't exist
    db.create_all()
    
    # Create Admin User if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
        db.session.add(admin)
        db.session.commit()
        print("Created default admin user: admin / admin123")
    
    print("Database initialized successfully.")
