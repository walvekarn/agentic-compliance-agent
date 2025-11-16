"""
Verify project is ready for GitHub.

Run: python scripts/verify_setup.py

This script checks for:
- No hardcoded secrets
- All required files present
- Documentation completeness
- Proper .gitignore configuration
"""

import os
import sys
from pathlib import Path


def check_secrets():
    """Check for hardcoded secrets."""
    print("🔍 Checking for secrets...")
    
    issues = []
    
    # Check .env doesn't exist in git (should be ignored)
    if os.path.exists('.env'):
        # Check if it's in .gitignore
        try:
            result = os.popen('git check-ignore .env').read().strip()
            if result:
                print("✅ .env exists locally but is properly ignored")
            else:
                issues.append("❌ .env exists and is NOT ignored in .gitignore!")
        except Exception:
            # Git might not be initialized yet, that's okay
            print("⚠️  .env exists locally (ensure it's in .gitignore)")
    else:
        print("✅ .env file not found (good - will be created from .env.example)")
    
    # Check for API keys in code (excluding test files and examples)
    print("  Checking for API keys in source code...")
    try:
        api_key_check = os.popen('grep -r "sk-proj-[a-zA-Z0-9]" --exclude-dir=venv --exclude-dir=.git --exclude-dir=__pycache__ --exclude="*.md" --exclude=".env.example" . 2>/dev/null').read()
        if api_key_check:
            # Check if it's just placeholder
            if 'sk-proj-your-key' not in api_key_check and 'sk-proj-your-actual-key' not in api_key_check:
                issues.append("❌ Possible API key found in code!")
                print(f"   Found: {api_key_check[:100]}...")
            else:
                print("✅ Only placeholder API keys found in documentation")
        else:
            print("✅ No API keys found in source code")
    except Exception as e:
        print(f"⚠️  Could not check for API keys: {e}")
    
    # Check for secrets in config
    print("  Checking configuration files...")
    if os.path.exists('src/config.py'):
        with open('src/config.py', 'r') as f:
            content = f.read()
            if 'sk-' in content and 'sk-proj-your' not in content:
                issues.append("❌ Possible API key in config.py!")
            else:
                print("✅ Configuration file uses environment variables")
    
    return issues


def check_required_files():
    """Check all required files exist."""
    print("\n📄 Checking required files...")
    
    required = [
        'README.md',
        'QUICKSTART.md',
        'LICENSE',
        'CONTRIBUTING.md',
        'CHANGELOG.md',
        '.gitignore',
        '.env.example',
        'requirements.txt',
        'dashboard/requirements.txt'
    ]
    
    missing = []
    for file in required:
        if not os.path.exists(file):
            missing.append(file)
        else:
            print(f"  ✅ {file}")
    
    if missing:
        return [f"❌ Missing file: {f}" for f in missing]
    
    print("✅ All required files present")
    return []


def check_documentation():
    """Check documentation completeness."""
    print("\n📚 Checking documentation...")
    
    docs_files = [
        'docs/ARCHITECTURE.md',
        'docs/API_REFERENCE.md',
        'docs/TESTING.md'
    ]
    
    missing = []
    for file in docs_files:
        if not os.path.exists(file):
            missing.append(file)
        else:
            print(f"  ✅ {file}")
    
    if missing:
        return [f"⚠️  Missing doc: {f}" for f in missing]
    
    print("✅ Documentation complete")
    return []


def check_github_files():
    """Check GitHub-specific files."""
    print("\n🔧 Checking GitHub files...")
    
    github_files = [
        '.github/workflows/tests.yml',
        '.github/ISSUE_TEMPLATE.md',
        '.github/PULL_REQUEST_TEMPLATE.md'
    ]
    
    missing = []
    for file in github_files:
        if not os.path.exists(file):
            missing.append(file)
        else:
            print(f"  ✅ {file}")
    
    if missing:
        return [f"⚠️  Missing GitHub file: {f}" for f in missing]
    
    print("✅ GitHub files present")
    return []


def check_gitignore():
    """Check .gitignore configuration."""
    print("\n🚫 Checking .gitignore...")
    
    if not os.path.exists('.gitignore'):
        return ["❌ .gitignore file missing!"]
    
    with open('.gitignore', 'r') as f:
        content = f.read()
    
    required_patterns = [
        '.env',
        '*.db',
        '*.log',
        '__pycache__',
        'venv'
    ]
    
    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)
        else:
            print(f"  ✅ {pattern} is ignored")
    
    if missing_patterns:
        return [f"⚠️  .gitignore missing pattern: {p}" for p in missing_patterns]
    
    print("✅ .gitignore properly configured")
    return []


def check_scripts():
    """Check scripts directory."""
    print("\n📜 Checking scripts...")
    
    scripts = [
        'scripts/create_sample_data.py',
        'scripts/setup_database.py'
    ]
    
    missing = []
    for script in scripts:
        if not os.path.exists(script):
            missing.append(script)
        else:
            print(f"  ✅ {script}")
    
    if missing:
        return [f"⚠️  Missing script: {s}" for s in missing]
    
    print("✅ Scripts present")
    return []


def main():
    print("="*60)
    print("GitHub Launch Verification")
    print("="*60 + "\n")
    
    all_issues = []
    all_issues.extend(check_secrets())
    all_issues.extend(check_required_files())
    all_issues.extend(check_documentation())
    all_issues.extend(check_github_files())
    all_issues.extend(check_gitignore())
    all_issues.extend(check_scripts())
    
    print("\n" + "="*60)
    if all_issues:
        print("❌ ISSUES FOUND:")
        for issue in all_issues:
            print(f"  {issue}")
        print("\n⚠️  Fix these before pushing to GitHub!")
        print("="*60)
        sys.exit(1)
    else:
        print("✅ PROJECT IS READY FOR GITHUB!")
        print("="*60)
        print("\nNext steps:")
        print("1. Review changes: git status")
        print("2. Add files: git add .")
        print("3. Commit: git commit -m 'Prepare for GitHub launch'")
        print("4. Push: git push origin main")
        sys.exit(0)


if __name__ == "__main__":
    main()

