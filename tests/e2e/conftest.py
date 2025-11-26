"""
Playwright Test Configuration
=============================
"""

import pytest
import subprocess
import time
import requests
import os
import sys
import logging
from pathlib import Path

# Add project root to path for backend imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

# Base URLs matching Makefile configuration
BASE_URL_FRONTEND = "http://localhost:8501"
BASE_URL_BACKEND = "http://localhost:8000"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def wait_for_health_check(url: str, max_wait_seconds: int = 15, check_interval: float = 0.5) -> bool:
    """
    Poll a health endpoint until it returns 200 or max_wait_seconds is reached.
    
    Args:
        url: The health endpoint URL to check
        max_wait_seconds: Maximum time to wait in seconds (default: 15)
        check_interval: Time between checks in seconds (default: 0.5)
    
    Returns:
        True if health check passed (200), False if timeout
    """
    start_time = time.time()
    elapsed = 0
    
    while elapsed < max_wait_seconds:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            pass
        
        time.sleep(check_interval)
        elapsed = time.time() - start_time
    
    return False


@pytest.fixture(scope="session")
def backend_server():
    """Start backend server for tests (skipped if SKIP_LIVE_BACKEND=1)."""
    # Skip if environment variable is set
    if os.getenv("SKIP_LIVE_BACKEND") == "1":
        print("⏭️  Skipping live backend server (SKIP_LIVE_BACKEND=1)")
        yield None
        return
    
    # Check if backend is already running
    if wait_for_health_check(f"{BASE_URL_BACKEND}/health", max_wait_seconds=2):
        print("✅ Backend already running")
        yield
        return
    
    # Start backend
    print("🚀 Starting backend server...")
    process = subprocess.Popen(
        ["python3", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    
    # Poll /health until it returns 200 (max 15 seconds)
    print("⏳ Waiting for backend to be ready (polling /health)...")
    if wait_for_health_check(f"{BASE_URL_BACKEND}/health", max_wait_seconds=15):
        print("✅ Backend is ready")
    else:
        process.kill()
        pytest.fail("Backend server failed to start: /health did not return 200 within 15 seconds")
    
    yield
    
    # Cleanup
    print("🛑 Stopping backend server...")
    try:
        process.terminate()
        process.wait(timeout=5)
    except:
        process.kill()


@pytest.fixture(scope="session")
def frontend_server():
    """Start frontend server for tests"""
    # Check if frontend is already running
    if wait_for_health_check(BASE_URL_FRONTEND, max_wait_seconds=2):
        print("✅ Frontend already running")
        yield
        return
    
    # Start frontend
    print("🚀 Starting frontend server...")
    process = subprocess.Popen(
        ["streamlit", "run", "frontend/Home.py", "--server.port", "8501", "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    
    # Poll frontend root URL until it returns 200 (max 15 seconds)
    # Streamlit doesn't have a /health endpoint, so we check the root URL
    print("⏳ Waiting for frontend to be ready (polling root URL)...")
    if wait_for_health_check(BASE_URL_FRONTEND, max_wait_seconds=15):
        print("✅ Frontend is ready")
    else:
        process.kill()
        pytest.fail("Frontend server failed to start: root URL did not return 200 within 15 seconds")
    
    yield
    
    # Cleanup
    print("🛑 Stopping frontend server...")
    try:
        process.terminate()
        process.wait(timeout=5)
    except:
        process.kill()


def check_database_schema() -> bool:
    """
    Check if the database schema matches current models.
    
    Returns:
        True if schema is up-to-date, False if outdated
    """
    try:
        from backend.db.base import engine
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        
        # Check if users table exists
        if "users" not in inspector.get_table_names():
            logger.warning("⚠️  Database schema check: 'users' table not found")
            return False
        
        # Get columns from users table
        users_columns = {col["name"]: col for col in inspector.get_columns("users")}
        
        # Check for required columns based on current User model
        required_columns = {
            "id": "INTEGER",
            "username": "VARCHAR",
            "email": "VARCHAR",  # This was missing in old schema
            "hashed_password": "VARCHAR",
            "is_active": "BOOLEAN",
            "created_at": "DATETIME",
            "updated_at": "DATETIME",
        }
        
        missing_columns = []
        for col_name, col_type in required_columns.items():
            if col_name not in users_columns:
                missing_columns.append(col_name)
                logger.warning(f"⚠️  Database schema check: Missing column 'users.{col_name}'")
        
        if missing_columns:
            logger.warning(f"⚠️  Database schema is outdated. Missing columns: {', '.join(missing_columns)}")
            return False
        
        logger.info("✅ Database schema check passed - schema is up-to-date")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️  Database schema check failed: {e}")
        return False


def reset_database():
    """
    Delete the database file and recreate it with current schema.
    """
    try:
        from backend.config import settings
        from backend.db.init_db import init_database
        
        # Extract database file path from DATABASE_URL
        db_url = settings.DATABASE_URL
        if db_url.startswith("sqlite:///"):
            # sqlite:///./compliance.db -> ./compliance.db
            db_path = db_url.replace("sqlite:///", "")
            db_file = Path(project_root) / db_path
            
            if db_file.exists():
                logger.warning(f"🗑️  Deleting outdated database file: {db_file}")
                db_file.unlink()
                logger.warning(f"✅ Database file deleted: {db_file}")
            else:
                logger.info(f"📝 Database file does not exist: {db_file}")
        else:
            logger.warning(f"⚠️  Non-SQLite database detected: {db_url}")
            logger.warning("   Schema reset only works for SQLite databases")
            return False
        
        # Recreate database with current schema
        logger.warning("🔄 Recreating database with current schema...")
        success = init_database(drop_existing=False)  # No need to drop, file is deleted
        
        if success:
            logger.warning("✅ Database recreated successfully with current schema")
            return True
        else:
            logger.error("❌ Failed to recreate database")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to reset database: {e}", exc_info=True)
        return False


@pytest.fixture(scope="session", autouse=True)
def check_and_reset_database():
    """
    Pre-test fixture to check database schema and reset if outdated.
    Runs before all tests to ensure database schema matches current models.
    """
    logger.info("🔍 Checking database schema before tests...")
    
    schema_ok = check_database_schema()
    
    if not schema_ok:
        logger.warning("=" * 70)
        logger.warning("⚠️  OUTDATED DATABASE SCHEMA DETECTED")
        logger.warning("⚠️  Database will be reset and recreated with current schema")
        logger.warning("⚠️  All existing data will be lost!")
        logger.warning("=" * 70)
        
        reset_success = reset_database()
        
        if not reset_success:
            logger.error("❌ Failed to reset database. Tests may fail.")
            pytest.fail("Database schema is outdated and could not be reset")
    else:
        logger.info("✅ Database schema is up-to-date, no reset needed")


@pytest.fixture(scope="session", autouse=True)
def ensure_test_user(backend_server):
    """
    Ensure admin user exists before running tests.
    Skips if backend_server was skipped (for in-process tests using TestClient).
    
    Tries to login first via POST /auth/login, and if user doesn't exist,
    creates it via backend import (ensure_admin_user).
    
    Note: backend_server fixture already ensures /health returns 200 before this runs.
    """
    # Skip if backend_server was skipped (for in-process tests)
    if os.getenv("SKIP_LIVE_BACKEND") == "1":
        print("⏭️  Skipping test user creation (using in-process TestClient)")
        return
    
    # Try to login to check if user exists
    user_exists = False
    try:
        login_response = requests.post(
            f"{BASE_URL_BACKEND}/auth/login",
            data={"username": "admin", "password": "admin"},
            timeout=5
        )
        
        # If login succeeds (200), user exists - we're done
        if login_response.status_code == 200:
            user_exists = True
            print("✅ Admin user exists and login works")
    except requests.exceptions.RequestException as e:
        # Connection error or other issue - will try to create user
        print(f"⚠️  Login check failed: {e}")
    
    # If login failed (401/500), user might not exist - create it via backend import
    if not user_exists:
        try:
            from backend.db.base import get_db
            from backend.auth.user_manager import ensure_admin_user
            
            # Get database session
            db = next(get_db())
            
            try:
                # Note: ensure_admin_user() creates "demo"/"demo123" by default
                # But tests use "admin"/"admin", so we need to create that user
                from backend.auth.auth_models import User
                from backend.auth.security import hash_password
                
                # Check if admin user exists
                admin_user = db.query(User).filter(User.username == "admin").first()
                if not admin_user:
                    # Create admin user for tests (username: "admin", password: "admin")
                    admin_user = User(
                        username="admin",
                        hashed_password=hash_password("admin"),
                        is_active=True,
                    )
                    db.add(admin_user)
                    db.commit()
                    db.refresh(admin_user)
                    print("✅ Created admin user for tests (admin/admin)")
                else:
                    print("✅ Admin user already exists in database")
                
                # Also ensure demo user exists (for compatibility with default ensure_admin_user)
                ensure_admin_user(db)
                print("✅ Demo user ensured (demo/demo123)")
            finally:
                db.close()
        except Exception as e:
            # If we can't create user via import, that's OK - login endpoint will create it
            print(f"⚠️  Could not create user via import: {e}")
            print("   User will be created on first login attempt via ensure_admin_user()")
