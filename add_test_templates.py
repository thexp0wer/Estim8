"""
Add Test Excel Templates
This script adds test templates to the excel_template table
"""

from app import app, db
from models import ExcelTemplate
from datetime import datetime
import os

def add_test_templates():
    """Add test templates to the excel_template table"""
    with app.app_context():
        # Check if we already have templates
        templates = ExcelTemplate.query.all()
        if templates:
            print(f"Database already has {len(templates)} templates. Skipping test data.")
            return
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(os.getcwd(), 'uploads', 'excel_templates')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Create test templates for different disciplines
        test_templates = [
            {
                'name': 'Civil Engineering Estimation Template',
                'discipline': 'Civil Engineering',
                'phase': 'Planning',
                'description': 'Standard template for civil engineering deliverables estimation',
                'file_path': os.path.join(uploads_dir, 'civil_template.xlsx'),
                'created_by': 1,  # Admin user
                'is_active': True
            },
            {
                'name': 'Electrical Engineering Estimation Template',
                'discipline': 'Electrical Engineering',
                'phase': 'Design',
                'description': 'Standard template for electrical engineering deliverables estimation',
                'file_path': os.path.join(uploads_dir, 'electrical_template.xlsx'),
                'created_by': 1,  # Admin user
                'is_active': True
            },
            {
                'name': 'Mechanical Engineering Estimation Template',
                'discipline': 'Mechanical Engineering',
                'phase': 'Implementation',
                'description': 'Standard template for mechanical engineering deliverables estimation',
                'file_path': os.path.join(uploads_dir, 'mechanical_template.xlsx'),
                'created_by': 1,  # Admin user
                'is_active': True
            }
        ]
        
        # Create placeholder files
        for template in test_templates:
            # Create an empty file if it doesn't exist
            if not os.path.exists(template['file_path']):
                with open(template['file_path'], 'w') as f:
                    f.write("Placeholder for Excel template")
                print(f"Created placeholder file at {template['file_path']}")
        
        # Add test templates to database
        for template_data in test_templates:
            template = ExcelTemplate(
                name=template_data['name'],
                discipline=template_data['discipline'],
                phase=template_data['phase'],
                description=template_data['description'],
                file_path=template_data['file_path'],
                created_by=template_data['created_by'],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=template_data['is_active']
            )
            db.session.add(template)
        
        # Commit the changes
        try:
            db.session.commit()
            print(f"Added {len(test_templates)} test templates to the database")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding test templates: {str(e)}")

if __name__ == "__main__":
    add_test_templates()