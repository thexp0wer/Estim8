#!/usr/bin/env python
"""
Script to add dashboard_theme column to User table
"""

import os
import sqlalchemy as sa
from app import app, db

def execute_sql(sql):
    """
    Execute SQL statement using SQLAlchemy
    """
    with app.app_context():
        try:
            result = db.session.execute(sa.text(sql))
            db.session.commit()
            return result
        except Exception as e:
            db.session.rollback()
            print(f"Error executing SQL: {e}")
            return None

def add_theme_column():
    """
    Add dashboard_theme column to user table
    """
    # Check if the column already exists
    check_sql = """
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'user' AND column_name = 'dashboard_theme'
    """
    
    with app.app_context():
        result = db.session.execute(sa.text(check_sql))
        existing = result.fetchone()
        
        if existing:
            print("Column 'dashboard_theme' already exists in the 'user' table.")
            return
        
        # Add the dashboard_theme column with default value
        add_column_sql = """
        ALTER TABLE "user" 
        ADD COLUMN dashboard_theme VARCHAR(50) NOT NULL DEFAULT 'default'
        """
        
        execute_sql(add_column_sql)
        print("Added 'dashboard_theme' column to 'user' table with default value 'default'")

if __name__ == "__main__":
    add_theme_column()
    print("Migration completed successfully.")