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

# Add dashboard directory to path
dashboard_dir = Path(__file__).parent.parent
sys.path.insert(0, str(dashboard_dir))

from components.auth_utils import require_auth
from components.session_manager import SessionManager
from components.api_client import APIClient, display_api_error, parseAgenticResponse

# Page config
st.set_page_config(page_title="Agentic Benchmark Lab", page_icon="📊", layout="wide")

# Authentication
require_auth()

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
            help="Select complexity levels to benchmark"
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
    run_button = st.button("🚀 Run Benchmark Suite", type="primary", use_container_width=True)

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
        st.session_state.benchmark_results = None
    elif status == "error":
        st.error(f"❌ **Error**: {error or 'Unknown error occurred'}")
        st.session_state.benchmark_results = None
    else:
        display_api_error(response)
        st.session_state.benchmark_results = None

# Display results
if st.session_state.benchmark_results:
    results = st.session_state.benchmark_results
    summary = results.get("summary", {}) if isinstance(results, dict) else {}
    
    # Summary metrics
    st.markdown("## 📊 Benchmark Summary")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Cases", summary.get("total_cases", 0))
    
    with col2:
        success_rate = summary.get("success_rate", 0)
        st.metric("Success Rate", f"{success_rate:.1%}")
    
    with col3:
        st.metric("Avg Accuracy", f"{summary.get('average_accuracy', 0):.3f}")
    
    with col4:
        st.metric("Avg Reasoning Depth", f"{summary.get('average_reasoning_depth_score', 0):.3f}")
    
    with col5:
        st.metric("Avg Execution Time", f"{summary.get('average_execution_time', 0):.2f}s")
    
    # Performance scorecard
    st.markdown("## 🎯 Performance Scorecard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        accuracy = summary.get("average_accuracy", 0)
        st.metric("Accuracy", f"{accuracy:.1%}", delta=f"{(accuracy - 0.7) * 100:.1f}% vs baseline")
    
    with col2:
        reasoning_depth = summary.get("average_reasoning_depth_score", 0)
        st.metric("Reasoning Depth", f"{reasoning_depth:.3f}")
    
    with col3:
        tool_precision = summary.get("average_tool_precision_score", 0)
        st.metric("Tool Precision", f"{tool_precision:.3f}")
    
    with col4:
        reflection_correction = summary.get("average_reflection_correction_score", 0)
        st.metric("Reflection Correction", f"{reflection_correction:.3f}")
    
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
        
        st.plotly_chart(fig, use_container_width=True)
    
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
                st.plotly_chart(fig, use_container_width=True)
    
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
            st.plotly_chart(fig, use_container_width=True)
    
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
                st.plotly_chart(fig, use_container_width=True)
    
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
        st.dataframe(results_df, use_container_width=True)
        
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

