"""
Script to add is_active column to User table
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

def check_column_exists():
    """
    Check if the is_active column already exists in the user table
    """
    query = """
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'user' AND column_name = 'is_active';
    """
    
    result = execute_sql(query)
    return result and len(result) > 0

def add_column():
    """
    Add is_active column to user table
    """
    if check_column_exists():
        logger.info("Column is_active already exists in user table")
        return True
    
    query = """
    ALTER TABLE "user" 
    ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
    """
    
    result = execute_sql(query)
    
    if result:
        logger.info("Column is_active added to user table")
    else:
        logger.error("Failed to add is_active column to user table")
    
    return result

if __name__ == "__main__":
    logger.info("Starting migration script to add is_active column to User table")
    
    if add_column():
        logger.info("Migration completed successfully")
    else:
        logger.error("Migration failed")
        sys.exit(1)