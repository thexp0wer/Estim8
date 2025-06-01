"""
Script to add last_modified column to DeliverableUpload table
"""
import os
import psycopg2
from datetime import datetime
from psycopg2 import sql

def execute_sql(sql_query, params=None):
    """
    Execute SQL statement using psycopg2
    """
    conn = None
    result = None
    
    try:
        # Get database connection parameters from environment variables
        db_url = os.environ.get('DATABASE_URL')
        
        # Connect to database
        conn = psycopg2.connect(db_url)
        
        # Create cursor with named parameters
        cursor = conn.cursor()
        
        # Execute SQL statement
        cursor.execute(sql_query, params)
        
        # Check if query returns results
        if cursor.description:
            result = cursor.fetchall()
        
        # Commit changes
        conn.commit()
        
        # Close cursor
        cursor.close()
        
    except Exception as e:
        print(f"Database error: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
    
    return result

def check_column_exists():
    """
    Check if the last_modified column already exists in the deliverable_upload table
    """
    check_query = """
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'deliverable_upload' 
        AND column_name = 'last_modified'
    );
    """
    
    result = execute_sql(check_query)
    
    if result and result[0][0]:
        return True
    
    return False

def add_column():
    """
    Add last_modified column to deliverable_upload table
    """
    if check_column_exists():
        print("Column 'last_modified' already exists in deliverable_upload table. No action needed.")
        return
    
    try:
        # Add last_modified column with default current timestamp
        add_column_query = """
        ALTER TABLE deliverable_upload 
        ADD COLUMN last_modified TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW();
        """
        
        execute_sql(add_column_query)
        print("Successfully added 'last_modified' column to deliverable_upload table.")
        
    except Exception as e:
        print(f"Error adding column: {str(e)}")

if __name__ == "__main__":
    add_column()