"""
Script to check if there are any revisions in the database
"""

import os
import sys
from models import db, Project
from app import app

def check_revisions():
    """
    Check if there are any revisions in the database
    """
    with app.app_context():
        # Get all revision projects
        revisions = Project.query.filter_by(is_revision=True).all()
        
        print(f"Found {len(revisions)} revision projects:")
        
        for revision in revisions:
            parent = Project.query.get(revision.parent_project_id)
            parent_title = parent.title if parent else "Unknown"
            print(f"Revision ID: {revision.id}, Rev #{revision.revision_number}")
            print(f"Title: {revision.title}")
            print(f"Parent ID: {revision.parent_project_id}, Parent Title: {parent_title}")
            print("-" * 50)
            
        # Get all non-revision projects with revisions
        parent_projects = Project.query.filter_by(is_revision=False).all()
        projects_with_revisions = []
        
        for project in parent_projects:
            revisions = Project.query.filter_by(parent_project_id=project.id).all()
            if revisions:
                projects_with_revisions.append((project, revisions))
        
        print(f"\nFound {len(projects_with_revisions)} parent projects with revisions:")
        
        for parent, revs in projects_with_revisions:
            print(f"Parent ID: {parent.id}, Title: {parent.title}")
            print(f"Revisions: {len(revs)}")
            for rev in revs:
                print(f"  - Rev #{rev.revision_number}: {rev.title} (ID: {rev.id})")
            print("-" * 50)

if __name__ == "__main__":
    check_revisions()