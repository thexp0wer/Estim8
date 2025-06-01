from app import app, db
from sqlalchemy import text

with app.app_context():
    # Get the schema of the notification table
    result = db.session.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'notification'
        ORDER BY ordinal_position
    """)).fetchall()
    
    print("Notification table schema:")
    for col in result:
        print(f"  - {col[0]} ({col[1]})")
    
    print("\nChecking table names with proper quoting:")
    # View all tables with proper quoting to ensure we're addressing "user" table correctly
    tables = db.session.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)).fetchall()
    
    print("All tables in database:")
    for table in tables:
        print(f"  - {table[0]}")