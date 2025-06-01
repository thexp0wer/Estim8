"""
Script to add custom_phase column to project table
"""
import psycopg2
import os

def execute_sql(sql):
    """
    Execute SQL statement using psycopg2
    """
    conn = None
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cursor = conn.cursor()
        
        # Execute the SQL command
        cursor.execute(sql)
        
        # Commit the changes
        conn.commit()
        
        # Close the cursor
        cursor.close()
        
        return True
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error executing SQL: {error}")
        return False
    finally:
        if conn is not None:
            conn.close()

def add_column():
    """
    Add custom_phase column to project table
    """
    # Check if column exists first
    check_sql = """
    SELECT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'project' AND column_name = 'custom_phase'
    );
    """
    
    # Add column if it doesn't exist
    add_sql = """
    ALTER TABLE project 
    ADD COLUMN IF NOT EXISTS custom_phase VARCHAR(100);
    """
    
    if execute_sql(add_sql):
        print("Successfully added custom_phase column to project table")
    else:
        print("Failed to add custom_phase column to project table")
        
if __name__ == "__main__":
    add_column()