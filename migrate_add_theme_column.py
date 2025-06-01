#!/usr/bin/env python
"""
Script to add dashboard_theme column to the User table
Uses direct database connection to avoid model initialization issues
"""

import os
import psycopg2
import psycopg2.extras

def execute_sql(conn, sql, params=None):
    """Execute SQL statement with proper error handling"""
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error executing SQL: {e}")
        return False

def add_column_if_not_exists(conn):
    """Add dashboard_theme column if it doesn't exist"""
    # Check if column exists
    check_sql = """
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'user' AND column_name = 'dashboard_theme'
    """
    
    with conn.cursor() as cursor:
        cursor.execute(check_sql)
        result = cursor.fetchone()
        
    if result:
        print("Column 'dashboard_theme' already exists.")
        return True
    
    # Add the column
    add_sql = """
    ALTER TABLE "user" 
    ADD COLUMN dashboard_theme VARCHAR(50) DEFAULT 'default' NOT NULL
    """
    
    success = execute_sql(conn, add_sql)
    if success:
        print("Successfully added 'dashboard_theme' column to the User table.")
    else:
        print("Failed to add column.")
    
    return success

def main():
    """Run the migration"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not set.")
        return False
    
    print(f"Connecting to database...")
    
    try:
        conn = psycopg2.connect(database_url)
        success = add_column_if_not_exists(conn)
        conn.close()
        
        if success:
            print("Migration completed successfully.")
        else:
            print("Migration failed.")
        
        return success
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False

if __name__ == "__main__":
    main()