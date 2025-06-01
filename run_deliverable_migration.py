"""
Direct SQL migration script for the Deliverables Estimation module.
This script creates new tables and adds columns using direct SQL statements.
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Get database connection string from environment variable
DB_URL = os.environ.get('DATABASE_URL')

# Parse the database connection URL
db_params = {}
components = DB_URL.split(':')
db_params['user'] = components[1].replace('//', '')
rest = components[2].split('/')
db_params['password'] = rest[0].split('@')[0]
db_params['host'] = rest[0].split('@')[1]
db_params['port'] = components[3].split('/')[0]
db_params['database'] = components[3].split('/')[1]

def execute_sql(sql, params=None, fetch=False):
    """Execute SQL with error handling"""
    conn = None
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=db_params['host'],
            port=db_params['port'],
            user=db_params['user'],
            password=db_params['password'],
            database=db_params['database']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Create cursor and execute
        cursor = conn.cursor()
        cursor.execute(sql, params or [])
        
        # Fetch results if requested
        result = None
        if fetch:
            result = cursor.fetchall()
            
        # Close cursor
        cursor.close()
        return result
    except Exception as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def update_deliverable_upload_table():
    """Add phase and version columns to deliverable_upload table"""
    print("Modifying deliverable_upload table...")
    
    # Check if phase column exists
    phase_exists = execute_sql(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'deliverable_upload' AND column_name = 'phase'",
        fetch=True
    )
    
    if not phase_exists:
        execute_sql("ALTER TABLE deliverable_upload ADD COLUMN phase VARCHAR(100) DEFAULT 'Define'")
        print("Added phase column")
    else:
        print("Phase column already exists")
    
    # Check if version column exists
    version_exists = execute_sql(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'deliverable_upload' AND column_name = 'version'",
        fetch=True
    )
    
    if not version_exists:
        execute_sql("ALTER TABLE deliverable_upload ADD COLUMN version INTEGER DEFAULT 1")
        print("Added version column")
    else:
        print("Version column already exists")
    
    # Make project_id not nullable if it is
    project_id_nullable = execute_sql(
        "SELECT is_nullable FROM information_schema.columns WHERE table_name = 'deliverable_upload' AND column_name = 'project_id'",
        fetch=True
    )
    
    if project_id_nullable and project_id_nullable[0][0] == 'YES':
        # Get default project id
        projects = execute_sql("SELECT id FROM project ORDER BY id LIMIT 1", fetch=True)
        if projects:
            default_project_id = projects[0][0]
            execute_sql(f"UPDATE deliverable_upload SET project_id = {default_project_id} WHERE project_id IS NULL")
            execute_sql("ALTER TABLE deliverable_upload ALTER COLUMN project_id SET NOT NULL")
            print(f"Made project_id not nullable (default: {default_project_id})")
    
    # Make discipline not nullable if it is
    discipline_nullable = execute_sql(
        "SELECT is_nullable FROM information_schema.columns WHERE table_name = 'deliverable_upload' AND column_name = 'discipline'",
        fetch=True
    )
    
    if discipline_nullable and discipline_nullable[0][0] == 'YES':
        execute_sql("UPDATE deliverable_upload SET discipline = 'General' WHERE discipline IS NULL")
        execute_sql("ALTER TABLE deliverable_upload ALTER COLUMN discipline SET NOT NULL")
        print("Made discipline not nullable")
    
    return True

def update_excel_template_table():
    """Add version column to excel_template table"""
    print("Modifying excel_template table...")
    
    # Check if version column exists
    version_exists = execute_sql(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'excel_template' AND column_name = 'version'",
        fetch=True
    )
    
    if not version_exists:
        execute_sql("ALTER TABLE excel_template ADD COLUMN version INTEGER DEFAULT 1")
        execute_sql("UPDATE excel_template SET version = 1")
        execute_sql("ALTER TABLE excel_template ALTER COLUMN version SET NOT NULL")
        print("Added version column")
    else:
        print("Version column already exists")
    
    return True

def create_deliverable_list_tables():
    """Create deliverable_list and deliverable_list_item tables"""
    print("Creating deliverable list tables...")
    
    # Check if deliverable_list table exists
    deliverable_list_exists = execute_sql(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'deliverable_list')",
        fetch=True
    )
    
    if not deliverable_list_exists or not deliverable_list_exists[0][0]:
        execute_sql("""
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
            )
        """)
        print("Created deliverable_list table")
    else:
        print("deliverable_list table already exists")
    
    # Check if deliverable_list_item table exists
    deliverable_list_item_exists = execute_sql(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'deliverable_list_item')",
        fetch=True
    )
    
    if not deliverable_list_item_exists or not deliverable_list_item_exists[0][0]:
        execute_sql("""
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
            )
        """)
        print("Created deliverable_list_item table")
    else:
        print("deliverable_list_item table already exists")
    
    return True

def create_standard_template_tables():
    """Create standard_deliverable_template and standard_deliverable_item tables"""
    print("Creating standard template tables...")
    
    # Check if standard_deliverable_template table exists
    std_template_exists = execute_sql(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'standard_deliverable_template')",
        fetch=True
    )
    
    if not std_template_exists or not std_template_exists[0][0]:
        execute_sql("""
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
            )
        """)
        print("Created standard_deliverable_template table")
    else:
        print("standard_deliverable_template table already exists")
    
    # Check if standard_deliverable_item table exists
    std_item_exists = execute_sql(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'standard_deliverable_item')",
        fetch=True
    )
    
    if not std_item_exists or not std_item_exists[0][0]:
        execute_sql("""
            CREATE TABLE standard_deliverable_item (
                id SERIAL PRIMARY KEY,
                template_id INTEGER NOT NULL REFERENCES standard_deliverable_template(id) ON DELETE CASCADE,
                deliverable_name VARCHAR(255) NOT NULL,
                description TEXT,
                deliverable_type VARCHAR(100),
                estimated_hours FLOAT DEFAULT 0.0,
                complexity VARCHAR(50) DEFAULT 'Medium',
                sequence INTEGER DEFAULT 0
            )
        """)
        print("Created standard_deliverable_item table")
    else:
        print("standard_deliverable_item table already exists")
    
    return True

def run_migration():
    """Run the migration script"""
    print("Starting database migration for Deliverables Estimation module...")
    
    # Test database connection
    test = execute_sql("SELECT 1", fetch=True)
    if not test:
        print("Failed to connect to database. Aborting migration.")
        return False
    
    # Add/modify columns to existing tables
    if not update_deliverable_upload_table():
        print("Failed to update deliverable_upload table. Migration aborted.")
        return False
    
    if not update_excel_template_table():
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