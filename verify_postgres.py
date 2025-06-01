#!/usr/bin/env python
"""
Script to verify PostgreSQL migration.
This script performs a set of tests to verify the application works correctly with PostgreSQL.
"""

import os
import sys
import logging
from sqlalchemy import text
from app import app, db
from models import User, Project, Notification, ProjectHistory

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_type():
    """Check if the app is using PostgreSQL"""
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    using_postgres = db_url.startswith('postgresql://')
    logger.info(f"Using PostgreSQL: {using_postgres}")
    logger.info(f"Database URL: {db_url}")
    return using_postgres

def check_tables():
    """Check if all required tables exist"""
    with app.app_context():
        # Get all tables from database
        tables = db.session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)).fetchall()
        
        table_names = [table[0] for table in tables]
        logger.info(f"Found {len(table_names)} tables: {', '.join(table_names)}")
        
        # Required tables for the application
        required_tables = [
            'user', 'project', 'project_history', 'notification', 
            'historical_rate', 'achievement', 'user_achievement',
            'project_rating', 'business_unit_program', 'bulk_estimate_import'
        ]
        
        # Check if all required tables exist
        missing_tables = [table for table in required_tables if table not in table_names]
        if missing_tables:
            logger.error(f"Missing tables: {', '.join(missing_tables)}")
            return False
        
        logger.info("✅ All required tables exist")
        return True

def check_data():
    """Check if data exists in the tables"""
    with app.app_context():
        # Check if users exist
        user_count = User.query.count()
        logger.info(f"User count: {user_count}")
        
        # Check if projects exist
        project_count = Project.query.count()
        logger.info(f"Project count: {project_count}")
        
        # Check if notifications exist
        notification_count = Notification.query.count()
        logger.info(f"Notification count: {notification_count}")
        
        # Check if project history exists
        history_count = ProjectHistory.query.count()
        logger.info(f"Project history count: {history_count}")
        
        # Data validation
        if user_count == 0:
            logger.warning("⚠️ No users found in database")
            # We will still return True since this might be a fresh installation
        
        return True

def check_relationships():
    """Check if relationships between tables work correctly"""
    with app.app_context():
        try:
            # Find an admin user
            admin = User.query.filter_by(is_admin=True).first()
            
            if admin:
                logger.info(f"Found admin user: {admin.username}")
                
                # Check relationships
                logger.info(f"Projects created by admin: {len(admin.projects_created)}")
                logger.info(f"Notifications for admin: {len(admin.notifications)}")
                
                # Find a project
                project = Project.query.first()
                if project:
                    logger.info(f"Found project: {project.title}")
                    logger.info(f"Project creator: {project.creator.username if project.creator else 'None'}")
                    
                    # Check project history
                    history_count = ProjectHistory.query.filter_by(project_id=project.id).count()
                    logger.info(f"Project history entries: {history_count}")
                
                logger.info("✅ Relationships tests passed")
                return True
            else:
                logger.warning("⚠️ No admin user found for relationship tests")
                return True  # Still return True for a fresh installation
                
        except Exception as e:
            logger.error(f"❌ Relationship tests failed: {e}")
            return False

def check_queries():
    """Test various queries to ensure they work with PostgreSQL"""
    with app.app_context():
        try:
            # Test 1: Complex join query
            result1 = db.session.execute(text("""
                SELECT p.id, p.title, p.status, u.username
                FROM project p
                JOIN "user" u ON p.created_by = u.id
                ORDER BY p.created_at DESC
                LIMIT 5
            """)).fetchall()
            logger.info(f"Complex join query returned {len(result1)} rows")
            
            # Test 2: Aggregate query
            result2 = db.session.execute(text("""
                SELECT status, COUNT(*) 
                FROM project 
                GROUP BY status
            """)).fetchall()
            logger.info("Aggregate query results:")
            for row in result2:
                logger.info(f"  {row[0]}: {row[1]}")
            
            # Test 3: Date based query
            result3 = db.session.execute(text("""
                SELECT 
                    DATE_TRUNC('month', created_at) as month,
                    COUNT(*) as count
                FROM project
                GROUP BY month
                ORDER BY month DESC
                LIMIT 6
            """)).fetchall()
            logger.info("Date-based query results:")
            for row in result3:
                logger.info(f"  {row[0]}: {row[1]}")
            
            logger.info("✅ Query tests passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Query tests failed: {e}")
            return False

def main():
    """Main function to verify PostgreSQL migration"""
    logger.info("=== PostgreSQL Migration Verification ===")
    
    # Check if using PostgreSQL
    if not check_database_type():
        logger.error("The application is not configured to use PostgreSQL. "
                    "Please set the DATABASE_URL environment variable to a PostgreSQL URL.")
        sys.exit(1)
    
    # Run all verification checks
    tables_ok = check_tables()
    data_ok = check_data()
    relationships_ok = check_relationships()
    queries_ok = check_queries()
    
    # Final verification result
    if tables_ok and data_ok and relationships_ok and queries_ok:
        logger.info("=== ✅ PostgreSQL Migration Verification Successful ===")
        logger.info("The application is correctly configured to use PostgreSQL.")
    else:
        logger.error("=== ❌ PostgreSQL Migration Verification Failed ===")
        logger.error("Please check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()