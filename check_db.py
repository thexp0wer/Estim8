from app import app, db
from sqlalchemy import text

with app.app_context():
    print(f'Using database: {app.config["SQLALCHEMY_DATABASE_URI"]}')
    
    # Try connecting to the database
    try:
        result = db.session.execute(text('SELECT 1')).scalar()
        print(f'Database connection successful: {result}')
        
        # Get tables
        tables = db.session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)).fetchall()
        
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
            
    except Exception as e:
        print(f'Database connection failed: {e}')