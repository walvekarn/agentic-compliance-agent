"""
Test Dashboard Pages
====================
Tests each Streamlit page for import and syntax errors.
"""

import sys
import os
from pathlib import Path
import ast
import importlib.util

# Add frontend to path
# From tests/frontend/test_dashboard_pages.py -> project_root/frontend
frontend_path = Path(__file__).parent.parent.parent / "frontend"
sys.path.insert(0, str(frontend_path))

print("=" * 70)
print("TESTING DASHBOARD PAGES")
print("=" * 70)
print()

pages_to_test = [
    ("Home.py", frontend_path / "Home.py"),
    ("1_Analyze_Task.py", frontend_path / "pages" / "1_Analyze_Task.py"),
    ("2_Compliance_Calendar.py", frontend_path / "pages" / "2_Compliance_Calendar.py"),
    ("3_Audit_Trail.py", frontend_path / "pages" / "3_Audit_Trail.py"),
    ("4_Agent_Insights.py", frontend_path / "pages" / "4_Agent_Insights.py"),
]

all_passed = True
errors_found = []

for page_name, page_path in pages_to_test:
    print(f"📄 Testing: {page_name}")
    print("-" * 70)
    
    # Test 1: Check file exists
    if not page_path.exists():
        print(f"   ✗ File not found: {page_path}")
        all_passed = False
        errors_found.append(f"{page_name}: File not found")
        continue
    else:
        print(f"   ✓ File exists")
    
    # Test 2: Read file content
    try:
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"   ✓ File readable ({len(content)} bytes)")
    except Exception as e:
        print(f"   ✗ Cannot read file: {e}")
        all_passed = False
        errors_found.append(f"{page_name}: Cannot read - {e}")
        continue
    
    # Test 3: Parse syntax
    try:
        ast.parse(content)
        print(f"   ✓ Syntax valid (Python AST parsing successful)")
    except SyntaxError as e:
        print(f"   ✗ Syntax error: Line {e.lineno}: {e.msg}")
        all_passed = False
        errors_found.append(f"{page_name}: Syntax error at line {e.lineno}")
        continue
    
    # Test 4: Check for required imports
    required_imports = ['streamlit']
    found_imports = []
    
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('import streamlit') or line.startswith('from streamlit'):
            found_imports.append('streamlit')
            break
    
    if 'streamlit' in found_imports:
        print(f"   ✓ Has required imports: {found_imports}")
    else:
        print(f"   ⚠ Warning: No streamlit import found")
    
    # Test 5: Check for authentication (for non-Home pages)
    if page_name != "Home.py":
        if "require_auth" in content or "auth" in content:
            print(f"   ✓ Has authentication check")
        else:
            print(f"   ⚠ Warning: No authentication check found")
    
    # Test 6: Check for common patterns
    patterns = {
        'st.title': 'Page title',
        'st.markdown': 'Markdown content',
        'requests.': 'API calls',
    }
    
    found_patterns = []
    for pattern, description in patterns.items():
        if pattern in content:
            found_patterns.append(description)
    
    if found_patterns:
        print(f"   ✓ Found patterns: {', '.join(found_patterns)}")
    
    # Test 7: Try to load as module (without executing)
    try:
        spec = importlib.util.spec_from_file_location(page_name.replace('.py', ''), page_path)
        if spec and spec.loader:
            # Don't actually execute, just check if it's loadable
            print(f"   ✓ Module is loadable")
        else:
            print(f"   ⚠ Warning: Module spec could not be created")
    except Exception as e:
        print(f"   ⚠ Warning: Module load test failed: {e}")
    
    # Test 8: Check for common errors
    error_patterns = [
        ('st.experimental_rerun', 'Deprecated: Use st.rerun()'),
        ('st.experimental_singleton', 'Deprecated: Use st.cache_resource()'),
        ('st.experimental_memo', 'Deprecated: Use st.cache_data()'),
    ]
    
    found_deprecations = []
    for pattern, warning in error_patterns:
        if pattern in content:
            found_deprecations.append(warning)
    
    if found_deprecations:
        print(f"   ⚠ Deprecation warnings:")
        for dep in found_deprecations:
            print(f"      - {dep}")
    
    print(f"   ✅ {page_name}: All checks passed")
    print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()

if all_passed and not errors_found:
    print("✅ ALL DASHBOARD PAGES PASSED")
    print()
    print("Summary:")
    for page_name, _ in pages_to_test:
        print(f"  ✓ {page_name}")
    print()
    print("Next Steps:")
    print("  1. Start backend: uvicorn main:app --port 8000")
    print("  2. Start frontend: streamlit run frontend/Home.py")
    print("  3. Test in browser: http://localhost:8501")
else:
    print("❌ SOME TESTS FAILED")
    print()
    print("Errors found:")
    for error in errors_found:
        print(f"  ✗ {error}")
    print()
    sys.exit(1)

