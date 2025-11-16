"""
Regression Test Page
====================
Internal test runner for validating all endpoints and UI components.
Access via: /debug/regression
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import requests
import json

# Add dashboard directory to path
dashboard_dir = Path(__file__).parent.parent
sys.path.insert(0, str(dashboard_dir))

from components.auth_utils import require_auth
from components.api_client import APIClient
from components.ui_helpers import multiselect_with_select_all

# Page config
st.set_page_config(page_title="Regression Tests", page_icon="🧪", layout="wide")

# Authentication
require_auth()

# Initialize API client
api_client = APIClient()

st.title("🧪 Regression Test Suite")
st.markdown("Internal test runner for validating endpoints and UI components.")

# Test results storage
if "test_results" not in st.session_state:
    st.session_state.test_results = {}

# ============================================================================
# ENDPOINT TESTS
# ============================================================================

st.markdown("## 📡 Endpoint Tests")

def test_endpoint(name, method, endpoint, payload=None, expected_status=200):
    """Test a single endpoint"""
    try:
        if method == "GET":
            response = api_client.get(endpoint)
        else:
            response = api_client.post(endpoint, payload or {}, timeout=120)
        
        result = {
            "name": name,
            "method": method,
            "endpoint": endpoint,
            "success": response.success and response.status_code == expected_status,
            "status_code": response.status_code,
            "has_standard_format": False,
            "has_status": False,
            "has_results": False,
            "has_timestamp": False,
            "has_error": False,
            "error": None
        }
        
        if response.success and response.data:
            data = response.data
            # Check standardized format
            result["has_standard_format"] = isinstance(data, dict)
            result["has_status"] = "status" in data
            result["has_results"] = "results" in data
            result["has_timestamp"] = "timestamp" in data
            result["has_error"] = "error" in data
            
            # Validate status values (standardized: completed, timeout, error)
            if result["has_status"]:
                valid_statuses = ["completed", "timeout", "error"]
                result["valid_status"] = data["status"] in valid_statuses
                result["status_value"] = data["status"]
            else:
                result["valid_status"] = False
                result["status_value"] = None
            
            # Validate timestamp format (ISO format)
            if result["has_timestamp"]:
                try:
                    from datetime import datetime
                    datetime.fromisoformat(data["timestamp"])
                    result["valid_timestamp"] = True
                except (ValueError, TypeError):
                    result["valid_timestamp"] = False
            else:
                result["valid_timestamp"] = False
        
        return result
    except Exception as e:
        return {
            "name": name,
            "method": method,
            "endpoint": endpoint,
            "success": False,
            "error": str(e)
        }

# Test all endpoints
test_col1, test_col2 = st.columns(2)

with test_col1:
    if st.button("🧪 Run Endpoint Tests", type="primary"):
        with st.spinner("Running endpoint tests..."):
            # Test 1: Status
            st.session_state.test_results["status"] = test_endpoint(
                "Status", "GET", "/api/v1/agentic/status"
            )
            
            # Test 2: Test Suite (minimal)
            st.session_state.test_results["testSuite"] = test_endpoint(
                "Test Suite", "POST", "/api/v1/agentic/testSuite",
                {"num_random": 1, "max_iterations": 2}
            )
            
            # Test 3: Benchmarks (minimal)
            st.session_state.test_results["benchmarks"] = test_endpoint(
                "Benchmarks", "POST", "/api/v1/agentic/benchmarks",
                {"levels": ["light"], "max_cases_per_level": 1, "max_iterations": 2}
            )
            
            # Test 4: Recovery (minimal)
            st.session_state.test_results["recovery"] = test_endpoint(
                "Recovery", "POST", "/api/v1/agentic/recovery",
                {"task": "Test", "failure_type": "tool_timeout", "max_iterations": 2}
            )
        
        st.success("✅ Endpoint tests completed!")

# Display endpoint test results
if st.session_state.test_results:
    st.markdown("### Endpoint Test Results")
    
    for test_name, result in st.session_state.test_results.items():
        with st.expander(f"{result['name']} - {'✅ PASS' if result.get('success') else '❌ FAIL'}"):
            st.json(result)
            
            if result.get("success"):
                if result.get("has_standard_format"):
                    st.success("✓ Standardized format present")
                    checks = [
                        ("status", result.get("has_status")),
                        ("results", result.get("has_results")),
                        ("timestamp", result.get("has_timestamp")),
                        ("error", result.get("has_error"))
                    ]
                    for field, present in checks:
                        if present:
                            st.success(f"✓ Has '{field}' field")
                        else:
                            st.error(f"✗ Missing '{field}' field")
                else:
                    st.warning("⚠️ Response not in standardized format")

# ============================================================================
# UI COMPONENT TESTS
# ============================================================================

st.markdown("## 🎨 UI Component Tests")

# Test 1: Multiselect with Select All
st.markdown("### Multiselect with Select All")
test_options = ["Option 1", "Option 2", "Option 3", "Option 4"]
test_selection = multiselect_with_select_all(
    "Test Multiselect",
    options=test_options,
    key="test_multiselect",
    help="Test multiselect with Select All functionality"
)
st.info(f"Selected: {test_selection}")

# Test 2: Date Picker (always enabled)
st.markdown("### Date Picker (Always Enabled)")
test_date = st.date_input(
    "Test Date Picker",
    value=datetime.now().date(),
    min_value=datetime.now().date(),
    disabled=False,
    key="test_date_picker",
    help="Date picker should always be enabled (never disabled)"
)
st.info(f"Selected date: {test_date}")

# Test 3: Validation Error Clearing
st.markdown("### Validation Error Clearing")
if "test_validation_error" not in st.session_state:
    st.session_state.test_validation_error = False

if st.button("Trigger Test Error"):
    st.session_state.test_validation_error = True

if st.session_state.test_validation_error:
    st.error("⚠️ **Test Error**: This error should clear on next submit")
    
if st.button("Clear Error (Simulates successful submit)"):
    st.session_state.test_validation_error = False
    st.success("✅ Error cleared!")
    st.rerun()

# ============================================================================
# PAGINATION TEST
# ============================================================================

st.markdown("## 📄 Pagination Test")

try:
    response = api_client.get("/api/v1/audit/entries", params={"limit": 25, "offset": 0})
    if response.success and response.data:
        data = response.data
        total_count = data.get("total_count", 0)
        total_returned = data.get("total_returned", 0)
        
        st.info(f"**Pagination Test**: Showing {total_returned} of {total_count} records")
        
        if total_count > 0:
            st.success(f"✓ total_count is valid: {total_count}")
        else:
            st.warning("⚠️ total_count is 0 - may indicate no data or pagination issue")
        
        if total_returned <= total_count:
            st.success("✓ total_returned ≤ total_count (valid)")
        else:
            st.error("✗ total_returned > total_count (invalid)")
    else:
        st.error("❌ Failed to fetch audit entries")
except Exception as e:
    st.error(f"❌ Pagination test failed: {str(e)}")

# ============================================================================
# DATA CONSISTENCY TEST
# ============================================================================

st.markdown("## 🔄 Data Consistency Test")

consistency_col1, consistency_col2 = st.columns(2)

with consistency_col1:
    if st.button("Test Calendar vs Home Task Counts"):
        # Get calendar stats
        try:
            # This would require creating a test entity
            st.info("Calendar stats: Would fetch from /api/v1/entity/analyze")
            st.caption("Note: Calendar uses frontend priority calculation (days + risk)")
        except Exception as e:
            st.error(f"Error: {str(e)}")

with consistency_col2:
    if st.button("Test Audit Stats"):
        try:
            response = api_client.get("/api/v1/audit/statistics")
            if response.success:
                stats = response.data
                st.info(f"High Risk Count: {stats.get('high_risk_count', 'N/A')}")
                st.caption("Note: Audit stats use risk level only (not deadlines)")
                if stats.get("last_updated"):
                    st.caption(f"Last Updated: {stats.get('last_updated')}")
            else:
                st.error("Failed to fetch audit statistics")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ============================================================================
# SUMMARY
# ============================================================================

st.markdown("---")
st.markdown("## 📊 Test Summary")

if st.session_state.test_results:
    passed = sum(1 for r in st.session_state.test_results.values() if r.get("success"))
    total = len(st.session_state.test_results)
    
    st.metric("Tests Passed", f"{passed}/{total}")
    
    if passed == total:
        st.success("✅ All endpoint tests passed!")
    else:
        st.warning(f"⚠️ {total - passed} test(s) failed")

st.info("💡 **Note**: This is an internal test page. Use it to validate system functionality before deployment.")

