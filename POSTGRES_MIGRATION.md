# PostgreSQL Migration Guide

This guide explains how to migrate the EstimateTracker application from SQLite to PostgreSQL.

## Status of Implementation

The PostgreSQL migration has been implemented with the following components:

1. **Database Configuration Updates**
   - The application now properly handles PostgreSQL connection strings
   - Enhanced connection pool settings for optimal performance
   - Compatible with both development (SQLite) and production (PostgreSQL) environments

2. **Migration Scripts**
   - `migrate_to_postgres.py`: Core script to transfer data from SQLite to PostgreSQL
   - `run_migration.py`: User-friendly wrapper to handle the migration process with error handling
   - `optimize_postgres.py`: Script to create indexes and optimize PostgreSQL settings
   - `db_health_check.py`: Tool to monitor database health and performance

3. **PostgreSQL Optimizations**
   - Comprehensive indexing strategy for faster queries
   - Connection pooling settings for better resource utilization
   - Partial indexes for common query patterns
   - Database health monitoring tools

## How to Migrate

### Prerequisites

1. Ensure you have PostgreSQL installed and running
2. Set the `DATABASE_URL` environment variable to your PostgreSQL connection string:
   ```
   export DATABASE_URL=postgresql://username:password@hostname:port/database
   ```

### Migration Steps

1. **Backup your existing SQLite data**
   ```
   python run_migration.py
   ```
   This will automatically create a backup of your SQLite database before migration.

2. **Run the migration**
   The migration script will:
   - Connect to both databases
   - Create all necessary tables in PostgreSQL
   - Copy all data from SQLite to PostgreSQL
   - Handle data type conversions as needed

3. **Optimize PostgreSQL**
   ```
   python optimize_postgres.py
   ```
   This will create indexes and optimize settings for better performance.

4. **Run health check**
   ```
   python db_health_check.py
   ```
   This will verify the database is healthy and provide performance insights.

## Production Deployment

For production deployment:

1. Ensure the `DATABASE_URL` environment variable is set to your PostgreSQL connection string
2. The application will automatically use PostgreSQL when this variable is set
3. SQLite will only be used as a fallback during development

## Database Pool Configuration

The application is configured with the following connection pool settings:
- `pool_recycle`: 300 seconds (5 minutes) - Connections are recycled after this period
- `pool_pre_ping`: True - Connections are verified before use
- `pool_size`: 10 - Maximum number of persistent connections
- `max_overflow`: 20 - Maximum additional connections

## Troubleshooting

If you encounter problems during migration:

1. Check the logs for detailed error messages
2. Verify your PostgreSQL connection string is correct
3. Make sure your PostgreSQL user has sufficient privileges
4. Ensure your SQLite database exists and is not corrupted