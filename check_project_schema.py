from app import app, db
from sqlalchemy import text

with app.app_context():
    # Get the schema of the project table
    result = db.session.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'project'
        ORDER BY ordinal_position
    """)).fetchall()
    
    print("Project table schema:")
    for col in result:
        print(f"  - {col[0]} ({col[1]})")
        
    # Check for the validation date field (could be named differently)
    result = db.session.execute(text("""
        SELECT column_name
        FROM information_schema.columns 
        WHERE table_name = 'project'
        AND (
            column_name LIKE '%valid%' OR 
            column_name LIKE '%approv%' OR
            column_name LIKE '%date%'
        )
    """)).fetchall()
    
    print("\nPossible validation date columns:")
    for col in result:
        print(f"  - {col[0]}")