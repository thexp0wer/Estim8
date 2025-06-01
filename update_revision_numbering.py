"""
Update Revision Numbering

This script updates the revision_number field in the Project table
to change from the 1-based numbering to 0-based numbering.

Original: Project original (revision 1) → First revision (revision 2) → etc.
New: Project original (revision 0) → First revision (revision 1) → etc.
"""

import os
import sys
from datetime import datetime
from app import app, db
from models import Project

def update_revision_numbering():
    """Update revision numbering for all projects"""
    print("Updating revision numbering for all projects...")
    
    # Count projects
    total_projects = Project.query.count()
    print(f"Found {total_projects} projects in the database")
    
    # Fetch all projects
    projects = Project.query.all()
    processed = 0
    modified = 0
    
    # Update revision numbers
    for project in projects:
        processed += 1
        
        # Only update projects with revision_number > 0
        if project.revision_number > 0:
            old_revision = project.revision_number
            project.revision_number = old_revision - 1
            modified += 1
            
            if processed % 100 == 0 or processed == total_projects:
                print(f"Processed {processed}/{total_projects} projects, modified {modified}")
                db.session.commit()
    
    # Commit any remaining changes
    if modified % 100 != 0:
        db.session.commit()
    
    print(f"Updated revision numbering for {modified} projects")
    return True

if __name__ == "__main__":
    with app.app_context():
        print(f"Starting revision numbering update at {datetime.now()}")
        try:
            result = update_revision_numbering()
            if result:
                print("Revision numbering update completed successfully!")
            else:
                print("Revision numbering update failed.")
        except Exception as e:
            print(f"Error during revision numbering update: {str(e)}")
            db.session.rollback()