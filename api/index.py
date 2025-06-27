"""
Vercel entry point for the Hospital Equipment Maintenance Management System.
This file provides a lightweight entry point for Vercel deployment.
"""

import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app

# Set production environment if not already set
if 'FLASK_ENV' not in os.environ:
    os.environ['FLASK_ENV'] = 'production'

# Create the Flask application instance
app = create_app()

# Vercel expects the app to be available directly
if __name__ == "__main__":
    app.run(debug=False) 