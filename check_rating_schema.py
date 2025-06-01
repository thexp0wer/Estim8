from app import app, db
from sqlalchemy import text

with app.app_context():
    # Get the schema of the project_rating table
    result = db.session.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'project_rating'
        ORDER BY ordinal_position
    """)).fetchall()
    
    print("Project Rating table schema:")
    for col in result:
        print(f"  - {col[0]} ({col[1]})")