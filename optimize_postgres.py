#!/usr/bin/env python
"""
Script to optimize PostgreSQL performance by adding indexes.
This script adds indexes to frequently queried columns to improve performance.
"""

import os
import sys
import logging
from sqlalchemy import text
from app import app, db

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_type():
    """Check if the app is using PostgreSQL"""
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    using_postgres = db_url.startswith('postgresql://')
    logger.info(f"Using PostgreSQL: {using_postgres}")
    if not using_postgres:
        logger.error("This script can only be run with PostgreSQL")
        sys.exit(1)
    return using_postgres

def create_indexes():
    """Create indexes on frequently queried columns"""
    with app.app_context():
        try:
            # 1. Projects table indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_project_status ON project (status);
                CREATE INDEX IF NOT EXISTS idx_project_business_unit ON project (business_unit);
                CREATE INDEX IF NOT EXISTS idx_project_program ON project (program);
                CREATE INDEX IF NOT EXISTS idx_project_created_by ON project (created_by);
                CREATE INDEX IF NOT EXISTS idx_project_project_type ON project (project_type);
                CREATE INDEX IF NOT EXISTS idx_project_phase ON project (phase);
                CREATE INDEX IF NOT EXISTS idx_project_created_at ON project (created_at);
                CREATE INDEX IF NOT EXISTS idx_project_approval_date ON project (approval_date);
                CREATE INDEX IF NOT EXISTS idx_project_submission_date ON project (submission_date);
                CREATE INDEX IF NOT EXISTS idx_project_validation_request_date ON project (validation_request_date);
            """))
            
            # 2. User table indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_username ON "user" (username);
                CREATE INDEX IF NOT EXISTS idx_user_email ON "user" (email);
                CREATE INDEX IF NOT EXISTS idx_user_discipline ON "user" (discipline);
                CREATE INDEX IF NOT EXISTS idx_user_business_unit ON "user" (business_unit);
                CREATE INDEX IF NOT EXISTS idx_user_role ON "user" (role);
            """))
            
            # 3. Project History table indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_project_history_project_id ON project_history (project_id);
                CREATE INDEX IF NOT EXISTS idx_project_history_action ON project_history (action);
                CREATE INDEX IF NOT EXISTS idx_project_history_timestamp ON project_history (timestamp);
                CREATE INDEX IF NOT EXISTS idx_project_history_user_id ON project_history (user_id);
            """))
            
            # 4. Notification table indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notification_user_id ON notification (user_id);
                CREATE INDEX IF NOT EXISTS idx_notification_related_project_id ON notification (related_project_id);
                CREATE INDEX IF NOT EXISTS idx_notification_read ON notification (read);
                CREATE INDEX IF NOT EXISTS idx_notification_timestamp ON notification (timestamp);
            """))
            
            # 5. Project Rating table indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_project_rating_project_id ON project_rating (project_id);
                CREATE INDEX IF NOT EXISTS idx_project_rating_rater_id ON project_rating (rater_id);
                CREATE INDEX IF NOT EXISTS idx_project_rating_overall_rating ON project_rating (overall_rating);
                CREATE INDEX IF NOT EXISTS idx_project_rating_created_at ON project_rating (created_at);
            """))
            
            # User Achievement table indexes have been removed
            
            # 7. Business Unit Program table indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_business_unit_program_business_unit ON business_unit_program (business_unit);
                CREATE INDEX IF NOT EXISTS idx_business_unit_program_program ON business_unit_program (program);
            """))
            
            db.session.commit()
            logger.info("✅ Created standard indexes")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error creating indexes: {e}")
            return False

def create_partial_indexes():
    """Create partial indexes for common query patterns"""
    with app.app_context():
        try:
            # 1. Partial index for unread notifications
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notification_unread 
                ON notification (user_id) 
                WHERE read = false;
            """))
            
            # 2. Partial index for draft projects
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_project_draft 
                ON project (created_by) 
                WHERE status = 'Draft';
            """))
            
            # 3. Partial index for submitted projects
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_project_submitted 
                ON project (created_at) 
                WHERE status = 'Submitted';
            """))
            
            # 4. Partial index for approved projects
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_project_approved 
                ON project (approval_date) 
                WHERE status = 'Approved';
            """))
            
            # 5. Partial index for OCP projects
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_project_ocp 
                ON project (created_at, business_unit) 
                WHERE project_type = 'OCP';
            """))
            
            db.session.commit()
            logger.info("✅ Created partial indexes")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error creating partial indexes: {e}")
            return False

def optimize_db_settings():
    """Optimize PostgreSQL-specific settings for improved performance"""
    with app.app_context():
        try:
            # 1. Enable connection pooling in application level
            # This is already done in the app.config["SQLALCHEMY_ENGINE_OPTIONS"]
            logger.info("✅ Connection pooling is already configured in app settings")
            
            # 2. Update table statistics for better query planning
            # Note: 'user' is a reserved word in PostgreSQL and needs to be quoted
            table_names = [
                '"user"', 'project', 'project_history', 'notification', 
                'historical_rate', 'achievement', 'user_achievement',
                'project_rating', 'business_unit_program', 'bulk_estimate_import'
            ]
            
            for table in table_names:
                db.session.execute(text(f"ANALYZE {table};"))
                
            logger.info("✅ Updated table statistics with ANALYZE")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error optimizing database settings: {e}")
            return False

def vacuum_analyze():
    """Run ANALYZE to update statistics (skipping VACUUM due to transaction requirements)"""
    with app.app_context():
        try:
            # Update statistics for all tables (ANALYZE can run in a transaction, VACUUM cannot)
            # Note: 'user' is a reserved word in PostgreSQL and needs to be quoted
            table_names = [
                '"user"', 'project', 'project_history', 'notification', 
                'historical_rate', 'achievement', 'user_achievement',
                'project_rating', 'business_unit_program', 'bulk_estimate_import'
            ]
            
            for table in table_names:
                db.session.execute(text(f"ANALYZE {table};"))
                
            logger.info("✅ Ran ANALYZE on all tables")
            return True
        except Exception as e:
            logger.error(f"❌ Error running ANALYZE: {e}")
            return False

def main():
    """Main function to run the optimization process"""
    logger.info("=== PostgreSQL Optimization ===")
    
    # Check if using PostgreSQL
    check_database_type()
    
    # Create standard indexes
    indexes_created = create_indexes()
    
    # Create partial indexes
    partial_indexes_created = create_partial_indexes()
    
    # Optimize database settings
    settings_optimized = optimize_db_settings()
    
    # Update statistics
    stats_updated = vacuum_analyze()
    
    # Summary
    logger.info("\n=== Optimization Summary ===")
    logger.info(f"Standard Indexes: {'✅ Created' if indexes_created else '❌ Failed'}")
    logger.info(f"Partial Indexes: {'✅ Created' if partial_indexes_created else '❌ Failed'}")
    logger.info(f"Database Settings: {'✅ Optimized' if settings_optimized else '❌ Failed'}")
    logger.info(f"Statistics: {'✅ Updated' if stats_updated else '❌ Failed'}")
    
    if indexes_created and partial_indexes_created and settings_optimized and stats_updated:
        logger.info("\n=== ✅ PostgreSQL Optimization Successful ===")
    else:
        logger.warning("\n=== ⚠️ PostgreSQL Optimization Partially Successful ===")
        logger.warning("Some operations failed. Check the logs for details.")

if __name__ == "__main__":
    main()