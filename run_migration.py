#!/usr/bin/env python
"""
Simplified runner script for SQLite to PostgreSQL migration.
This script handles the migration process with proper error handling and feedback.
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_env():
    """Check if environment is properly set up"""
    # Check if DATABASE_URL is set
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.error("❌ DATABASE_URL environment variable is not set.")
        logger.error("Please set it to a valid PostgreSQL connection string.")
        logger.error("Example: postgresql://username:password@hostname:port/database")
        return False
    
    if not db_url.startswith('postgresql://'):
        logger.error("❌ DATABASE_URL does not appear to be a PostgreSQL connection string.")
        logger.error("It should start with 'postgresql://'")
        return False
    
    # Check for SQLite database
    sqlite_path = 'instance/app.db'
    if not os.path.exists(sqlite_path):
        logger.error(f"❌ SQLite database not found at {sqlite_path}")
        logger.error("Please make sure the SQLite database exists.")
        return False
    
    return True

def backup_database():
    """Create a backup of the SQLite database"""
    sqlite_path = 'instance/app.db'
    backup_dir = 'backups'
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Create backup with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{backup_dir}/app.db.backup_{timestamp}"
    
    try:
        import shutil
        shutil.copy2(sqlite_path, backup_path)
        logger.info(f"✅ Created backup of SQLite database: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating backup: {e}")
        return False

def run_migration():
    """Run the migration script with automatic confirmation"""
    try:
        # Set environment variables for the subprocess
        env = os.environ.copy()
        env['MIGRATION_AUTO_CONFIRM'] = 'yes'
        env['MIGRATION_SQLITE_PATH'] = 'instance/app.db'
        
        # Run the migration script
        logger.info("🚀 Starting migration process...")
        process = subprocess.Popen(
            ['python', 'migrate_to_postgres.py'],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Provide automatic answers to prompts
        stdout, stderr = process.communicate(input="yes\ninstance/app.db\n")
        
        # Print output
        for line in stdout.splitlines():
            print(line)
        
        if process.returncode == 0:
            logger.info("✅ Migration completed successfully!")
            return True
        else:
            logger.error(f"❌ Migration failed with exit code {process.returncode}")
            for line in stderr.splitlines():
                logger.error(line)
            return False
            
    except Exception as e:
        logger.error(f"❌ Error running migration: {e}")
        return False

def run_verification():
    """Run the verification script"""
    try:
        logger.info("🔍 Verifying PostgreSQL migration...")
        process = subprocess.run(
            ['python', 'verify_postgres.py'],
            capture_output=True,
            text=True
        )
        
        # Print output
        for line in process.stdout.splitlines():
            print(line)
        
        if process.returncode == 0:
            logger.info("✅ Verification completed successfully!")
            return True
        else:
            logger.error(f"❌ Verification failed with exit code {process.returncode}")
            for line in process.stderr.splitlines():
                logger.error(line)
            return False
            
    except Exception as e:
        logger.error(f"❌ Error running verification: {e}")
        return False

def run_optimization():
    """Run the optimization script"""
    try:
        logger.info("⚙️ Optimizing PostgreSQL database...")
        process = subprocess.run(
            ['python', 'optimize_postgres.py'],
            capture_output=True,
            text=True
        )
        
        # Print output
        for line in process.stdout.splitlines():
            print(line)
        
        if process.returncode == 0:
            logger.info("✅ Optimization completed successfully!")
            return True
        else:
            logger.error(f"❌ Optimization failed with exit code {process.returncode}")
            for line in process.stderr.splitlines():
                logger.error(line)
            return False
            
    except Exception as e:
        logger.error(f"❌ Error running optimization: {e}")
        return False

def main():
    """Main function to run the migration process"""
    print("""
========================================================
     SQLite to PostgreSQL Migration Runner
========================================================

This script will:
1. Check environment setup
2. Create a backup of your SQLite database
3. Migrate data to PostgreSQL
4. Verify the migration
5. Optimize the PostgreSQL database

""")
    
    # Ask for confirmation
    confirmation = input("Do you want to continue? (yes/no): ")
    if confirmation.lower() != 'yes':
        logger.info("❌ Migration process cancelled by user")
        return
    
    # Check environment
    if not check_env():
        logger.error("❌ Environment check failed. Please fix the issues and try again.")
        return
    
    # Create backup
    if not backup_database():
        logger.error("❌ Backup failed. Aborting migration.")
        return
    
    # Run migration
    if not run_migration():
        logger.error("❌ Migration failed. Please check the logs for details.")
        return
    
    # Run verification
    if not run_verification():
        logger.warning("⚠️ Verification failed. Migration may be incomplete or have issues.")
    
    # Run optimization
    if not run_optimization():
        logger.warning("⚠️ Optimization failed. Database will still work but may not be optimized.")
    
    logger.info("""
========================================================
     Migration Process Completed
========================================================

Your data has been migrated from SQLite to PostgreSQL.
The application will now use PostgreSQL as its database.

To switch back to SQLite, remove or rename the DATABASE_URL
environment variable.
""")

if __name__ == "__main__":
    main()