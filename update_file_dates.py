"""
Script to add file upload date fields to the Project model
"""
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable is not set")
    sys.exit(1)

# Create database connection
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()
metadata = MetaData()
metadata.bind = engine

def add_file_date_columns():
    """Add file date columns to Project table"""
    # Reflect the existing table
    project_table = Table('project', metadata, autoload_with=engine)
    
    # Add date columns for each discipline
    disciplines = [
        'process_sid',
        'civil_structure',
        'piping',
        'mechanical',
        'electrical',
        'instrumentation_control',
        'digitalization',
        'engineering_management',
        'environmental',
        'tools_admin',
        'construction'
    ]
    
    with engine.begin() as connection:
        for discipline in disciplines:
            date_column = f"{discipline}_files_date"
            # Check if column already exists
            if date_column not in project_table.columns:
                print(f"Adding column {date_column} to Project table")
                connection.execute(text(f"ALTER TABLE project ADD COLUMN {date_column} VARCHAR(30)"))

if __name__ == '__main__':
    add_file_date_columns()
    print("Update complete! File date columns have been added to the Project table.")