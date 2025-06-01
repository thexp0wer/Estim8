"""
This script updates the progress of all existing projects based on their status.
Run this script to ensure all projects have their progress correctly set.
"""
from app import app, db
from models import Project
from datetime import datetime

def update_all_project_progress():
    """Update all projects' progress based on their status"""
    with app.app_context():
        # Get all projects
        projects = Project.query.all()
        updated_count = 0
        
        for project in projects:
            old_progress = project.progress_percentage
            new_progress = project.calculate_status_based_progress()
            
            # Only update if progress is different
            if old_progress != new_progress:
                project.progress_percentage = new_progress
                print(f"Updating project {project.id} ({project.title}): {old_progress}% → {new_progress}%")
                updated_count += 1
        
        # Commit all changes at once
        if updated_count > 0:
            db.session.commit()
            print(f"Successfully updated progress for {updated_count} projects")
        else:
            print("No projects needed progress updates")

if __name__ == "__main__":
    update_all_project_progress()