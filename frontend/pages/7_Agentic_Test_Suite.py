"""
Agentic Test Suite
==================
Run curated test scenarios and compare actual vs expected results.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# Force light theme for all Plotly charts
pio.templates.default = "plotly_white"

# Add frontend directory to path
frontend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(frontend_dir))

from components.auth_utils import require_auth, show_logout_button
from components.session_manager import SessionManager
from components.api_client import APIClient, display_api_error, parseAgenticResponse
from components.ui_helpers import render_plotly_chart

# Page config
st.set_page_config(page_title="Agentic Test Suite", page_icon="🧪", layout="wide")

# Apply light theme CSS
from components.ui_helpers import apply_light_theme_css
apply_light_theme_css()

# Authentication
require_auth()

# Show logout button in header
col1, col2 = st.columns([5, 1])
with col2:
    show_logout_button()

# Initialize session
SessionManager.init()

# Initialize API client
api_client = APIClient()

# Custom CSS
st.markdown("""
<style>
.test-suite-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
}
.metric-card {
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}
.success-badge {
    background-color: #28a745;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
}
.failure-badge {
    background-color: #dc3545;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
}
</style>
""", unsafe_allow_html=True)

# Header
from components.ui_helpers import render_page_header
render_page_header(
    title="Agentic Test Suite",
    icon="🧪",
    description="Run curated test scenarios and compare actual vs expected results"
)

# Session state
if "test_results" not in st.session_state:
    st.session_state.test_results = None
if "test_running" not in st.session_state:
    st.session_state.test_running = False

# Information about curated scenarios
st.info("""
📋 **About This Test Suite**: This test suite runs curated scenarios from `/test_scenarios/*.json` files.
Each scenario includes expected decision, risk level, and minimum confidence. Results are compared
against expectations to measure accuracy and confidence alignment.
""")

# Run test suite button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_button = st.button("🚀 Run Test Suite", type="primary", width="stretch")

if run_button or st.session_state.test_running:
    if not st.session_state.test_running:
        st.session_state.test_running = True
        st.session_state.test_results = None
    
    # Prepare request (no configuration needed - uses curated scenarios)
    request_data = {}
    
    # Show progress with 120s timeout
    try:
        with st.spinner("Running test suite... This may take a few minutes."):
            response = api_client.post("/api/v1/agentic/testSuite", request_data, timeout=120)
        
        st.session_state.test_running = False
        
        # Parse standardized agentic response
        status, results, error, timestamp = parseAgenticResponse(response)
        
        if status == "completed" and results:
            st.session_state.test_results = results
            st.success(f"✅ Test suite completed! (Completed at {timestamp or 'unknown'})")
        elif status == "timeout":
            st.error(f"⏱️ **Timeout**: {error or 'Test suite timed out after 120 seconds'}")
            st.session_state.test_results = None
        elif status == "error":
            st.error(f"❌ **Error**: {error or 'Unknown error occurred'}")
            st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify test scenarios exist in /test_scenarios/\n3. Check backend logs for details")
            st.session_state.test_results = None
        else:
            display_api_error(response)
            st.session_state.test_results = None
    except Exception as e:
        st.session_state.test_running = False
        st.error(f"❌ **API Error**: {str(e)}")
        st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify your network connection\n3. Try again in a few moments")
        st.session_state.test_results = None

# Display results
if st.session_state.test_results:
    results = st.session_state.test_results
    summary = results.get("summary", {}) if isinstance(results, dict) else {}
    
    # Summary metrics
    from components.ui_helpers import render_section_header
    render_section_header("Test Suite Summary", icon="📊", level=2)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_tests = summary.get("total_tests", 0)
        st.metric("Total Tests", total_tests if total_tests > 0 else "N/A")
    
    with col2:
        pass_rate = summary.get("pass_rate", 0)
        if pass_rate > 0:
            st.metric("Pass Rate", f"{pass_rate:.1%}", 
                     delta=f"{summary.get('passed_tests', 0)}/{total_tests} passed")
        else:
            st.metric("Pass Rate", "N/A")
    
    with col3:
        decision_accuracy = summary.get("decision_accuracy", 0)
        if decision_accuracy > 0:
            st.metric("Decision Accuracy", f"{decision_accuracy:.1%}")
        else:
            st.metric("Decision Accuracy", "N/A")
    
    with col4:
        risk_accuracy = summary.get("risk_level_accuracy", 0)
        if risk_accuracy > 0:
            st.metric("Risk Level Accuracy", f"{risk_accuracy:.1%}")
        else:
            st.metric("Risk Level Accuracy", "N/A")
    
    with col5:
        confidence_adequacy = summary.get("confidence_adequacy", 0)
        if confidence_adequacy > 0:
            st.metric("Confidence Adequacy", f"{confidence_adequacy:.1%}")
        else:
            st.metric("Confidence Adequacy", "N/A")
    
    # Failures section
    failures = summary.get("failures", [])
    if failures:
        render_section_header("Test Failures", icon="❌", level=2)
        
        for failure in failures:
            scenario_name = failure.get("scenario", "Unknown")
            diff = failure.get("diff", {})
            error = failure.get("error")
            
            with st.expander(f"❌ {scenario_name}", expanded=True):
                if error:
                    st.error(f"**Error**: {error}")
                
                if diff:
                    st.markdown("### Differences")
                    
                    if "decision" in diff:
                        d = diff["decision"]
                        st.warning(f"**Decision Mismatch**: Expected `{d.get('expected')}`, got `{d.get('actual')}`")
                    
                    if "risk_level" in diff:
                        r = diff["risk_level"]
                        st.warning(f"**Risk Level Mismatch**: Expected `{r.get('expected')}`, got `{r.get('actual')}`")
                    
                    if "confidence" in diff:
                        c = diff["confidence"]
                        deviation = c.get("deviation", 0)
                        st.warning(f"**Confidence Below Threshold**: Expected min `{c.get('expected_min'):.2f}`, got `{c.get('actual'):.2f}` (deviation: {deviation:+.2f})")
    
    # Confidence deviations
    confidence_deviations = summary.get("confidence_deviations", [])
    # Fallback: if there are test_results but no deviations, build a flat-zero chart so the UI is not blank
    if (not confidence_deviations) and test_results:
        fallback_devs = []
        for r in test_results:
            scenario = r.get("scenario", {})
            title = scenario.get("title", "Scenario")
            expected_min = r.get("expected", {}).get("min_confidence", 0.0)
            actual_conf = r.get("actual", {}).get("confidence", expected_min)
            fallback_devs.append({
                "scenario": title,
                "expected_min": expected_min,
                "actual": actual_conf,
                "deviation": actual_conf - expected_min if actual_conf is not None else 0.0,
                "adequate": (actual_conf or 0.0) >= expected_min
            })
        confidence_deviations = fallback_devs

    if confidence_deviations:
        render_section_header("Confidence Deviations", icon="📈", level=2)
        
        deviation_df = pd.DataFrame(confidence_deviations)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Deviation chart
            if not deviation_df.empty:
                fig = px.bar(
                    deviation_df,
                    x="scenario",
                    y="deviation",
                    color="adequate",
                    color_discrete_map={True: "#28a745", False: "#dc3545"},
                    labels={"deviation": "Deviation", "scenario": "Scenario"}
                )
                render_plotly_chart(fig, title="Confidence Deviations (Actual - Expected Min)", height=400, show_title=True)
        
        with col2:
            # Deviation table
            st.dataframe(
                deviation_df[["scenario", "expected_min", "actual", "deviation", "adequate"]],
                width="stretch"
            )
    
    # Detailed results table
    render_section_header("Detailed Test Results", icon="🔍", level=2)
    
    test_results = results.get("test_results", [])
    if test_results:
        results_data = []
        for r in test_results:
            scenario = r.get("scenario", {})
            results_data.append({
                "Scenario": scenario.get("title", "Unknown"),
                "Status": "✅ Pass" if r.get("passed") else "❌ Fail",
                "Decision": "✅" if r.get("decision_correct") else "❌",
                "Risk Level": "✅" if r.get("risk_level_correct") else "❌",
                "Confidence": "✅" if r.get("confidence_adequate") else "❌",
                "Expected Decision": r.get("expected", {}).get("decision", "N/A"),
                "Actual Decision": r.get("actual", {}).get("decision", "N/A"),
                "Expected Risk": r.get("expected", {}).get("risk_level", "N/A"),
                "Actual Risk": r.get("actual", {}).get("risk_level", "N/A"),
                "Expected Min Conf": f"{r.get('expected', {}).get('min_confidence', 0):.2f}",
                "Actual Conf": f"{r.get('actual', {}).get('confidence', 0):.2f}" if r.get('actual', {}).get('confidence') is not None else "N/A",
                "Execution Time (s)": f"{r.get('execution_time', 0):.2f}"
            })
        
        df = pd.DataFrame(results_data)
        st.dataframe(df, width="stretch")
        
        # Expandable details for each test
        for i, result in enumerate(test_results):
            scenario = result.get("scenario", {})
            scenario_name = scenario.get("title", f"Test {i+1}")
            
            with st.expander(f"{'✅' if result.get('passed') else '❌'} {scenario_name}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Expected:**")
                    expected = result.get("expected", {})
                    st.write(f"- Decision: `{expected.get('decision', 'N/A')}`")
                    st.write(f"- Risk Level: `{expected.get('risk_level', 'N/A')}`")
                    st.write(f"- Min Confidence: `{expected.get('min_confidence', 0):.2f}`")
                
                with col2:
                    st.markdown("**Actual:**")
                    actual = result.get("actual", {})
                    st.write(f"- Decision: `{actual.get('decision', 'N/A')}`")
                    st.write(f"- Risk Level: `{actual.get('risk_level', 'N/A')}`")
                    st.write(f"- Confidence: `{actual.get('confidence', 'N/A')}`")
                
                diff = result.get("diff", {})
                if diff:
                    st.markdown("**Differences:**")
                    st.json(diff)
                
                if result.get("error"):
                    st.error(f"**Error**: {result.get('error')}")
else:
    st.info("No test results available.")
