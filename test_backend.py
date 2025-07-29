#!/usr/bin/env python3
"""Test script to diagnose backend startup issues."""

import sys
import traceback

def test_imports():
    """Test all imports"""
    print("Testing imports...")
    
    try:
        import asyncio
        print("✅ asyncio")
    except Exception as e:
        print(f"❌ asyncio: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ uvicorn")
    except Exception as e:
        print(f"❌ uvicorn: {e}")
        return False
    
    try:
        import fastapi
        print("✅ fastapi")
    except Exception as e:
        print(f"❌ fastapi: {e}")
        return False
    
    try:
        from backend import models
        print("✅ backend.models")
    except Exception as e:
        print(f"❌ backend.models: {e}")
        return False
    
    try:
        from backend import database
        print("✅ backend.database")
    except Exception as e:
        print(f"❌ backend.database: {e}")
        return False
    
    try:
        from backend import api
        print("✅ backend.api")
    except Exception as e:
        print(f"❌ backend.api: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        import json
        import os
        
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config = json.load(f)
            print("✅ config.json loaded")
            print(f"   Database file: {config.get('database', {}).get('file', 'N/A')}")
            print(f"   Server port: {config.get('server', {}).get('port', 'N/A')}")
        else:
            print("❌ config.json not found")
            return False
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False
    
    return True

def test_database():
    """Test database initialization"""
    print("\nTesting database...")
    
    try:
        from backend.database import init_database
        import asyncio
        
        async def test_db():
            await init_database()
            print("✅ Database initialized")
        
        asyncio.run(test_db())
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    return True

def test_server_start():
    """Test starting the server"""
    print("\nTesting server startup...")
    
    try:
        from backend.api import app
        import uvicorn
        
        print("✅ FastAPI app created")
        print("ℹ️  Server would start on localhost:8000")
        print("ℹ️  Use: uvicorn.run(app, host='localhost', port=8000)")
        
    except Exception as e:
        print(f"❌ Server startup error: {e}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🔍 UpTime Monitor Backend Diagnostic\n")
    
    all_good = True
    
    all_good &= test_imports()
    all_good &= test_config()
    all_good &= test_database()
    all_good &= test_server_start()
    
    print(f"\n{'🎉 All tests passed!' if all_good else '❌ Some tests failed'}")
    
    if all_good:
        print("\n📋 To start the server manually:")
        print("   python -c \"import uvicorn; from backend.api import app; uvicorn.run(app, host='localhost', port=8000)\"")
    
    sys.exit(0 if all_good else 1)