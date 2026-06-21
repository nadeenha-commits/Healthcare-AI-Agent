#!/usr/bin/env python
"""
Quick test script to verify all imports work correctly.
Run this to check for import errors before starting the app.
"""
import sys
import os

# Add backend to path (same as main.py does)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 60)
print("HEALTHCARE AI AGENT - Import Verification Test")
print("=" * 60)

try:
    print("\n✓ Testing backend package structure...")
    import backend
    print("  ✓ backend package imported")

    print("\n✓ Testing database layer...")
    from backend.db import models
    from backend.db import database
    print("  ✓ db.models imported")
    print("  ✓ db.database imported")

    print("\n✓ Testing configuration...")
    from backend import config
    print("  ✓ config imported")

    print("\n✓ Testing services layer...")
    from backend.services import auth_service
    from backend.services import patient_service
    from backend.services import appointment_service
    from backend.services import analytics_service
    print("  ✓ auth_service imported")
    print("  ✓ patient_service imported")
    print("  ✓ appointment_service imported")
    print("  ✓ analytics_service imported")

    print("\n✓ Testing utils layer...")
    from backend.utils import security
    from backend.utils import responses
    print("  ✓ security imported")
    print("  ✓ responses imported")

    print("\n✓ Testing routes layer...")
    from backend.routes import auth_routes
    from backend.routes import patient_routes
    from backend.routes import doctor_routes
    from backend.routes import appointment_routes
    from backend.routes import treatment_routes
    from backend.routes import analytics_routes
    from backend.routes import agent_routes
    from backend.routes import department_routes
    print("  ✓ auth_routes imported")
    print("  ✓ patient_routes imported")
    print("  ✓ doctor_routes imported")
    print("  ✓ appointment_routes imported")
    print("  ✓ treatment_routes imported")
    print("  ✓ analytics_routes imported")
    print("  ✓ agent_routes imported")
    print("  ✓ department_routes imported")

    print("\n✓ Testing agent layer...")
    from backend.agent import agent
    from backend.agent import tools
    from backend.agent import prompts
    from backend.agent import gemini_client
    print("  ✓ agent imported")
    print("  ✓ tools imported")
    print("  ✓ prompts imported")
    print("  ✓ gemini_client imported")

    print("\n✓ Testing Flask app...")
    from backend.app import app
    print("  ✓ Flask app imported and created")

    print("\n" + "=" * 60)
    print("✅ ALL IMPORTS SUCCESSFUL!")
    print("=" * 60)
    print("\nYour project is ready to run. Try:")
    print("  python main.py")
    print("\nOr with Docker:")
    print("  docker compose up --build")
    print("=" * 60)

except ImportError as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    print("\nThis likely means:")
    print("  - Missing required package (install with: pip install -r backend/requirements.txt)")
    print("  - Missing __init__.py file")
    print("  - Wrong import path")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print(f"Error type: {type(e).__name__}")
    sys.exit(1)

