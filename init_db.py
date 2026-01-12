
import os
from app import create_app, db
from app.models import OPDQueue, SilentIssue, User

app = create_app()

with app.app_context():

    # Create tables if they don't exist
    db.create_all()
    
    # Create Admin User if not exists
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin = User(username='admin')
        admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
        # Ensure role is set correctly
        admin.role = 'admin'
        db.session.add(admin)
        db.session.commit()
        print("Created default admin user: admin")
    else:
        # User exists, verify role
        if admin_user.role != 'admin':
            print(f"Warning: Admin user found with role '{admin_user.role}'. Fixing to 'admin'.")
            admin_user.role = 'admin'
            db.session.commit()
            print("Admin role corrected successfully.")
    
    print("Database initialized successfully.")
