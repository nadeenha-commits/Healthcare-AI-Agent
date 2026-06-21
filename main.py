#!/usr/bin/env python
"""
Healthcare AI Agent - Main Entry Point
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import and create Flask app
from backend.app import app

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    print(f"Starting Healthcare AI Agent on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
