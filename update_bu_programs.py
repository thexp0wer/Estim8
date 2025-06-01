#!/usr/bin/env python3
"""
Script to update the BusinessUnitProgram model with the latest business unit and program mapping.
This ensures the database has the correct mappings based on the centralized definition.
"""

import os
import sys
from app import app, db
from models import BusinessUnitProgram
from utils.business_units import BU_PROGRAM_MAPPING

def update_bu_programs():
    """Update the business units and programs in the database"""
    print("Starting update of business units and programs...")
    
    try:
        with app.app_context():
            # First, get existing relationships to track changes
            existing_programs = {}
            for bu_program in BusinessUnitProgram.query.all():
                if bu_program.business_unit not in existing_programs:
                    existing_programs[bu_program.business_unit] = []
                existing_programs[bu_program.business_unit].append(bu_program.program)
            
            # Count stats for reporting
            updated_count = 0
            added_count = 0
            
            # Update database with new mapping
            for bu, programs in BU_PROGRAM_MAPPING.items():
                for program in programs:
                    # Check if this combination already exists
                    existing = BusinessUnitProgram.query.filter_by(
                        business_unit=bu, program=program).first()
                    
                    if not existing:
                        # Add new mapping
                        db.session.add(BusinessUnitProgram(
                            business_unit=bu,
                            program=program
                        ))
                        added_count += 1
                        print(f"  Adding: {bu} - {program}")
                    else:
                        updated_count += 1
            
            # Commit all changes
            db.session.commit()
            
            print(f"Update complete: {added_count} new relationships added, {updated_count} existing relationships preserved")
            return True
    
    except Exception as e:
        print(f"Error updating business units and programs: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    success = update_bu_programs()
    sys.exit(0 if success else 1)