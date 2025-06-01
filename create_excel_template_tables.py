"""
Create Excel Template Tables
This script creates the necessary tables and columns for Excel-based deliverables estimation
"""

from app import app, db
from models import ExcelTemplate
import sqlalchemy as sa

def create_excel_tables():
    """Create Excel Template table and add columns to DeliverableUpload"""
    with app.app_context():
        # Create excel_template table if it doesn't exist
        inspector = sa.inspect(db.engine)
        if 'excel_template' not in inspector.get_table_names():
            ExcelTemplate.__table__.create(bind=db.engine)
            print("Created excel_template table")
        else:
            print("excel_template table already exists")
        
        # Check if deliverable_upload table exists and add columns
        inspector = sa.inspect(db.engine)
        table_names = inspector.get_table_names()
        
        try:
            conn = db.engine.connect()
            
            # Only proceed if deliverable_upload table exists
            if 'deliverable_upload' in table_names:
                columns = [col['name'] for col in inspector.get_columns('deliverable_upload')]
                
                # Add columns if they don't exist
                # Using direct execution with proper SQL syntax
                try:
                    if 'project_id' not in columns:
                        conn.execute(sa.text(
                            "ALTER TABLE deliverable_upload ADD COLUMN project_id INTEGER REFERENCES project(id)"
                        ))
                        print("Added project_id column to deliverable_upload")
                except Exception as e:
                    print(f"Error adding project_id column: {str(e)}")
                
                try:
                    if 'discipline' not in columns:
                        conn.execute(sa.text(
                            "ALTER TABLE deliverable_upload ADD COLUMN discipline VARCHAR(100)"
                        ))
                        print("Added discipline column to deliverable_upload")
                except Exception as e:
                    print(f"Error adding discipline column: {str(e)}")
                
                try:
                    if 'is_estimate_sheet' not in columns:
                        conn.execute(sa.text(
                            "ALTER TABLE deliverable_upload ADD COLUMN is_estimate_sheet BOOLEAN DEFAULT FALSE"
                        ))
                        print("Added is_estimate_sheet column to deliverable_upload")
                except Exception as e:
                    print(f"Error adding is_estimate_sheet column: {str(e)}")
                
                try:
                    if 'template_id' not in columns:
                        conn.execute(sa.text(
                            "ALTER TABLE deliverable_upload ADD COLUMN template_id INTEGER REFERENCES excel_template(id)"
                        ))
                        print("Added template_id column to deliverable_upload")
                except Exception as e:
                    print(f"Error adding template_id column: {str(e)}")
                    
                try:
                    if 'last_accessed' not in columns:
                        conn.execute(sa.text(
                            "ALTER TABLE deliverable_upload ADD COLUMN last_accessed TIMESTAMP"
                        ))
                        print("Added last_accessed column to deliverable_upload")
                except Exception as e:
                    print(f"Error adding last_accessed column: {str(e)}")
            else:
                print("deliverable_upload table does not exist, skipping column additions")
            
            conn.close()
            
        except Exception as e:
            print(f"Error updating tables: {str(e)}")
            db.session.rollback()
            raise
        
        # Commit the changes
        db.session.commit()
        print("Migration completed successfully")

if __name__ == "__main__":
    create_excel_tables()