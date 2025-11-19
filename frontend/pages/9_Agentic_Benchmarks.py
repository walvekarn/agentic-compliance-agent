"""
Agentic Benchmark Lab
======================
Run benchmarks and visualize performance metrics with charts and radar diagrams.
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
st.set_page_config(page_title="Agentic Benchmark Lab", page_icon="📊", layout="wide")

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
.benchmark-header {
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
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="benchmark-header"><h1>📊 Agentic Benchmark Lab</h1><p>Evaluate performance with comprehensive benchmarks</p></div>', unsafe_allow_html=True)

# Feature explanation
st.markdown("""
<div style='background-color: #e7f3ff; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 2rem;'>
    <h3 style='margin-top: 0; color: #1e40af;'>❓ What is This Tool?</h3>
    <p style='color: #1e293b; margin-bottom: 0.5rem;'><strong>Purpose:</strong> Measure and compare AI performance across different complexity levels and scenarios. Helps evaluate how well the AI handles various compliance tasks.</p>
    <p style='color: #1e293b; margin-bottom: 0.5rem;'><strong>When to Use:</strong> When evaluating AI performance improvements, comparing different AI configurations, or validating system capabilities before deployment.</p>
    <p style='color: #1e293b; margin-bottom: 0.5rem;'><strong>What It Does:</strong> Runs standardized test cases at different complexity levels (light, medium, heavy) and measures accuracy, reasoning depth, tool precision, and reflection correction scores.</p>
    <p style='color: #1e293b; margin-bottom: 0.5rem;'><strong>Expected Output:</strong> Performance metrics, radar diagrams showing strengths/weaknesses, comparison charts, and detailed results for each test case. Helps identify areas for improvement.</p>
    <p style='color: #1e293b; margin-bottom: 0;'><strong>Time Required:</strong> 5-15 minutes depending on number of levels and cases selected. More cases = more accurate results but longer runtime.</p>
</div>
""", unsafe_allow_html=True)

# Session state
if "benchmark_results" not in st.session_state:
    st.session_state.benchmark_results = None
if "benchmark_running" not in st.session_state:
    st.session_state.benchmark_running = False

# Configuration section
with st.expander("⚙️ Benchmark Configuration", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        from components.ui_helpers import multiselect_with_select_all
        benchmark_levels = multiselect_with_select_all(
            "Benchmark Levels",
            options=["light", "medium", "heavy"],
            default=["light", "medium", "heavy"],
            key="benchmark_levels_multiselect",
            help="Select complexity levels to benchmark",
            inside_form=False
        )
    
    with col2:
        max_cases_per_level = st.number_input(
            "Max Cases per Level",
            min_value=1,
            max_value=30,
            value=10,
            help="Maximum benchmark cases to run per level"
        )
    
    with col3:
        max_iterations = st.number_input(
            "Max Iterations per Case",
            min_value=1,
            max_value=20,
            value=10,
            help="Maximum reasoning iterations for each case"
        )

# Run benchmark button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_button = st.button("🚀 Run Benchmark Suite", type="primary", width="stretch")

if run_button or st.session_state.benchmark_running:
    if not st.session_state.benchmark_running:
        st.session_state.benchmark_running = True
        st.session_state.benchmark_results = None
    
    # Prepare request
    request_data = {
        "levels": benchmark_levels if benchmark_levels else None,
        "max_cases_per_level": max_cases_per_level,
        "max_iterations": max_iterations
    }
    
    # Show progress with 120s timeout
    try:
        with st.spinner("Running benchmark suite... This may take several minutes."):
            response = api_client.post("/api/v1/agentic/benchmarks", request_data, timeout=120)
        
        st.session_state.benchmark_running = False
        
        # Parse standardized agentic response
        status, results, error, timestamp = parseAgenticResponse(response)
        
        if status == "completed" and results:
            st.session_state.benchmark_results = results
            st.success(f"✅ Benchmark suite completed! (Completed at {timestamp or 'unknown'})")
        elif status == "timeout":
            st.error(f"⏱️ **Timeout**: {error or 'Benchmark timed out after 120 seconds'}")
            st.info("💡 **Tip**: Try reducing the number of benchmark levels or max iterations.")
            st.session_state.benchmark_results = None
        elif status == "error":
            st.error(f"❌ **Error**: {error or 'Unknown error occurred'}")
            st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify your network connection\n3. Try again with fewer levels")
            st.session_state.benchmark_results = None
        else:
            display_api_error(response)
            st.session_state.benchmark_results = None
    except Exception as e:
        st.session_state.benchmark_running = False
        st.error(f"❌ **API Error**: {str(e)}")
        st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify your network connection\n3. Try again in a few moments")
        st.session_state.benchmark_results = None

# Display results
if st.session_state.benchmark_results:
    results = st.session_state.benchmark_results
    summary = results.get("summary", {}) if isinstance(results, dict) else {}
    
    # Summary metrics
    st.markdown("## 📊 Benchmark Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_cases = summary.get("total_cases", 0)
        st.metric("Total Cases", total_cases if total_cases > 0 else "N/A",
                 help="Total number of benchmark cases executed")
    
    with col2:
        success_rate = summary.get("success_rate", 0)
        if success_rate > 0:
            st.metric("Success Rate", f"{success_rate:.1%}",
                     help="Percentage of benchmark cases that passed")
        else:
            st.metric("Success Rate", "N/A", help="No benchmark results available")
    
    with col3:
        avg_accuracy = summary.get('average_accuracy', 0)
        if avg_accuracy > 0:
            st.metric("Avg Accuracy", f"{avg_accuracy:.3f}",
                     help="Average accuracy score across all benchmarks")
        else:
            st.metric("Avg Accuracy", "N/A", help="Accuracy data not available")
    
    with col4:
        reasoning_depth = summary.get('average_reasoning_depth_score', 0)
        if reasoning_depth > 0:
            st.metric("Avg Reasoning Depth", f"{reasoning_depth:.3f}",
                     help="Average reasoning depth score (0.0-1.0)")
        else:
            st.metric("Avg Reasoning Depth", "N/A", help="Reasoning depth data not available")
    
    with col5:
        avg_time = summary.get('average_execution_time', 0)
        if avg_time > 0:
            st.metric("Avg Execution Time", f"{avg_time:.2f}s",
                     help="Average time taken per benchmark case")
        else:
            st.metric("Avg Execution Time", "N/A", help="Timing data not available")
    
    # Performance scorecard
    st.markdown("## 🎯 Performance Scorecard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        accuracy = summary.get("average_accuracy", 0)
        if accuracy > 0:
            delta_val = (accuracy - 0.7) * 100
            st.metric("Accuracy", f"{accuracy:.1%}", 
                     delta=f"{delta_val:.1f}% vs baseline" if abs(delta_val) > 0.1 else None,
                     help="Average accuracy score (0.0-1.0)")
        else:
            st.metric("Accuracy", "N/A", help="Accuracy data not available")
    
    with col2:
        reasoning_depth = summary.get("average_reasoning_depth_score", 0)
        if reasoning_depth > 0:
            st.metric("Reasoning Depth", f"{reasoning_depth:.3f}",
                     help="Average reasoning depth score (0.0-1.0)")
        else:
            st.metric("Reasoning Depth", "N/A", help="Reasoning depth data not available")
    
    with col3:
        tool_precision = summary.get("average_tool_precision_score", 0)
        if tool_precision > 0:
            st.metric("Tool Precision", f"{tool_precision:.3f}",
                     help="Average tool precision score (0.0-1.0)")
        else:
            st.metric("Tool Precision", "N/A", help="Tool precision data not available")
    
    with col4:
        reflection_correction = summary.get("average_reflection_correction_score", 0)
        if reflection_correction > 0:
            st.metric("Reflection Correction", f"{reflection_correction:.3f}",
                     help="Average reflection correction score (0.0-1.0)")
        else:
            st.metric("Reflection Correction", "N/A", help="Reflection correction data not available")
    
    # Charts section
    st.markdown("## 📈 Performance Charts")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Radar Diagram", "Metrics Comparison", "Results by Level", "Execution Time Analysis"])
    
    with tab1:
        # Radar diagram
        metrics_data = {
            "Accuracy": summary.get("average_accuracy", 0),
            "Reasoning Depth": summary.get("average_reasoning_depth_score", 0),
            "Tool Precision": summary.get("average_tool_precision_score", 0),
            "Reflection Correction": summary.get("average_reflection_correction_score", 0)
        }
        
        categories = list(metrics_data.keys())
        values = list(metrics_data.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Performance',
            line_color='#667eea'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Performance Radar Diagram"
        )
        
        st.plotly_chart(fig, width="stretch")
    
    with tab2:
        # Metrics comparison chart
        benchmark_results = results.get("benchmark_results", [])
        if benchmark_results:
            metrics_df = pd.DataFrame([
                {
                    "Case": r["case"].get("title", r["case_id"]),
                    "Accuracy": r["metrics"].get("accuracy", 0),
                    "Reasoning Depth": r["metrics"].get("reasoning_depth_score", 0),
                    "Tool Precision": r["metrics"].get("tool_precision_score", 0),
                    "Reflection Correction": r["metrics"].get("reflection_correction_score", 0)
                }
                for r in benchmark_results if r["status"] == "success"
            ])
            
            if not metrics_df.empty:
                fig = px.bar(
                    metrics_df,
                    x="Case",
                    y=["Accuracy", "Reasoning Depth", "Tool Precision", "Reflection Correction"],
                    title="Metrics Comparison by Case",
                    barmode="group"
                )
                st.plotly_chart(fig, width="stretch")
    
    with tab3:
        # Results by level
        results_by_level = summary.get("results_by_level", {})
        if results_by_level:
            level_data = []
            for level, stats in results_by_level.items():
                level_data.append({
                    "Level": level.upper(),
                    "Total": stats.get("total", 0),
                    "Successful": stats.get("successful", 0),
                    "Failed": stats.get("failed", 0)
                })
            
            level_df = pd.DataFrame(level_data)
            
            fig = px.bar(
                level_df,
                x="Level",
                y=["Successful", "Failed"],
                title="Results by Complexity Level",
                barmode="group",
                color_discrete_map={"Successful": "#28a745", "Failed": "#dc3545"}
            )
            st.plotly_chart(fig, width="stretch")
    
    with tab4:
        # Execution time analysis
        benchmark_results = results.get("benchmark_results", [])
        if benchmark_results:
            time_df = pd.DataFrame([
                {
                    "Case": r["case"].get("title", r["case_id"]),
                    "Level": r["case"].get("level", "unknown"),
                    "Execution Time (s)": r["execution_time"]
                }
                for r in benchmark_results
            ])
            
            if not time_df.empty:
                fig = px.box(
                    time_df,
                    x="Level",
                    y="Execution Time (s)",
                    title="Execution Time Distribution by Level",
                    color="Level"
                )
                st.plotly_chart(fig, width="stretch")
    
    # Detailed results table
    st.markdown("## 🔍 Detailed Benchmark Results")
    
    benchmark_results = results.get("benchmark_results", [])
    if benchmark_results:
        results_df = pd.DataFrame([
            {
                "Case ID": r["case_id"],
                "Title": r["case"].get("title", "N/A"),
                "Level": r["case"].get("level", "unknown"),
                "Status": r["status"],
                "Execution Time (s)": f"{r['execution_time']:.2f}",
                "Accuracy": f"{r['metrics'].get('accuracy', 0):.3f}",
                "Reasoning Depth": f"{r['metrics'].get('reasoning_depth_score', 0):.3f}",
                "Tool Precision": f"{r['metrics'].get('tool_precision_score', 0):.3f}",
                "Reflection Correction": f"{r['metrics'].get('reflection_correction_score', 0):.3f}"
            }
            for r in benchmark_results
        ])
        st.dataframe(results_df, width="stretch")
        
        # Individual case details
        st.markdown("### 📋 Individual Case Details")
        for i, result in enumerate(benchmark_results):
            with st.expander(f"Case {i+1}: {result['case'].get('title', result['case_id'])} - {result['status'].upper()}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Case Information:**")
                    st.json(result["case"])
                
                with col2:
                    st.write("**Metrics:**")
                    st.json(result["metrics"])
                
                if result.get("error"):
                    st.error(f"**Error:** {result['error']}")

