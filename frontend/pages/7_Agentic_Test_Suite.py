"""
Agentic Test Suite
==================
Run comprehensive test scenarios through the agentic engine and view metrics.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add frontend directory to path
frontend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(frontend_dir))

from components.auth_utils import require_auth, show_logout_button
from components.session_manager import SessionManager
from components.api_client import APIClient, display_api_error, parseAgenticResponse

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
st.markdown('<div class="test-suite-header"><h1>🧪 Agentic Test Suite</h1><p>Run comprehensive test scenarios and analyze performance metrics</p></div>', unsafe_allow_html=True)

# Session state
if "test_results" not in st.session_state:
    st.session_state.test_results = None
if "test_running" not in st.session_state:
    st.session_state.test_running = False

# Configuration section
with st.expander("⚙️ Test Configuration", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_random = st.number_input(
            "Number of Random Scenarios",
            min_value=0,
            max_value=20,
            value=5,
            help="Number of randomly generated test scenarios"
        )
    
    with col2:
        max_iterations = st.number_input(
            "Max Iterations per Scenario",
            min_value=1,
            max_value=20,
            value=10,
            help="Maximum reasoning iterations for each scenario"
        )
    
    with col3:
        complexity_low = st.number_input("Low Complexity", min_value=0, max_value=10, value=2)
        complexity_medium = st.number_input("Medium Complexity", min_value=0, max_value=10, value=2)
        complexity_high = st.number_input(
            "High Complexity ℹ️", 
            min_value=0, 
            max_value=10, 
            value=1,
            help="Number of high-complexity test scenarios. High-complexity tasks require multiple reasoning passes and tool interactions."
        )

# Run test suite button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_button = st.button("🚀 Run Test Suite", type="primary", width="stretch")

if run_button or st.session_state.test_running:
    if not st.session_state.test_running:
        st.session_state.test_running = True
        st.session_state.test_results = None
    
    # Prepare request
    complexity_dist = {}
    if complexity_low > 0:
        complexity_dist["low"] = complexity_low
    if complexity_medium > 0:
        complexity_dist["medium"] = complexity_medium
    if complexity_high > 0:
        complexity_dist["high"] = complexity_high
    
    request_data = {
        "num_random": num_random,
        "max_iterations": max_iterations,
        "complexity_distribution": complexity_dist if complexity_dist else None
    }
    
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
            st.info("💡 **Tip**: Try reducing the number of scenarios or max iterations.")
            st.session_state.test_results = None
        elif status == "error":
            st.error(f"❌ **Error**: {error or 'Unknown error occurred'}")
            st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify your network connection\n3. Try again with fewer scenarios")
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
    st.markdown("## 📊 Test Suite Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_tests = summary.get("total_tests", 0)
        st.metric("Total Tests", total_tests if total_tests > 0 else "N/A",
                 help="Total number of test scenarios executed")
    
    with col2:
        success_rate = summary.get("success_rate", 0)
        if success_rate > 0:
            st.metric("Success Rate", f"{success_rate:.1%}",
                     help="Percentage of tests that passed successfully")
        else:
            st.metric("Success Rate", "N/A", help="No test results available")
    
    with col3:
        avg_time = summary.get('avg_execution_time', 0)
        if avg_time > 0:
            st.metric("Avg Execution Time", f"{avg_time:.2f}s",
                     help="Average time taken per test scenario")
        else:
            st.metric("Avg Execution Time", "N/A", help="Timing data not available")
    
    with col4:
        avg_passes = summary.get('avg_reasoning_passes', 0)
        if avg_passes > 0:
            st.metric("Avg Reasoning Passes", f"{avg_passes:.1f}",
                     help="Average number of reasoning passes per test")
        else:
            st.metric("Avg Reasoning Passes", "N/A", help="Reasoning data not available")
    
    with col5:
        avg_confidence = summary.get('avg_confidence', 0)
        if avg_confidence > 0:
            st.metric("Avg Confidence", f"{avg_confidence:.2f}",
                     help="Average confidence score across all tests")
        else:
            st.metric("Avg Confidence", "N/A", help="Confidence data not available")
    
    # Charts section
    st.markdown("## 📈 Performance Metrics")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Results Overview", "Error Distribution", "Tool Usage", "Pass/Fail Heatmap"])
    
    with tab1:
        # Results table
        test_results = results.get("test_results", [])
        if test_results and len(test_results) > 0:
            try:
                df = pd.DataFrame([
                    {
                        "Scenario": r.get("scenario", {}).get("title", "Unknown") if isinstance(r.get("scenario"), dict) else str(r.get("scenario", "Unknown")),
                        "Status": r.get("status", "unknown"),
                        "Success": "✅" if r.get("success", False) else "❌",
                        "Execution Time (s)": f"{r.get('execution_time', 0):.2f}",
                        "Reasoning Passes": r.get("reasoning_passes", 0),
                        "Confidence": f"{r.get('confidence_score', 0):.2f}",
                        "Tools Used": len(r.get("tools_used", [])),
                        "Errors": len(r.get("errors", []))
                    }
                    for r in test_results if isinstance(r, dict)
                ])
                if not df.empty:
                    st.dataframe(df, width="stretch")
                else:
                    st.warning("⚠️ **Test results data format issue**: Results are present but couldn't be parsed into a table.")
            except Exception as e:
                st.error(f"❌ **Error displaying test results**: {str(e)}")
                st.info("💡 **Troubleshooting**: The test results may be in an unexpected format. Check backend logs for details.")
                # Show raw results for debugging
                with st.expander("🔍 Debug: Raw Test Results"):
                    st.json(test_results[:2] if len(test_results) > 2 else test_results)
        else:
            st.info("📊 **No Test Results**: Test results will appear here once you run a test suite.")
    
    with tab2:
        # Error distribution chart
        error_dist = summary.get("error_distribution", {})
        if error_dist and isinstance(error_dist, dict) and len(error_dist) > 0:
            try:
                error_df = pd.DataFrame([
                    {"Error Type": str(k), "Count": int(v) if isinstance(v, (int, float)) else 0}
                    for k, v in error_dist.items()
                ])
                if not error_df.empty:
                    fig = px.bar(
                        error_df,
                        x="Error Type",
                        y="Count",
                        title="Error Distribution",
                        color="Count",
                        color_continuous_scale="Reds"
                    )
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info("No errors encountered in test suite.")
            except Exception as e:
                st.warning(f"⚠️ **Error displaying error distribution**: {str(e)}")
                st.info("Error distribution data may be in an unexpected format.")
        else:
            st.info("✅ **No errors encountered** in test suite - all tests passed successfully!")
    
    with tab3:
        # Tool usage chart
        tool_usage = summary.get("tool_usage_counts", {})
        if tool_usage and isinstance(tool_usage, dict) and len(tool_usage) > 0:
            try:
                tool_df = pd.DataFrame([
                    {"Tool": str(k), "Usage Count": int(v) if isinstance(v, (int, float)) else 0}
                    for k, v in tool_usage.items()
                ])
                if not tool_df.empty:
                    fig = px.pie(
                        tool_df,
                        values="Usage Count",
                        names="Tool",
                        title="Tool Usage Distribution"
                    )
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info("No tool usage data available.")
            except Exception as e:
                st.warning(f"⚠️ **Error displaying tool usage**: {str(e)}")
                st.info("Tool usage data may be in an unexpected format.")
        else:
            st.info("No tool usage data available.")
    
    with tab4:
        # Pass/Fail heatmap by complexity
        if test_results and len(test_results) > 0:
            try:
                complexity_data = {}
                for r in test_results:
                    if not isinstance(r, dict):
                        continue
                    scenario = r.get("scenario", {})
                    if isinstance(scenario, dict):
                        complexity = scenario.get("complexity", "unknown")
                    else:
                        complexity = "unknown"
                    
                    if complexity not in complexity_data:
                        complexity_data[complexity] = {"pass": 0, "fail": 0}
                    if r.get("success", False):
                        complexity_data[complexity]["pass"] += 1
                    else:
                        complexity_data[complexity]["fail"] += 1
            
            heatmap_data = []
            for complexity, counts in complexity_data.items():
                heatmap_data.append({
                    "Complexity": complexity.upper(),
                    "Pass": counts["pass"],
                    "Fail": counts["fail"]
                })
            
            if heatmap_data:
                heatmap_df = pd.DataFrame(heatmap_data)
                heatmap_df = heatmap_df.set_index("Complexity")
                fig = px.imshow(
                    heatmap_df,
                    labels=dict(x="Result", y="Complexity", color="Count"),
                    title="Pass/Fail Heatmap by Complexity",
                    color_continuous_scale=["#dc3545", "#28a745"]
                )
                st.plotly_chart(fig, width="stretch")
    
    # Detailed results
    st.markdown("## 🔍 Detailed Test Results")
    
    for i, result in enumerate(test_results):
        with st.expander(f"Test {i+1}: {result['scenario'].get('title', 'Unknown')} - {result['status'].upper()}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Scenario Details:**")
                st.json(result["scenario"])
            
            with col2:
                st.write("**Execution Metrics:**")
                metrics_data = {
                    "Execution Time": f"{result['execution_time']:.2f}s",
                    "Reasoning Passes": result["reasoning_passes"],
                    "Confidence Score": f"{result['confidence_score']:.2f}",
                    "Plan Steps": result["plan_steps"],
                    "Executed Steps": result["executed_steps"],
                    "Tools Used": ", ".join(result["tools_used"]) if result["tools_used"] else "None",
                    "Required Tools": ", ".join(result["required_tools"]) if result["required_tools"] else "None",
                    "Missing Tools": ", ".join(result["missing_tools"]) if result["missing_tools"] else "None"
                }
                for key, value in metrics_data.items():
                    st.write(f"**{key}:** {value}")
            
            if result["errors"]:
                st.error("**Errors:**")
                for error in result["errors"]:
                    st.write(f"- {error}")

