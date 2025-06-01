"""
Update database schema to add missing columns
"""

import logging
from app import app, db
from sqlalchemy import Column, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the SQL to add missing columns
ADD_COLUMNS_SQL = """
-- Add missing document columns
ALTER TABLE project ADD COLUMN IF NOT EXISTS func_heads_meeting_mom TEXT DEFAULT '[]';
ALTER TABLE project ADD COLUMN IF NOT EXISTS bu_approval_to_bid TEXT DEFAULT '[]';
ALTER TABLE project ADD COLUMN IF NOT EXISTS expression_of_needs TEXT DEFAULT '[]';
ALTER TABLE project ADD COLUMN IF NOT EXISTS scope_of_work TEXT DEFAULT '[]';
ALTER TABLE project ADD COLUMN IF NOT EXISTS execution_schedule TEXT DEFAULT '[]';
ALTER TABLE project ADD COLUMN IF NOT EXISTS execution_strategy TEXT DEFAULT '[]';
ALTER TABLE project ADD COLUMN IF NOT EXISTS resource_mobilization TEXT DEFAULT '[]';

-- Add validation request date column
ALTER TABLE project ADD COLUMN IF NOT EXISTS validation_request_date TIMESTAMP;
"""

# Define SQL to create project_rating table if it doesn't exist
CREATE_RATING_TABLE_SQL = """
-- Create project rating table for E&D team ratings
CREATE TABLE IF NOT EXISTS project_rating (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES project(id),
    rater_id INTEGER NOT NULL REFERENCES "user"(id),
    documentation_completeness INTEGER NOT NULL,
    documentation_clarity INTEGER NOT NULL,
    documentation_quality INTEGER NOT NULL,
    scope_definition INTEGER NOT NULL,
    overall_rating INTEGER NOT NULL,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, rater_id)
);
"""

with app.app_context():
    try:
        # Check if columns exist first
        column_check = db.session.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'project' AND column_name = 'func_heads_meeting_mom'"
        ))
        
        # If column doesn't exist, add all the missing columns
        if not column_check.fetchone():
            logger.info("Adding missing columns to project table...")
            
            # Execute the SQL to add columns
            db.session.execute(text(ADD_COLUMNS_SQL))
            db.session.commit()
            
            logger.info("Project table columns updated successfully!")
            print("Project table columns updated successfully!")
        else:
            logger.info("Project columns already exist. No update needed.")
            print("Project columns already exist. No update needed.")
        
        # Check if project_rating table exists
        table_check = db.session.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'project_rating')"
        ))
        
        if not table_check.scalar():
            logger.info("Creating project_rating table...")
            
            # Create project_rating table
            db.session.execute(text(CREATE_RATING_TABLE_SQL))
            db.session.commit()
            
            logger.info("Project rating table created successfully!")
            print("Project rating table created successfully!")
        else:
            logger.info("Project rating table already exists. No update needed.")
            print("Project rating table already exists. No update needed.")
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating database schema: {str(e)}")
        print(f"Error: {str(e)}")