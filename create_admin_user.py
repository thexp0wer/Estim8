from app import app, db
from models import User
from flask import Flask

with app.app_context():
    # Check if admin user already exists
    existing_admin = User.query.filter_by(username='admin').first()
    
    if existing_admin:
        print("Admin user already exists.")
    else:
        # Create new admin user
        admin_user = User(
            username='admin',
            email='admin@estimatetracker.com',
            role='Admin',
            discipline='tools_admin',
            business_unit='BU1',
            working_title='System Administrator',
            is_admin=True
        )
        
        # Set password
        admin_user.set_password('admin')
        
        # Add to database
        db.session.add(admin_user)
        db.session.commit()
        
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: admin")