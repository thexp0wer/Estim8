"""
Simple script to rename requirements-export.txt to requirements.txt
"""
import os
import shutil

try:
    # Check if source file exists
    if os.path.exists('requirements-export.txt'):
        # Check if destination file already exists and remove it if needed
        if os.path.exists('requirements.txt'):
            os.remove('requirements.txt')
        
        # Copy the file (instead of rename, to avoid potential permission issues)
        shutil.copy('requirements-export.txt', 'requirements.txt')
        print("Successfully created requirements.txt")
    else:
        print("Source file requirements-export.txt not found")
except Exception as e:
    print(f"Error: {e}")