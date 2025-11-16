#!/usr/bin/env python3
"""
MVP Readiness Verification Script
==================================
Verify that the MVP is ready for demo and deployment.

Usage:
    python scripts/verify_mvp.py

Exit codes:
    0 - All tests passed, MVP is ready
    1 - Some tests failed, MVP needs fixes
"""

import sys
import requests
from datetime import datetime
from typing import Tuple, List


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_test(name: str, passed: bool, message: str = ""):
    """Print test result"""
    icon = f"{Colors.GREEN}✅{Colors.END}" if passed else f"{Colors.RED}❌{Colors.END}"
    status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
    print(f"{icon} {name:<40} [{status}]")
    if message:
        indent = "   "
        print(f"{indent}{Colors.YELLOW}{message}{Colors.END}")


def test_backend_health() -> Tuple[bool, str]:
    """Test backend health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            version = data.get('version', 'unknown')
            status = data.get('status', 'unknown')
            
            if status == 'healthy' and version == '0.1.0':
                return True, f"Backend healthy (v{version})"
            else:
                return False, f"Unexpected response: status={status}, version={version}"
        else:
            return False, f"Status code: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Backend not responding - is it running?"
    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except Exception as e:
        return False, f"Error: {str(e)}"


def test_backend_root() -> Tuple[bool, str]:
    """Test backend root endpoint"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'message' in data and 'version' in data:
                return True, f"Root endpoint OK (v{data['version']})"
            else:
                return False, "Missing expected fields in response"
        else:
            return False, f"Status code: {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def test_dashboard_accessible() -> Tuple[bool, str]:
    """Test dashboard is accessible"""
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            return True, "Dashboard is running"
        else:
            return False, f"Status code: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Dashboard not responding - is it running?"
    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except Exception as e:
        return False, f"Error: {str(e)}"


def test_decision_api() -> Tuple[bool, str]:
    """Test decision analysis API endpoint"""
    try:
        payload = {
            "entity": {
                "name": "Test Corp",
                "entity_type": "STARTUP",
                "industry": "TECHNOLOGY",
                "jurisdictions": ["US_FEDERAL"],
                "employee_count": 10,
                "has_personal_data": False,
                "is_regulated": False,
                "previous_violations": 0
            },
            "task": {
                "description": "MVP verification test task",
                "category": "GENERAL_INQUIRY",
                "affects_personal_data": False,
                "affects_financial_data": False,
                "involves_cross_border": False,
                "requires_external_approval": False,
                "potential_impact": "Low"
            }
        }
        
        response = requests.post(
            "http://localhost:8000/api/v1/decision/analyze",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check for required fields
            required_fields = ['decision', 'risk_level', 'confidence', 'risk_score']
            missing = [f for f in required_fields if f not in result]
            
            if missing:
                return False, f"Missing fields: {', '.join(missing)}"
            
            decision = result['decision']
            confidence = result['confidence']
            
            return True, f"Decision API works (decision={decision}, confidence={confidence:.0%})"
        else:
            return False, f"Status code: {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "Request timed out - AI processing may be slow"
    except Exception as e:
        return False, f"Error: {str(e)}"


def test_audit_api() -> Tuple[bool, str]:
    """Test audit trail API endpoint"""
    try:
        response = requests.get(
            "http://localhost:8000/api/v1/audit/entries?limit=5",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('total', 0)
            return True, f"Audit API works ({count} entries)"
        else:
            return False, f"Status code: {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def test_audit_statistics() -> Tuple[bool, str]:
    """Test audit statistics endpoint"""
    try:
        response = requests.get(
            "http://localhost:8000/api/v1/audit/statistics",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_decisions', 0)
            return True, f"Statistics API works ({total} total decisions)"
        else:
            return False, f"Status code: {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def run_all_tests() -> List[Tuple[str, bool, str]]:
    """Run all verification tests"""
    tests = [
        ("Backend Health Check", test_backend_health),
        ("Backend Root Endpoint", test_backend_root),
        ("Dashboard Accessibility", test_dashboard_accessible),
        ("Decision Analysis API", test_decision_api),
        ("Audit Trail API", test_audit_api),
        ("Audit Statistics API", test_audit_statistics),
    ]
    
    results = []
    for name, test_func in tests:
        passed, message = test_func()
        results.append((name, passed, message))
        print_test(name, passed, message)
    
    return results


def print_summary(results: List[Tuple[str, bool, str]]):
    """Print test summary"""
    total = len(results)
    passed = sum(1 for _, p, _ in results if p)
    failed = total - passed
    
    print_header("TEST SUMMARY")
    
    print(f"Total Tests:   {total}")
    print(f"{Colors.GREEN}Passed:        {passed}{Colors.END}")
    
    if failed > 0:
        print(f"{Colors.RED}Failed:        {failed}{Colors.END}")
    else:
        print(f"Failed:        {failed}")
    
    print(f"\nSuccess Rate:  {passed}/{total} ({passed*100//total}%)")
    
    print()
    
    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ MVP IS READY!{Colors.END}")
        print()
        print(f"{Colors.GREEN}🎉 Next steps:{Colors.END}")
        print("  1. Take screenshots of the dashboard")
        print("  2. Record a demo video")
        print("  3. Document any manual testing")
        print("  4. Push to GitHub")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ MVP NOT READY - Fix failing tests{Colors.END}")
        print()
        print(f"{Colors.YELLOW}Failed tests:{Colors.END}")
        for name, passed, message in results:
            if not passed:
                print(f"  • {name}")
                if message:
                    print(f"    └─ {message}")
        print()
        print(f"{Colors.YELLOW}💡 Troubleshooting:{Colors.END}")
        print("  • Ensure backend is running: make start")
        print("  • Ensure dashboard is running: cd dashboard && streamlit run Home.py")
        print("  • Check logs: tail -f backend.log")
        print("  • Restart everything: make restart")
        return 1


def main():
    """Main entry point"""
    print_header("MVP READINESS VERIFICATION")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("Running verification tests...\n")
    
    results = run_all_tests()
    exit_code = print_summary(results)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

