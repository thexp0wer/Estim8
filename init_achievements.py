"""
Script to initialize achievements in the database
"""
import os
import sys
from datetime import datetime
from app import app, db
from utils.achievements import initialize_achievements

if __name__ == "__main__":
    with app.app_context():
        try:
            # Initialize default achievements
            added_count = initialize_achievements()
            print(f"Successfully initialized {added_count} achievements")
            
        except Exception as e:
            print(f"Error initializing achievements: {str(e)}")
            sys.exit(1)