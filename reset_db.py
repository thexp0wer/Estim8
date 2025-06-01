"""
Script to reset the database connection pool.
This helps recover from failed transaction states.
"""

from app import app, db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

with app.app_context():
    try:
        # Close all sessions and connections
        logger.info("Attempting to close all database sessions...")
        db.session.close()
        
        # Dispose of the engine to close all connections in the pool
        logger.info("Disposing the SQLAlchemy engine...")
        db.engine.dispose()
        
        # Create a new session
        logger.info("Creating a fresh database session...")
        db.session = db.create_scoped_session()
        
        # Test the connection with a simple query
        logger.info("Testing connection with a simple query...")
        db.session.execute("SELECT 1")
        
        logger.info("Database connection pool has been successfully reset!")
        print("Database connection pool has been successfully reset!")
    except Exception as e:
        logger.error(f"Error resetting database connection pool: {str(e)}")
        print(f"Error: {str(e)}")