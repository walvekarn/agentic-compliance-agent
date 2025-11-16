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

# Add dashboard directory to path
dashboard_dir = Path(__file__).parent.parent
sys.path.insert(0, str(dashboard_dir))

from components.auth_utils import require_auth
from components.session_manager import SessionManager
from components.api_client import APIClient, display_api_error, parseAgenticResponse

# Page config
st.set_page_config(page_title="Agentic Test Suite", page_icon="🧪", layout="wide")

# Authentication
require_auth()

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
    run_button = st.button("🚀 Run Test Suite", type="primary", use_container_width=True)

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
        st.session_state.test_results = None
    else:
        display_api_error(response)
        st.session_state.test_results = None

# Display results
if st.session_state.test_results:
    results = st.session_state.test_results
    summary = results.get("summary", {}) if isinstance(results, dict) else {}
    
    # Summary metrics
    st.markdown("## 📊 Test Suite Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Tests", summary.get("total_tests", 0))
    
    with col2:
        success_rate = summary.get("success_rate", 0)
        st.metric("Success Rate", f"{success_rate:.1%}")
    
    with col3:
        st.metric("Avg Execution Time", f"{summary.get('avg_execution_time', 0):.2f}s")
    
    with col4:
        st.metric("Avg Reasoning Passes", f"{summary.get('avg_reasoning_passes', 0):.1f}")
    
    with col5:
        st.metric("Avg Confidence", f"{summary.get('avg_confidence', 0):.2f}")
    
    # Charts section
    st.markdown("## 📈 Performance Metrics")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Results Overview", "Error Distribution", "Tool Usage", "Pass/Fail Heatmap"])
    
    with tab1:
        # Results table
        test_results = results.get("test_results", [])
        if test_results:
            df = pd.DataFrame([
                {
                    "Scenario": r["scenario"].get("title", "Unknown"),
                    "Status": r["status"],
                    "Success": "✅" if r["success"] else "❌",
                    "Execution Time (s)": f"{r['execution_time']:.2f}",
                    "Reasoning Passes": r["reasoning_passes"],
                    "Confidence": f"{r['confidence_score']:.2f}",
                    "Tools Used": len(r["tools_used"]),
                    "Errors": len(r["errors"])
                }
                for r in test_results
            ])
            st.dataframe(df, use_container_width=True)
    
    with tab2:
        # Error distribution chart
        error_dist = summary.get("error_distribution", {})
        if error_dist:
            error_df = pd.DataFrame([
                {"Error Type": k, "Count": v}
                for k, v in error_dist.items()
            ])
            fig = px.bar(
                error_df,
                x="Error Type",
                y="Count",
                title="Error Distribution",
                color="Count",
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No errors encountered in test suite.")
    
    with tab3:
        # Tool usage chart
        tool_usage = summary.get("tool_usage_counts", {})
        if tool_usage:
            tool_df = pd.DataFrame([
                {"Tool": k, "Usage Count": v}
                for k, v in tool_usage.items()
            ])
            fig = px.pie(
                tool_df,
                values="Usage Count",
                names="Tool",
                title="Tool Usage Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tool usage data available.")
    
    with tab4:
        # Pass/Fail heatmap by complexity
        if test_results:
            complexity_data = {}
            for r in test_results:
                complexity = r["scenario"].get("complexity", "unknown")
                if complexity not in complexity_data:
                    complexity_data[complexity] = {"pass": 0, "fail": 0}
                if r["success"]:
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
                st.plotly_chart(fig, use_container_width=True)
    
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

