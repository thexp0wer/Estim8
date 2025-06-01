"""
Script to add SystemSetting table to the database
"""
import os
import sys
from datetime import datetime
import logging
import psycopg2
from psycopg2 import sql

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def execute_sql(sql_query, params=None):
    """
    Execute SQL statement using psycopg2
    """
    # Get connection details from environment
    db_url = os.environ.get("DATABASE_URL")
    
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    conn = None
    cursor = None
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        if params:
            cursor.execute(sql_query, params)
        else:
            cursor.execute(sql_query)
            
        conn.commit()
        logger.info("SQL executed successfully")
        
        # Return results if this is a SELECT query
        if sql_query.strip().upper().startswith("SELECT"):
            return cursor.fetchall()
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {str(e)}")
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def check_table_exists():
    """
    Check if the system_setting table already exists in the database
    """
    query = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'system_setting'
    );
    """
    
    result = execute_sql(query)
    if result and result[0][0]:
        return True
    return False

def create_table():
    """
    Create SystemSetting table in the database
    """
    if check_table_exists():
        logger.info("The system_setting table already exists")
        return True
    
    query = """
    CREATE TABLE system_setting (
        id SERIAL PRIMARY KEY,
        setting_key VARCHAR(100) NOT NULL UNIQUE,
        setting_value TEXT,
        setting_type VARCHAR(50) DEFAULT 'string',
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    result = execute_sql(query)
    
    if result:
        logger.info("Successfully created system_setting table")
        
        # Add some default settings
        default_settings = [
            {
                'key': 'app.name',
                'value': 'JESA Engineering Estimation Tool',
                'type': 'string',
                'description': 'Application name displayed in various parts of the UI'
            },
            {
                'key': 'app.footer_text',
                'value': '© 2025 JESA Group. All rights reserved.',
                'type': 'string',
                'description': 'Text displayed in the application footer'
            },
            {
                'key': 'app.default_timezone',
                'value': 'UTC',
                'type': 'string',
                'description': 'Default timezone for date/time display'
            },
            {
                'key': 'project.auto_archive_days',
                'value': '90',
                'type': 'int',
                'description': 'Number of days after which completed projects are auto-archived'
            },
            {
                'key': 'notifications.max_age_days',
                'value': '30',
                'type': 'int',
                'description': 'Maximum age in days for notifications before they are automatically deleted'
            }
        ]
        
        for setting in default_settings:
            insert_query = """
            INSERT INTO system_setting (setting_key, setting_value, setting_type, description)
            VALUES (%s, %s, %s, %s);
            """
            execute_sql(insert_query, (setting['key'], setting['value'], setting['type'], setting['description']))
        
        logger.info(f"Added {len(default_settings)} default system settings")
        return True
    else:
        logger.error("Failed to create system_setting table")
        return False

if __name__ == "__main__":
    logger.info("Starting migration to add SystemSetting table")
    
    if create_table():
        logger.info("Migration completed successfully")
    else:
        logger.error("Migration failed")
        sys.exit(1)