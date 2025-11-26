"""
Environment validation script
Checks if all required dependencies and configs are present
"""

import os
import sys
from pathlib import Path


def check_env_file():
    """Check if .env file exists and has required variables"""
    print("\n1. Checking .env file...")
    
    env_path = Path(".env")
    if not env_path.exists():
        print("   ✗ .env file not found")
        print("   → Create .env file with OPENAI_API_KEY, SECRET_KEY, JWT_SECRET")
        print("   → Note: OPENAI_API_KEY is optional (system works in mock mode)")
        return False
    
    with open(env_path) as f:
        env_content = f.read()
    
    # Parse .env file
    env_vars = {}
    for line in env_content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip()
    
    required = ["SECRET_KEY", "JWT_SECRET"]
    optional = ["OPENAI_API_KEY"]
    missing = []
    empty = []
    
    # Check required variables
    for var in required:
        if var not in env_vars:
            missing.append(var)
        elif not env_vars[var] or env_vars[var] == "":
            empty.append(var)
    
    if missing:
        print(f"   ✗ Missing required variables: {', '.join(missing)}")
        return False
    
    if empty:
        print(f"   ✗ Empty required variables: {', '.join(empty)}")
        return False
    
    # Check optional variables
    if "OPENAI_API_KEY" not in env_vars or not env_vars.get("OPENAI_API_KEY"):
        print("   ⚠️  OPENAI_API_KEY not set (system will use mock mode)")
    else:
        api_key = env_vars["OPENAI_API_KEY"]
        if api_key.startswith("sk-"):
            print("   ✓ OPENAI_API_KEY is set (real LLM mode enabled)")
        else:
            print("   ⚠️  OPENAI_API_KEY format looks invalid (should start with 'sk-')")
    
    # Check for default values
    if "dev_secret_key_change_me" in env_vars.get("SECRET_KEY", ""):
        print("   ⚠️  Using default SECRET_KEY (OK for dev, change for production)")
    
    if "dev_jwt_secret_change_me" in env_vars.get("JWT_SECRET", ""):
        print("   ⚠️  Using default JWT_SECRET (OK for dev, change for production)")
    
    print("   ✓ .env file exists with required variables")
    return True


def check_dependencies():
    """Check if all required packages are installed"""
    print("\n2. Checking dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "streamlit",
        "openai",
        "sqlalchemy",
        "pydantic"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"   ✗ Missing packages: {', '.join(missing)}")
        print("   → Run: pip install -r requirements.txt")
        return False
    
    print("   ✓ All required packages installed")
    return True


def check_database():
    """Check if database file exists"""
    print("\n3. Checking database...")
    
    db_path = Path("compliance.db")
    if not db_path.exists():
        print("   ⚠️  Database file not found (will be created on first run)")
        return True
    
    print("   ✓ Database file exists")
    return True


def check_frontend_pages():
    """Check if required frontend pages exist"""
    print("\n4. Checking frontend pages...")
    
    required_pages = [
        "frontend/Home.py",
        "frontend/pages/1_Analyze_Task.py",
        "frontend/pages/3_Audit_Trail.py",
        "frontend/pages/5_Agentic_Analysis.py",
        "frontend/pages/7_Agentic_Test_Suite.py"
    ]
    
    missing = []
    for page in required_pages:
        if not Path(page).exists():
            missing.append(page)
    
    if missing:
        print(f"   ✗ Missing pages: {', '.join(missing)}")
        return False
    
    print("   ✓ All required frontend pages exist")
    return True


def check_backend_structure():
    """Check if backend structure is correct"""
    print("\n5. Checking backend structure...")
    
    required_dirs = [
        "backend/api",
        "backend/agent",
        "backend/agentic_engine",
        "backend/db",
        "backend/utils"
    ]
    
    missing = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        print(f"   ✗ Missing directories: {', '.join(missing)}")
        return False
    
    # Check for critical backend files
    required_files = [
        "backend/main.py",
        "backend/config/settings.py",
        "backend/db/models.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"   ✗ Missing critical files: {', '.join(missing_files)}")
        return False
    
    print("   ✓ Backend structure is correct")
    return True


def check_virtual_environment():
    """Check if running in virtual environment"""
    print("\n6. Checking virtual environment...")
    
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if in_venv:
        print("   ✓ Running in virtual environment")
        return True
    else:
        print("   ⚠️  Not running in virtual environment")
        print("   → Recommended: Activate venv with 'source venv/bin/activate'")
        # Don't fail, just warn
        return True


def main():
    print("=" * 70)
    print("ENVIRONMENT VALIDATION")
    print("=" * 70)
    
    checks = [
        check_env_file(),
        check_dependencies(),
        check_database(),
        check_frontend_pages(),
        check_backend_structure(),
        check_virtual_environment()
    ]
    
    print("\n" + "=" * 70)
    if all(checks):
        print("✅ ENVIRONMENT VALIDATION PASSED")
        print("=" * 70)
        print("\nYou're ready to run the demo!")
        print("Start backend: uvicorn backend.main:app --reload")
        print("Start frontend: streamlit run frontend/Home.py")
        return 0
    else:
        print("❌ ENVIRONMENT VALIDATION FAILED")
        print("=" * 70)
        print("\nFix the issues above before running the demo.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

