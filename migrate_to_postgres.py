#!/usr/bin/env python
"""
Migration script to transfer data from SQLite to PostgreSQL.
This script creates a copy of all data from the SQLite database into PostgreSQL.
"""

import os
import sys
import logging
import time
from datetime import datetime
import sqlite3
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app import app, db

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_postgres_url():
    """Check if PostgreSQL URL is set"""
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if not db_url.startswith('postgresql://'):
        logger.error("❌ PostgreSQL URL is not properly configured.")
        logger.error("Please set the DATABASE_URL environment variable to a valid PostgreSQL URL.")
        sys.exit(1)
    return db_url

def create_sqlite_connection(sqlite_path):
    """Create a connection to the SQLite database"""
    try:
        if not os.path.exists(sqlite_path):
            logger.error(f"❌ SQLite database file not found: {sqlite_path}")
            sys.exit(1)
            
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row
        logger.info(f"✅ Connected to SQLite database: {sqlite_path}")
        return conn
    except Exception as e:
        logger.error(f"❌ Error connecting to SQLite database: {e}")
        sys.exit(1)

def get_tables(sqlite_conn):
    """Get a list of tables from the SQLite database"""
    try:
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
        logger.info(f"📊 Found {len(tables)} tables in SQLite: {', '.join(tables)}")
        return tables
    except Exception as e:
        logger.error(f"❌ Error getting tables from SQLite: {e}")
        sys.exit(1)

def get_table_columns(sqlite_conn, table):
    """Get column names for a table"""
    try:
        cursor = sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [row[1] for row in cursor.fetchall()]
        return columns
    except Exception as e:
        logger.error(f"❌ Error getting columns for table {table}: {e}")
        return []

def get_table_data(sqlite_conn, table):
    """Get all data from a table"""
    try:
        cursor = sqlite_conn.cursor()
        columns = get_table_columns(sqlite_conn, table)
        column_str = ", ".join(columns)
        cursor.execute(f"SELECT {column_str} FROM {table};")
        rows = cursor.fetchall()
        logger.info(f"📊 Found {len(rows)} rows in table {table}")
        return rows, columns
    except Exception as e:
        logger.error(f"❌ Error getting data from table {table}: {e}")
        return [], []

def clear_postgres_table(session, table):
    """Clear data from PostgreSQL table"""
    try:
        session.execute(text(f'TRUNCATE TABLE "{table}" CASCADE;'))
        session.commit()
        logger.info(f"🗑️ Cleared data from PostgreSQL table: {table}")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error clearing PostgreSQL table {table}: {e}")
        return False

def insert_data_to_postgres(session, table, rows, columns):
    """Insert data from SQLite to PostgreSQL"""
    if not rows:
        logger.warning(f"⚠️ No data to insert for table {table}")
        return 0
    
    try:
        success_count = 0
        total_rows = len(rows)
        
        # PostgreSQL doesn't support SQLite's rowid, so we need to handle it specially
        # Also, some tables might need special handling for data types
        for row in rows:
            try:
                # Convert SQLite row to dict
                row_dict = {columns[i]: row[i] for i in range(len(columns))}
                
                # Special processing for certain columns/tables
                if table == 'user' and 'password_hash' in row_dict:
                    # Ensure password hash is stored as string
                    if row_dict['password_hash'] is not None:
                        row_dict['password_hash'] = str(row_dict['password_hash'])
                
                # Build placeholders for SQL
                placeholders = ", ".join([f":{col}" for col in columns])
                column_str = ", ".join([f'"{col}"' for col in columns])
                
                # Insert data
                session.execute(
                    text(f'INSERT INTO "{table}" ({column_str}) VALUES ({placeholders})'),
                    row_dict
                )
                
                # Commit in batches
                if success_count % 100 == 0:
                    session.commit()
                
                success_count += 1
                
                # Show progress for large tables
                if total_rows > 100 and success_count % 100 == 0:
                    logger.info(f"⏳ Inserted {success_count}/{total_rows} rows into {table} ({(success_count/total_rows)*100:.1f}%)")
            
            except Exception as e:
                session.rollback()
                logger.error(f"❌ Error inserting row into {table}: {e}")
                logger.error(f"Problematic row: {row_dict}")
        
        # Final commit
        session.commit()
        
        logger.info(f"✅ Inserted {success_count}/{total_rows} rows into {table}")
        return success_count
    
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error inserting data into {table}: {e}")
        return 0

def migrate_table(sqlite_conn, pg_session, table):
    """Migrate a single table from SQLite to PostgreSQL"""
    logger.info(f"\n=== Migrating table: {table} ===")
    
    # Get data from SQLite
    rows, columns = get_table_data(sqlite_conn, table)
    if not rows:
        logger.warning(f"⚠️ No data to migrate for table {table}")
        return 0
    
    # Clear PostgreSQL table (optional - be careful!)
    # clear_postgres_table(pg_session, table)
    
    # Insert data into PostgreSQL
    inserted_count = insert_data_to_postgres(pg_session, table, rows, columns)
    
    return inserted_count

def backup_sqlite_database(sqlite_path):
    """Create a backup of the SQLite database"""
    try:
        backup_path = f"{sqlite_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(sqlite_path, backup_path)
        logger.info(f"✅ Created backup of SQLite database: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"❌ Error creating backup of SQLite database: {e}")
        return None

def reset_sequences(pg_session):
    """Reset sequence counters in PostgreSQL based on max ID values"""
    try:
        # Get a list of all tables
        result = pg_session.execute(text("""
            SELECT tablename FROM pg_tables WHERE schemaname = 'public';
        """)).fetchall()
        
        tables = [row[0] for row in result]
        
        for table in tables:
            try:
                # Check if table has an id column
                result = pg_session.execute(text(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = '{table}' AND column_name = 'id';
                """)).fetchone()
                
                if result:
                    # Get the sequence name
                    result = pg_session.execute(text(f"""
                        SELECT pg_get_serial_sequence('{table}', 'id');
                    """)).fetchone()
                    
                    if result and result[0]:
                        sequence_name = result[0]
                        
                        # Get max id
                        result = pg_session.execute(text(f"""
                            SELECT COALESCE(MAX(id), 0) + 1 FROM "{table}";
                        """)).fetchone()
                        
                        if result:
                            max_id = result[0]
                            
                            # Set sequence value
                            pg_session.execute(text(f"""
                                ALTER SEQUENCE {sequence_name} RESTART WITH {max_id};
                            """))
                            
                            logger.info(f"✅ Reset sequence for {table} to {max_id}")
            
            except Exception as e:
                logger.warning(f"⚠️ Could not reset sequence for {table}: {e}")
        
        pg_session.commit()
        logger.info("✅ Reset all sequences")
        return True
    
    except Exception as e:
        pg_session.rollback()
        logger.error(f"❌ Error resetting sequences: {e}")
        return False

def main():
    """Main migration function"""
    logger.info("=== SQLite to PostgreSQL Migration ===")
    
    # Check if PostgreSQL URL is set
    postgres_url = check_postgres_url()
    
    # Ask for confirmation
    print("\n⚠️ WARNING: This will migrate data from SQLite to PostgreSQL.")
    print("Existing data in PostgreSQL will NOT be deleted unless you uncomment the clear_postgres_table calls.")
    print("It's recommended to run this on a fresh PostgreSQL database.")
    
    confirmation = input("\nDo you want to continue? (yes/no): ")
    if confirmation.lower() != 'yes':
        logger.info("❌ Migration cancelled by user")
        return
    
    # Ask for SQLite database path
    sqlite_path = input("\nEnter the path to the SQLite database file (default: instance/app.db): ")
    if not sqlite_path:
        sqlite_path = 'instance/app.db'
    
    # Create a backup of the SQLite database
    backup_path = backup_sqlite_database(sqlite_path)
    if not backup_path:
        logger.error("❌ Failed to create backup. Aborting migration.")
        return
    
    # Connect to SQLite
    sqlite_conn = create_sqlite_connection(sqlite_path)
    
    # Create PostgreSQL session
    try:
        with app.app_context():
            # Check PostgreSQL connection
            db.session.execute(text('SELECT 1')).scalar()
            logger.info("✅ Connected to PostgreSQL database")
            
            # Get tables from SQLite
            tables = get_tables(sqlite_conn)
            
            # Start migration
            start_time = time.time()
            total_rows_migrated = 0
            
            for table in tables:
                rows_migrated = migrate_table(sqlite_conn, db.session, table)
                total_rows_migrated += rows_migrated
            
            # Reset sequences
            reset_sequences(db.session)
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"\n=== Migration Summary ===")
            logger.info(f"Total tables migrated: {len(tables)}")
            logger.info(f"Total rows migrated: {total_rows_migrated}")
            logger.info(f"Total time: {duration:.2f} seconds")
            logger.info(f"Backup created at: {backup_path}")
            logger.info(f"\n=== ✅ Migration Completed Successfully ===")
    
    except Exception as e:
        logger.error(f"❌ Error during migration: {e}")
    
    finally:
        # Close connections
        sqlite_conn.close()

if __name__ == "__main__":
    main()