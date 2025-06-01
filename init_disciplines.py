#!/usr/bin/env python3
"""
Script to initialize the discipline table with default values.
This will add standard engineering disciplines to the database.
"""
import os
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create a minimal Flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db = SQLAlchemy(app)

# Define model for script
class Discipline(db.Model):
    __tablename__ = 'discipline'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def init_disciplines():
    """Initialize the discipline table with default values."""
    # Standard engineering disciplines
    disciplines = [
        "Process SID",
        "Civil Structure",
        "Piping",
        "Mechanical",
        "Electrical",
        "Instrumentation Control",
        "Digitalization",
        "Engineering Management",
        "Environmental",
        "Tools Admin",
        "Construction",
    ]
    
    # Check if disciplines already exist
    existing_count = Discipline.query.count()
    if existing_count > 0:
        print(f"Found {existing_count} existing disciplines. No action taken.")
        return
    
    # Add disciplines
    for name in disciplines:
        discipline = Discipline(name=name)
        db.session.add(discipline)
    
    try:
        db.session.commit()
        print(f"Successfully added {len(disciplines)} disciplines to the database.")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding disciplines: {str(e)}")

if __name__ == "__main__":
    with app.app_context():
        init_disciplines()