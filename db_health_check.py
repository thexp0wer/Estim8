#!/usr/bin/env python
"""
PostgreSQL database health check script.
Runs various tests on the database to check for health and performance issues.
"""

import os
import sys
import logging
import time
from datetime import datetime, timedelta
from sqlalchemy import text, func
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

def check_connection():
    """Check if we can connect to the database"""
    with app.app_context():
        try:
            result = db.session.execute(text('SELECT 1')).scalar()
            logger.info(f"✅ Database connection successful: {result}")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

def get_db_size():
    """Get the size of the database"""
    with app.app_context():
        try:
            result = db.session.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database()));
            """)).scalar()
            logger.info(f"📊 Database size: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Error getting database size: {e}")
            return None

def get_table_sizes():
    """Get sizes of all tables"""
    with app.app_context():
        try:
            result = db.session.execute(text("""
                SELECT 
                    relname as table_name,
                    pg_size_pretty(pg_total_relation_size(c.oid)) as total_size,
                    pg_size_pretty(pg_relation_size(c.oid)) as data_size,
                    pg_size_pretty(pg_total_relation_size(c.oid) - pg_relation_size(c.oid)) as external_size
                FROM 
                    pg_class c
                LEFT JOIN 
                    pg_namespace n ON n.oid = c.relnamespace
                WHERE 
                    n.nspname = 'public' AND 
                    c.relkind = 'r'
                ORDER BY 
                    pg_total_relation_size(c.oid) DESC
                LIMIT 10;
            """)).fetchall()
            
            logger.info("📊 Table sizes:")
            for row in result:
                logger.info(f"  - {row[0]}: {row[1]} (data: {row[2]}, indexes: {row[3]})")
            
            return result
        except Exception as e:
            logger.error(f"❌ Error getting table sizes: {e}")
            return None

def check_active_connections():
    """Check active connections to the database"""
    with app.app_context():
        try:
            result = db.session.execute(text("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections,
                    count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction_connections
                FROM 
                    pg_stat_activity
                WHERE 
                    datname = current_database();
            """)).fetchone()
            
            logger.info(f"📊 Database connections:")
            logger.info(f"  - Total: {result[0]}")
            logger.info(f"  - Active: {result[1]}")
            logger.info(f"  - Idle: {result[2]}")
            logger.info(f"  - Idle in transaction: {result[3]}")
            
            # Check for long-running transactions
            long_running = db.session.execute(text("""
                SELECT 
                    pid, 
                    usename, 
                    application_name,
                    state, 
                    pg_size_pretty(pg_xact_commit_timestamp(xmin))::text as transaction_start,
                    query
                FROM 
                    pg_stat_activity
                WHERE 
                    datname = current_database()
                    AND state = 'active'
                    AND (now() - query_start) > interval '5 minutes'
                ORDER BY 
                    query_start;
            """)).fetchall()
            
            if long_running:
                logger.warning(f"⚠️ Long running queries found ({len(long_running)}):")
                for row in long_running:
                    logger.warning(f"  - PID {row[0]} ({row[1]}, {row[2]}): {row[3]} since {row[4]}")
                    logger.warning(f"    Query: {row[5][:100]}...")
            else:
                logger.info("✅ No long running queries found")
            
            return result
        except Exception as e:
            logger.error(f"❌ Error checking connections: {e}")
            return None

def check_long_running_queries():
    """Check for long running queries"""
    with app.app_context():
        try:
            result = db.session.execute(text("""
                SELECT 
                    pid, 
                    usename, 
                    query_start, 
                    extract(epoch from (now() - query_start)) as duration_seconds,
                    state,
                    query
                FROM 
                    pg_stat_activity
                WHERE 
                    datname = current_database()
                    AND state = 'active'
                    AND query_start is not null
                ORDER BY 
                    duration_seconds DESC
                LIMIT 5;
            """)).fetchall()
            
            if result:
                logger.info("📊 Top 5 longest running queries:")
                for row in result:
                    duration = f"{row[3]:.1f} seconds"
                    logger.info(f"  - PID {row[0]} ({row[1]}): {duration} - {row[4]}")
                    logger.info(f"    Query: {row[5][:100]}...")
            else:
                logger.info("✅ No active queries found")
            
            return result
        except Exception as e:
            logger.error(f"❌ Error checking long running queries: {e}")
            return None

def check_index_usage():
    """Check index usage statistics"""
    with app.app_context():
        try:
            result = db.session.execute(text("""
                SELECT
                    schemaname || '.' || relname as table,
                    indexrelname as index,
                    pg_size_pretty(pg_relation_size(i.indexrelid)) as index_size,
                    idx_scan as index_scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched
                FROM
                    pg_stat_user_indexes ui
                JOIN
                    pg_index i ON ui.indexrelid = i.indexrelid
                WHERE
                    schemaname = 'public'
                ORDER BY
                    idx_scan DESC
                LIMIT 10;
            """)).fetchall()
            
            if result:
                logger.info("📊 Top 10 most used indexes:")
                for row in result:
                    logger.info(f"  - {row[1]} on {row[0]}: {row[2]}, scans: {row[3]}, reads: {row[4]}, fetches: {row[5]}")
            else:
                logger.info("⚠️ No index usage statistics found")
            
            # Find unused indexes
            unused = db.session.execute(text("""
                SELECT
                    schemaname || '.' || relname as table,
                    indexrelname as index,
                    pg_size_pretty(pg_relation_size(i.indexrelid)) as index_size,
                    idx_scan as index_scans
                FROM
                    pg_stat_user_indexes ui
                JOIN
                    pg_index i ON ui.indexrelid = i.indexrelid
                WHERE
                    schemaname = 'public'
                    AND idx_scan = 0
                    AND i.indisprimary = false
                    AND i.indisunique = false
                ORDER BY
                    pg_relation_size(i.indexrelid) DESC
                LIMIT 10;
            """)).fetchall()
            
            if unused:
                logger.warning("⚠️ Unused indexes (excluding primary/unique keys):")
                for row in unused:
                    logger.warning(f"  - {row[1]} on {row[0]}: {row[2]}, scans: {row[3]}")
            else:
                logger.info("✅ No unused indexes found")
            
            return result
        except Exception as e:
            logger.error(f"❌ Error checking index usage: {e}")
            return None

def check_table_bloat():
    """Check for table bloat (tables that need vacuuming)"""
    with app.app_context():
        try:
            result = db.session.execute(text("""
                SELECT
                    schemaname || '.' || relname as table,
                    n_dead_tup as dead_tuples,
                    n_live_tup as live_tuples,
                    round(n_dead_tup::numeric / GREATEST(n_live_tup, 1), 4) * 100 as dead_percentage
                FROM
                    pg_stat_user_tables
                WHERE
                    schemaname = 'public'
                    AND n_dead_tup > 0
                ORDER BY
                    dead_percentage DESC
                LIMIT 10;
            """)).fetchall()
            
            if result:
                logger.info("📊 Tables that might need VACUUM:")
                for row in result:
                    logger.info(f"  - {row[0]}: {row[1]} dead tuples ({row[3]:.2f}% of {row[2]} live tuples)")
                    if row[3] > 20:
                        logger.warning(f"  ⚠️ {row[0]} has high bloat ({row[3]:.2f}%), consider VACUUM")
            else:
                logger.info("✅ No table bloat detected")
            
            return result
        except Exception as e:
            logger.error(f"❌ Error checking table bloat: {e}")
            return None

def check_missing_indexes():
    """Check for potential missing indexes based on table scans"""
    with app.app_context():
        try:
            result = db.session.execute(text("""
                SELECT
                    schemaname || '.' || relname as table,
                    seq_scan as sequential_scans,
                    idx_scan as index_scans,
                    n_live_tup as live_tuples
                FROM
                    pg_stat_user_tables
                WHERE
                    schemaname = 'public'
                    AND seq_scan > 0
                    AND (seq_scan > idx_scan OR idx_scan IS NULL)
                    AND n_live_tup > 100
                ORDER BY
                    seq_scan DESC
                LIMIT 10;
            """)).fetchall()
            
            if result:
                logger.warning("⚠️ Tables with high sequential scans (possibly missing indexes):")
                for row in result:
                    idx_scan_str = "0" if row[2] is None else str(row[2])
                    logger.warning(f"  - {row[0]}: {row[1]} sequential scans vs {idx_scan_str} index scans, {row[3]} rows")
            else:
                logger.info("✅ No tables with excessive sequential scans")
            
            return result
        except Exception as e:
            logger.error(f"❌ Error checking for missing indexes: {e}")
            return None

def check_query_performance():
    """Run a few common queries and check their performance"""
    with app.app_context():
        try:
            # Common queries to test
            queries = [
                ("List all projects", "SELECT * FROM project LIMIT 10"),
                ("Count projects by status", "SELECT status, COUNT(*) FROM project GROUP BY status"),
                ("Count users by role", "SELECT role, COUNT(*) FROM \"user\" GROUP BY role"),
                ("Complex join", """
                    SELECT p.title, p.status, u.username 
                    FROM project p
                    JOIN \"user\" u ON p.created_by = u.id
                    WHERE p.status = 'Draft'
                    LIMIT 10
                """),
                ("Notification query", """
                    SELECT n.message, u.username
                    FROM notification n
                    JOIN \"user\" u ON n.user_id = u.id
                    WHERE n.read = false
                    LIMIT 10
                """),
            ]
            
            results = []
            logger.info("📊 Query performance test:")
            
            for name, query in queries:
                start_time = time.time()
                result = db.session.execute(text(query)).fetchall()
                end_time = time.time()
                duration = (end_time - start_time) * 1000  # ms
                
                row_count = len(result)
                results.append((name, duration, row_count))
                logger.info(f"  - {name}: {duration:.2f}ms for {row_count} rows")
                
                if duration > 100:
                    logger.warning(f"  ⚠️ Slow query: {name} took {duration:.2f}ms")
            
            return results
        except Exception as e:
            logger.error(f"❌ Error running performance tests: {e}")
            return None

def suggest_optimizations():
    """Suggest database optimizations based on health check results"""
    with app.app_context():
        logger.info("\n🔧 Optimization suggestions:")
        
        # Check for missing indexes
        missing_indexes = db.session.execute(text("""
            SELECT
                schemaname || '.' || relname as table,
                seq_scan as sequential_scans,
                idx_scan as index_scans,
                n_live_tup as live_tuples,
                attname as column
            FROM
                pg_stat_user_tables
            JOIN
                pg_attribute a ON a.attrelid = relid
            WHERE
                schemaname = 'public'
                AND seq_scan > idx_scan
                AND n_live_tup > 100
                AND a.attnum > 0
                AND NOT a.attisdropped
            ORDER BY
                seq_scan DESC,
                n_live_tup DESC
            LIMIT
                20;
        """)).fetchall()
        
        if missing_indexes:
            logger.info("1. Consider adding indexes to these tables/columns:")
            for row in missing_indexes:
                logger.info(f"   CREATE INDEX ON {row[0]} ({row[4]});")
        
        # Check for bloated tables
        bloated_tables = db.session.execute(text("""
            SELECT
                schemaname || '.' || relname as table,
                round(n_dead_tup::numeric / GREATEST(n_live_tup, 1), 4) * 100 as dead_percentage
            FROM
                pg_stat_user_tables
            WHERE
                schemaname = 'public'
                AND n_dead_tup > 0
                AND round(n_dead_tup::numeric / GREATEST(n_live_tup, 1), 4) * 100 > 10
            ORDER BY
                dead_percentage DESC
            LIMIT 5;
        """)).fetchall()
        
        if bloated_tables:
            logger.info("2. Run VACUUM on these bloated tables:")
            for row in bloated_tables:
                logger.info(f"   VACUUM {row[0]};  -- {row[1]:.2f}% bloat")
        
        # Check for outdated statistics
        outdated_stats = db.session.execute(text("""
            SELECT
                schemaname || '.' || relname as table,
                last_analyze,
                last_autoanalyze
            FROM
                pg_stat_user_tables
            WHERE
                schemaname = 'public'
                AND (last_analyze IS NULL OR last_analyze < now() - interval '1 day')
                AND (last_autoanalyze IS NULL OR last_autoanalyze < now() - interval '1 day')
            ORDER BY
                coalesce(last_analyze, '1970-01-01'::timestamp),
                coalesce(last_autoanalyze, '1970-01-01'::timestamp)
            LIMIT 5;
        """)).fetchall()
        
        if outdated_stats:
            logger.info("3. Update statistics for these tables:")
            for row in outdated_stats:
                logger.info(f"   ANALYZE {row[0]};")
        
        # General recommendations
        logger.info("\n4. General recommendations:")
        logger.info("   - Run the optimize_postgres.py script regularly")
        logger.info("   - Set up regular VACUUM and ANALYZE operations")
        logger.info("   - Monitor query performance with query execution plans")
        logger.info("   - Use connection pooling for better resource utilization")

def main():
    """Main function to run the database health check"""
    logger.info("=== PostgreSQL Database Health Check ===")
    
    # Check if using PostgreSQL
    check_database_type()
    
    # Basic connection test
    connection_ok = check_connection()
    if not connection_ok:
        logger.error("❌ Cannot connect to the database. Aborting.")
        sys.exit(1)
    
    # Run all health checks
    get_db_size()
    get_table_sizes()
    check_active_connections()
    check_long_running_queries()
    check_index_usage()
    check_table_bloat()
    check_missing_indexes()
    check_query_performance()
    
    # Suggest optimizations
    suggest_optimizations()
    
    logger.info("\n=== ✅ Database Health Check Completed ===")

if __name__ == "__main__":
    main()