"""
Migration script to update the database schema for the Deliverables Estimation module.

This script adds:
1. phase column to DeliverableUpload
2. version column to ExcelTemplate and DeliverableUpload
3. Creates new tables: deliverable_list, deliverable_list_item, 
   standard_deliverable_template, standard_deliverable_item

Run this script directly to perform the migration.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("DATABASE_URL environment variable is not set.")
    sys.exit(1)

# Create engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()
metadata = MetaData()

def add_columns_to_deliverable_upload():
    """Add phase and version columns to deliverable_upload table"""
    print("Adding phase and version columns to deliverable_upload table...")
    
    try:
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        # Get the deliverable_upload table
        if 'deliverable_upload' not in metadata.tables:
            print("Error: deliverable_upload table does not exist")
            return False
            
        deliverable_upload = metadata.tables['deliverable_upload']
        conn = engine.connect()
        
        # Check if phase column exists and add it if not
        if 'phase' not in deliverable_upload.columns:
            conn.execute("""ALTER TABLE deliverable_upload ADD COLUMN phase VARCHAR(100) DEFAULT 'Define'""")
            print("Added phase column")
        else:
            print("phase column already exists")
        
        # Check if version column exists and add it if not
        if 'version' not in deliverable_upload.columns:
            conn.execute("""ALTER TABLE deliverable_upload ADD COLUMN version INTEGER DEFAULT 1""")
            print("Added version column")
        else:
            print("version column already exists")
        
        # Update nullable status for project_id and discipline
        # First set default values for any NULL columns
        if 'project_id' in deliverable_upload.columns:
            # Check if there are any nulls in project_id
            null_project_ids = conn.execute("SELECT COUNT(*) FROM deliverable_upload WHERE project_id IS NULL").fetchone()[0]
            if null_project_ids > 0:
                # Get the first project id to use as default
                first_project = conn.execute("SELECT id FROM project ORDER BY id LIMIT 1").fetchone()
                if first_project:
                    default_project_id = first_project[0]
                    conn.execute(f"UPDATE deliverable_upload SET project_id = {default_project_id} WHERE project_id IS NULL")
                    print(f"Updated NULL project_ids to default value: {default_project_id}")
                else:
                    print("No projects found in database, cannot set default project_id")
                    return False
                    
                # Now alter column to not null
                conn.execute("ALTER TABLE deliverable_upload ALTER COLUMN project_id SET NOT NULL")
                print("Made project_id not nullable")
        
        # Do the same for discipline
        if 'discipline' in deliverable_upload.columns:
            null_disciplines = conn.execute("SELECT COUNT(*) FROM deliverable_upload WHERE discipline IS NULL").fetchone()[0]
            if null_disciplines > 0:
                conn.execute("UPDATE deliverable_upload SET discipline = 'General' WHERE discipline IS NULL")
                print("Updated NULL disciplines to 'General'")
                
                # Now alter column to not null
                conn.execute("ALTER TABLE deliverable_upload ALTER COLUMN discipline SET NOT NULL")
                print("Made discipline not nullable")
        
        # Make phase not nullable once it exists
        conn.execute("ALTER TABLE deliverable_upload ALTER COLUMN phase SET NOT NULL")
        
        # Make version not nullable once it exists
        conn.execute("ALTER TABLE deliverable_upload ALTER COLUMN version SET NOT NULL")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding columns to deliverable_upload: {e}")
        return False

def add_version_to_excel_template():
    """Add version column to excel_template table"""
    print("Adding version column to excel_template table...")
    
    try:
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        # Get the excel_template table
        if 'excel_template' not in metadata.tables:
            print("Error: excel_template table does not exist")
            return False
            
        excel_template = metadata.tables['excel_template']
        conn = engine.connect()
        
        # Check if version column exists and add it if not
        if 'version' not in excel_template.columns:
            conn.execute("ALTER TABLE excel_template ADD COLUMN version INTEGER DEFAULT 1")
            conn.execute("UPDATE excel_template SET version = 1")
            conn.execute("ALTER TABLE excel_template ALTER COLUMN version SET NOT NULL")
            print("Added version column")
        else:
            print("version column already exists")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding version column to excel_template: {e}")
        return False

def create_deliverable_list_tables():
    """Create deliverable_list and deliverable_list_item tables"""
    print("Creating deliverable list tables...")
    
    try:
        metadata = MetaData()
        metadata.reflect(bind=engine)
        conn = engine.connect()
        
        # Check if deliverable_list table exists
        if 'deliverable_list' not in metadata.tables:
            # Create deliverable_list table
            conn.execute("""
                CREATE TABLE deliverable_list (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL REFERENCES project(id) ON DELETE CASCADE,
                    discipline VARCHAR(100) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    file_id INTEGER REFERENCES deliverable_upload(id),
                    status VARCHAR(50) DEFAULT 'Draft',
                    created_by INTEGER NOT NULL REFERENCES "user"(id),
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    completion_percentage FLOAT DEFAULT 0.0,
                    estimated_hours FLOAT DEFAULT 0.0
                );
            """)
            print("Created deliverable_list table")
        else:
            print("deliverable_list table already exists")
        
        # Refresh metadata to include the new table
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        # Check if deliverable_list_item table exists
        if 'deliverable_list_item' not in metadata.tables:
            # Create deliverable_list_item table
            conn.execute("""
                CREATE TABLE deliverable_list_item (
                    id SERIAL PRIMARY KEY,
                    list_id INTEGER NOT NULL REFERENCES deliverable_list(id) ON DELETE CASCADE,
                    deliverable_name VARCHAR(255) NOT NULL,
                    description TEXT,
                    deliverable_type VARCHAR(100),
                    estimated_hours FLOAT DEFAULT 0.0,
                    complexity VARCHAR(50) DEFAULT 'Medium',
                    status VARCHAR(50) DEFAULT 'Not Started',
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    is_template_item BOOLEAN DEFAULT FALSE,
                    sequence INTEGER DEFAULT 0
                );
            """)
            print("Created deliverable_list_item table")
        else:
            print("deliverable_list_item table already exists")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating deliverable list tables: {e}")
        return False

def create_standard_template_tables():
    """Create standard_deliverable_template and standard_deliverable_item tables"""
    print("Creating standard template tables...")
    
    try:
        metadata = MetaData()
        metadata.reflect(bind=engine)
        conn = engine.connect()
        
        # Check if standard_deliverable_template table exists
        if 'standard_deliverable_template' not in metadata.tables:
            # Create standard_deliverable_template table
            conn.execute("""
                CREATE TABLE standard_deliverable_template (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    discipline VARCHAR(100) NOT NULL,
                    phase VARCHAR(100) NOT NULL,
                    description TEXT,
                    created_by INTEGER NOT NULL REFERENCES "user"(id),
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    is_active BOOLEAN DEFAULT TRUE
                );
            """)
            print("Created standard_deliverable_template table")
        else:
            print("standard_deliverable_template table already exists")
        
        # Refresh metadata to include the new table
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        # Check if standard_deliverable_item table exists
        if 'standard_deliverable_item' not in metadata.tables:
            # Create standard_deliverable_item table
            conn.execute("""
                CREATE TABLE standard_deliverable_item (
                    id SERIAL PRIMARY KEY,
                    template_id INTEGER NOT NULL REFERENCES standard_deliverable_template(id) ON DELETE CASCADE,
                    deliverable_name VARCHAR(255) NOT NULL,
                    description TEXT,
                    deliverable_type VARCHAR(100),
                    estimated_hours FLOAT DEFAULT 0.0,
                    complexity VARCHAR(50) DEFAULT 'Medium',
                    sequence INTEGER DEFAULT 0
                );
            """)
            print("Created standard_deliverable_item table")
        else:
            print("standard_deliverable_item table already exists")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating standard template tables: {e}")
        return False

def run_migration():
    """Run the migration script"""
    print("Starting database migration for Deliverables Estimation module...")
    
    # Add columns to existing tables
    if not add_columns_to_deliverable_upload():
        print("Failed to update deliverable_upload table. Migration aborted.")
        return False
    
    if not add_version_to_excel_template():
        print("Failed to update excel_template table. Migration aborted.")
        return False
    
    # Create new tables
    if not create_deliverable_list_tables():
        print("Failed to create deliverable list tables. Migration aborted.")
        return False
    
    if not create_standard_template_tables():
        print("Failed to create standard template tables. Migration aborted.")
        return False
    
    print("Migration completed successfully!")
    return True

if __name__ == "__main__":
    run_migration()