#!/usr/bin/env python3
"""
Test script for all 4 agentic API endpoints
Usage: python scripts/test_agentic_endpoints.py
"""

import os
import sys
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
ENDPOINTS_BASE = "/api/v1/agentic"
TIMEOUT = 125  # 120s + 5s buffer


def test_endpoint(
    name: str,
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None
) -> bool:
    """Test a single endpoint and validate response format"""
    print(f"\n{'='*80}")
    print(f"🧪 Testing: {name}")
    print(f"  Method: {method}")
    print(f"  Endpoint: {endpoint}")
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        else:
            response = requests.post(
                url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=TIMEOUT
            )
        
        print(f"  HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"  ❌ Failed with status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
        
        try:
            result = response.json()
        except json.JSONDecodeError:
            print(f"  ❌ Invalid JSON response")
            return False
        
        # Validate standardized format
        required_fields = ["status", "results", "error", "timestamp"]
        missing_fields = [f for f in required_fields if f not in result]
        
        if missing_fields:
            print(f"  ❌ Missing required fields: {missing_fields}")
            return False
        
        # Validate status value
        valid_statuses = ["completed", "running", "timeout", "error"]
        if result["status"] not in valid_statuses:
            print(f"  ⚠️  Status '{result['status']}' not in expected values: {valid_statuses}")
        
        # Validate timestamp format
        try:
            datetime.fromisoformat(result["timestamp"].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            print(f"  ⚠️  Invalid timestamp format: {result['timestamp']}")
        
        print(f"  ✅ Response format valid")
        print(f"  Status: {result['status']}")
        print(f"  Timestamp: {result['timestamp']}")
        
        if result["status"] == "completed" and result["results"]:
            print(f"  ✅ Results present: {type(result['results']).__name__}")
            if isinstance(result["results"], dict):
                print(f"  Results keys: {list(result['results'].keys())[:5]}...")
        elif result["status"] == "error":
            print(f"  ⚠️  Error: {result.get('error', 'Unknown error')}")
        
        print(f"  Response preview (first 300 chars):")
        print(f"  {json.dumps(result, indent=2)[:300]}...")
        
        return True
        
    except requests.exceptions.Timeout:
        print(f"  ❌ Request timed out after {TIMEOUT} seconds")
        return False
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Connection error - is the backend running at {BASE_URL}?")
        print(f"  Start backend with: make backend")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {str(e)}")
        return False


def main():
    """Run all endpoint tests"""
    print("\n" + "="*80)
    print("🧪 AGENTIC API ENDPOINT TESTS")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = []
    
    # Test 1: Status endpoint
    results.append((
        "Status",
        test_endpoint("Status", "GET", f"{ENDPOINTS_BASE}/status")
    ))
    
    # Test 2: Test Suite endpoint (with minimal data for speed)
    test_suite_data = {
        "num_random": 2,
        "max_iterations": 3,
        "complexity_distribution": {"low": 1, "medium": 1}
    }
    results.append((
        "Test Suite",
        test_endpoint("Test Suite", "POST", f"{ENDPOINTS_BASE}/testSuite", test_suite_data)
    ))
    
    # Test 3: Benchmarks endpoint
    benchmark_data = {
        "levels": ["light"],
        "max_cases_per_level": 2,
        "max_iterations": 3
    }
    results.append((
        "Benchmarks",
        test_endpoint("Benchmarks", "POST", f"{ENDPOINTS_BASE}/benchmarks", benchmark_data)
    ))
    
    # Test 4: Recovery endpoint
    recovery_data = {
        "task": "Test recovery simulation",
        "failure_type": "tool_timeout",
        "failure_rate": 0.5,
        "max_iterations": 3
    }
    results.append((
        "Recovery",
        test_endpoint("Recovery", "POST", f"{ENDPOINTS_BASE}/recovery", recovery_data)
    ))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        print("\nTroubleshooting:")
        print("  1. Ensure backend is running: make backend")
        print("  2. Check OPENAI_API_KEY is set in .env")
        print("  3. Check backend logs for errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())

