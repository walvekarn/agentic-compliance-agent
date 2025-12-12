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
import altair as alt

# Configure Altair for light theme
alt.themes.enable('default')  # Use default light theme

# Or configure explicitly:
def light_theme():
    return {
        'config': {
            'view': {'continuousWidth': 400, 'continuousHeight': 300},
            'background': '#ffffff',
            'title': {'color': '#1e293b'},
            'axis': {
                'labelColor': '#1e293b',
                'titleColor': '#1e293b',
                'gridColor': '#e2e8f0',
                'domainColor': '#64748b'
            },
            'legend': {
                'labelColor': '#1e293b',
                'titleColor': '#1e293b'
            }
        }
    }

alt.themes.register('light_compliance', light_theme)
alt.themes.enable('light_compliance')

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
# render_plotly_chart removed - using direct st.plotly_chart instead

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
/* Test result badges - force light theme */
.test-expected-badge, .test-actual-badge {
    background-color: #f1f5f9 !important;
    color: #1e293b !important;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 500;
    border: 1px solid #e2e8f0;
}
/* Force light theme for ALL badges in test results */
.stMarkdown span[style*="background"],
.element-container span[style*="background"] {
    background-color: #f1f5f9 !important;
    color: #1e293b !important;
    border: 1px solid #e2e8f0 !important;
}
/* Specific badge overrides */
code, .stMarkdown code {
    background-color: #f1f5f9 !important;
    color: #1e293b !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
}
/* Decision badges */
.stMarkdown strong + code,
code:contains("ESCALATE"),
code:contains("AUTONOMOUS"),
code:contains("REVIEW") {
    background-color: #f1f5f9 !important;
    color: #1e293b !important;
}
/* Detailed results table styling */
.stDataFrame, [data-testid="stDataFrame"] {
    background-color: #ffffff !important;
}
.stDataFrame td, .stDataFrame th {
    background-color: #ffffff !important;
    color: #1e293b !important;
}
/* Override any dark theme leakage */
[data-testid="stExpander"] {
    background-color: #ffffff !important;
}
[data-testid="stExpander"] summary {
    color: #1e293b !important;
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
        st.rerun()  # Rerun to show loading state immediately
    
    # Prepare request (no configuration needed - uses curated scenarios)
    request_data = {}
    
    # Show progress with 120s timeout
    try:
        with st.spinner("Running test suite... This may take a few minutes."):
            response = api_client.post("/api/v1/agentic/testSuite", request_data, timeout=120)
        
        # Parse standardized agentic response
        status, results, error, timestamp = parseAgenticResponse(response)
        
        # Clear running state before processing results
        st.session_state.test_running = False
        
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

# Show loading state if test is running but no results yet
if st.session_state.test_running and not st.session_state.test_results:
    st.info("🔄 **Test suite is running...** Please wait while tests are executed.")
    st.stop()  # Stop rendering to prevent showing empty sections

# Display results - only when results are ready and test is not running
if st.session_state.test_results and not st.session_state.test_running:
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
    
    # Get test results and build deviations
    test_results = results.get("test_results", []) if results else []
    summary = results.get("summary", {}) if results else {}
    confidence_deviations = summary.get("confidence_deviations", [])
    
    # Build deviations from test_results if not provided by backend
    if not confidence_deviations and test_results:
        confidence_deviations = []
        for i, r in enumerate(test_results):
            scenario = r.get("scenario", {})
            expected = r.get("expected", {})
            actual = r.get("actual", {})
            
            expected_min = expected.get("min_confidence", 0.5)
            actual_conf = actual.get("confidence")
            
            if actual_conf is not None:
                confidence_deviations.append({
                    "scenario": scenario.get("title", f"Test {i+1}"),
                    "expected_min": round(expected_min, 3),
                    "actual": round(actual_conf, 3),
                    "deviation": round(actual_conf - expected_min, 3),
                    "adequate": actual_conf >= expected_min
                })
    
    # Confidence Deviations Chart - Using Altair for simple bar chart
    render_section_header("Confidence Deviations", icon="📈", level=2)
    
    # Validate and process confidence_deviations data
    # Show chart if we have deviations (including when all tests pass - all deviations >= 0)
    if confidence_deviations and isinstance(confidence_deviations, list) and len(confidence_deviations) > 0:
        try:
            # Convert to DataFrame
            deviation_df = pd.DataFrame(confidence_deviations)
            
            # Validate required columns
            required_cols = ["scenario", "deviation"]
            if not all(col in deviation_df.columns for col in required_cols):
                st.error(f"❌ **Data format error**: Missing required columns. Expected: {required_cols}, Got: {list(deviation_df.columns)}")
                st.info("📊 Raw data sample: " + str(confidence_deviations[:2]))
            else:
                # Ensure deviation is numeric
                deviation_df["deviation"] = pd.to_numeric(deviation_df["deviation"], errors="coerce")
                
                # Check if all deviations are valid (not NaN)
                valid_deviations = deviation_df["deviation"].notna()
                if not valid_deviations.all():
                    st.warning(f"⚠️ Some deviation values are invalid (NaN). Valid: {valid_deviations.sum()}/{len(deviation_df)}")
                    deviation_df = deviation_df[valid_deviations]
                
                # Check if we have any data after cleaning
                if len(deviation_df) == 0:
                    st.error("❌ **Data error**: No valid deviation data after processing.")
                else:
                    # Check if all deviations are adequate (>= 0)
                    all_adequate = (deviation_df["deviation"] >= 0).all()
                    
                    # Show success message for 100% adequacy, but still display the chart
                    if all_adequate:
                        st.success("✅ **All confidence scores met or exceeded expectations!** All scenarios have confidence >= expected minimum.")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Confidence Deviations Chart**")
                        
                        # Create color condition: green if deviation >= 0, red if < 0
                        chart = alt.Chart(deviation_df).mark_bar().encode(
                            x=alt.X("scenario:N", title="Scenario", sort=None, axis=alt.Axis(labelAngle=-45 if len(deviation_df) > 5 else 0)),
                            y=alt.Y("deviation:Q", title="Deviation (Actual - Expected Min)"),
                            color=alt.condition(
                                alt.datum.deviation >= 0,
                                alt.value("#22c55e"),  # Green for adequate
                                alt.value("#ef4444")   # Red for inadequate
                            ),
                            tooltip=["scenario", "deviation"]
                        ).properties(
                            width="container",
                            height=400,
                            title="Confidence Deviations (Actual - Expected Min)"
                        )
                        
                        st.altair_chart(chart, use_container_width=True)
                    
                    with col2:
                        st.markdown("**Deviation Data Table**")
                        if not deviation_df.empty:
                            try:
                                display_cols = ["scenario", "expected_min", "actual", "deviation", "adequate"]
                                available_cols = [col for col in display_cols if col in deviation_df.columns]
                                if available_cols:
                                    st.dataframe(deviation_df[available_cols], use_container_width=True)
                                else:
                                    # Show available columns if expected ones are missing
                                    st.dataframe(deviation_df, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error creating table: {str(e)}")
                        else:
                            st.info("📊 Run the test suite to see confidence deviations.")
        
        except Exception as e:
            st.error(f"❌ **Data processing error**: {str(e)}")
            st.info("📊 Raw data sample: " + str(confidence_deviations[:3] if confidence_deviations else "None"))
    
    else:
        # No deviations data available - this should be rare since we build from test_results above
        # But handle edge case where test_results might not have confidence data
        if test_results and len(test_results) > 0:
            # Try to check if we can determine adequacy from test_results
            all_adequate = True
            has_confidence_data = False
            for r in test_results:
                actual_conf = r.get("actual", {}).get("confidence")
                expected_min = r.get("expected", {}).get("min_confidence", 0.5)
                if actual_conf is not None and expected_min is not None:
                    has_confidence_data = True
                    if actual_conf < expected_min:
                        all_adequate = False
                        break
            
            if has_confidence_data:
                if all_adequate:
                    st.success("✅ **All confidence scores met or exceeded expectations!** All scenarios have confidence >= expected minimum.")
                else:
                    st.warning("⚠️ **Some confidence scores below threshold** - but deviation data could not be generated.")
            else:
                st.info("📊 **No confidence data available** in test results. Cannot generate deviation chart.")
        else:
            st.info("📊 No test results available. Run the test suite to see confidence deviations.")
    
    # Detailed Test Results section
    test_results = results.get("test_results", []) if results else []
    
    if test_results and len(test_results) > 0:
        render_section_header("Detailed Test Results", icon="🔍", level=2)
        
        # Build results table
        results_data = []
        for r in test_results:
            scenario = r.get("scenario", {})
            expected = r.get("expected", {})
            actual = r.get("actual", {})
            
            results_data.append({
                "Scenario": scenario.get("title", "Unknown"),
                "Status": "✅ Pass" if r.get("passed", False) else "❌ Fail",
                "Decision Match": "✅" if r.get("decision_correct", False) else "❌",
                "Risk Match": "✅" if r.get("risk_level_correct", False) else "❌",
                "Confidence OK": "✅" if r.get("confidence_adequate", False) else "❌",
                "Expected Decision": expected.get("decision", "N/A"),
                "Actual Decision": actual.get("decision", "N/A"),
                "Expected Risk": expected.get("risk_level", "N/A"),
                "Actual Risk": actual.get("risk_level", "N/A"),
                "Confidence": f"{actual.get('confidence', 0):.2f}" if actual.get('confidence') is not None else "N/A"
            })
        
        if results_data:
            df = pd.DataFrame(results_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No test results to display.")
    else:
        st.info("📊 Run the test suite to see detailed results.")
else:
    # No results available and test is not running
    if not st.session_state.test_running:
        st.info("No test results available. Run the test suite to see results.")
