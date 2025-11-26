"""
Error Recovery Simulator
========================
Simulate failures and test error recovery capabilities.
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
from components.constants import COMPANY_TYPE_OPTIONS, INDUSTRY_OPTIONS, LOCATION_OPTIONS

# Page config
st.set_page_config(page_title="Error Recovery Simulator", page_icon="🔧", layout="wide")

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
.simulator-header {
    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
    color: white;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
}
.failure-badge {
    background-color: #dc3545;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
}
.recovery-badge {
    background-color: #28a745;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
}
.timeline-event {
    padding: 8px;
    margin: 4px 0;
    border-radius: 4px;
    border-left: 4px solid;
}
</style>
""", unsafe_allow_html=True)

# Header
from components.ui_helpers import render_page_header
render_page_header(
    title="Error Recovery Simulator",
    icon="🔧",
    description="Simulate failures and test error recovery capabilities"
)

# Feature explanation
st.markdown("""
<div style='background-color: #fff3cd; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #ffc107; margin-bottom: 2rem;'>
    <h3 style='margin-top: 0; color: #856404;'>❓ What is This Tool?</h3>
    <p style='color: #1e293b; margin-bottom: 0.5rem;'><strong>Purpose:</strong> Test how the AI system handles failures and recovers from errors. This helps ensure system reliability before deployment.</p>
    <p style='color: #1e293b; margin-bottom: 0.5rem;'><strong>When to Use:</strong> Before deploying to production, or when troubleshooting system reliability issues. Use this to verify the AI can recover from various failure scenarios.</p>
    <p style='color: #1e293b; margin-bottom: 0.5rem;'><strong>What It Does:</strong> Injects simulated failures (timeouts, network errors, invalid inputs, etc.) into the AI execution and measures how successfully the system recovers from each failure type.</p>
    <p style='color: #1e293b; margin-bottom: 0.5rem;'><strong>Expected Output:</strong> A detailed report showing which failures were successfully recovered from and which caused system errors. Includes recovery timeline, success rates, and recommendations.</p>
    <p style='color: #1e293b; margin-bottom: 0;'><strong>Time Required:</strong> 2-5 minutes per simulation, depending on complexity and failure rate settings.</p>
</div>
""", unsafe_allow_html=True)

# Session state
if "simulation_results" not in st.session_state:
    st.session_state.simulation_results = None
if "simulation_running" not in st.session_state:
    st.session_state.simulation_running = False

# Failure type options
FAILURE_TYPES = [
    "tool_timeout",
    "invalid_input",
    "degraded_output",
    "missing_tool_result",
    "network_error",
    "permission_error"
]

# Configuration section
with st.expander("⚙️ Simulation Configuration", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        failure_type = st.selectbox(
            "Failure Type",
            options=FAILURE_TYPES,
            help="Type of failure to inject during execution"
        )
        
        failure_rate = st.slider(
            "Failure Rate",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.1,
            help="Probability of injecting the failure (0.0 = never, 1.0 = always)"
        )
        
        max_iterations = st.number_input(
            "Max Iterations",
            min_value=1,
            max_value=20,
            value=10,
            help="Maximum reasoning iterations"
        )
    
    with col2:
        task_description = st.text_area(
            "Task Description",
            value="Analyze GDPR compliance requirements for data processing activities",
            help="Compliance task to execute with failure injection"
        )
        
        # Optional entity context
        use_entity_context = st.checkbox(
            "Include Entity Context",
            key="error_recovery_use_entity_context_checkbox"
        )
        
        if use_entity_context:
            entity_name = st.text_input("Entity Name", value="TestCorp")
            entity_type = st.selectbox("Entity Type", options=COMPANY_TYPE_OPTIONS)
            from components.ui_helpers import multiselect_with_select_all
            locations = multiselect_with_select_all(
                "Locations", 
                options=LOCATION_OPTIONS, 
                default=["EU"],
                key="recovery_locations_multiselect",
                help="Select locations for entity context",
                inside_form=False
            )
            industry = st.selectbox("Industry", options=INDUSTRY_OPTIONS)

# Run simulation buttons
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    run_button = st.button("🚀 Run Failure Simulation", type="primary", width="stretch")
with col2:
    run_enhanced_button = st.button("🔧 Run Enhanced Error Recovery Suite", type="secondary", width="stretch")

# Session state for enhanced recovery
if "enhanced_recovery_results" not in st.session_state:
    st.session_state.enhanced_recovery_results = None
if "enhanced_recovery_running" not in st.session_state:
    st.session_state.enhanced_recovery_running = False

if run_button or st.session_state.simulation_running:
    if not st.session_state.simulation_running:
        st.session_state.simulation_running = True
        st.session_state.simulation_results = None
    
    # Prepare request
    request_data = {
        "task": task_description,
        "failure_type": failure_type,
        "failure_rate": failure_rate,
        "max_iterations": max_iterations
    }
    
    if use_entity_context:
        request_data["entity_context"] = {
            "entity_name": entity_name,
            "entity_type": entity_type,
            "locations": locations,
            "industry": industry,
            "has_personal_data": True
        }
        request_data["task_context"] = {
            "task_description": task_description,
            "task_category": "DATA_PROTECTION"
        }
    
    # Show progress with 120s timeout
    try:
        with st.spinner(f"Running simulation with {failure_type} failures... This may take a few minutes."):
            response = api_client.post("/api/v1/agentic/recovery", request_data, timeout=120)
        
        st.session_state.simulation_running = False
        
        # Parse standardized agentic response
        status, results, error, timestamp = parseAgenticResponse(response)
        
        if status == "completed" and results:
            st.session_state.simulation_results = results
            st.success(f"✅ Simulation completed! (Completed at {timestamp or 'unknown'})")
        elif status == "timeout":
            st.error(f"⏱️ **Timeout**: {error or 'Simulation timed out after 120 seconds'}")
            st.info("💡 **Tip**: Try reducing the number of failure scenarios or max iterations.")
            st.session_state.simulation_results = None
        elif status == "error":
            st.error(f"❌ **Error**: {error or 'Unknown error occurred'}")
            st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify your network connection\n3. Try again with fewer scenarios")
            st.session_state.simulation_results = None
        else:
            display_api_error(response)
            st.session_state.simulation_results = None
    except Exception as e:
        st.session_state.simulation_running = False
        st.error(f"❌ **API Error**: {str(e)}")
        st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify your network connection\n3. Try again in a few moments")
        st.session_state.simulation_results = None

# Display results
if st.session_state.simulation_results:
    results = st.session_state.simulation_results
    
    # Check if running in mock mode (all values are zero)
    exec_time = results.get('execution_time', 0)
    recovery_rate = results.get('recovery_rate', 0)
    if exec_time == 0 and recovery_rate == 0:
        st.info("ℹ️ **Mock Mode**: Running in mock mode without API key. Recovery times show 0ms because errors are simulated instantly. In production mode with real API calls, recovery times will reflect actual retry delays and network latency.")
    
    # Summary metrics
    from components.ui_helpers import render_section_header
    render_section_header("Simulation Summary", icon="📊", level=2)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = results.get("status", "unknown")
        st.metric("Status", status.upper() if status != "unknown" else "N/A",
                 help="Overall simulation status")
    
    with col2:
        exec_time = results.get('execution_time', 0)
        if exec_time > 0:
            st.metric("Execution Time", f"{exec_time:.2f}s",
                     help="Total simulation execution time")
        else:
            st.metric("Execution Time", "N/A", help="Execution time not available")
    
    with col3:
        failures = results.get("failures", [])
        failure_count = len(failures) if isinstance(failures, list) and failures else 0
        # Check if we have actual failure data or if it's just empty
        if failure_count > 0:
            st.metric("Failures Injected", failure_count,
                     help="Number of failures injected during simulation")
        else:
            # Check if failures key exists but is empty vs missing
            if "failures" in results:
                st.metric("Failures Injected", "0", 
                         delta="No failures injected", 
                         delta_color="off",
                         help="No failures were injected. Check simulation configuration.")
            else:
                st.metric("Failures Injected", "N/A",
                         help="Failure data not available in response")
    
    with col4:
        recovery_attempts = results.get("recovery_attempts", [])
        recovery_count = len(recovery_attempts) if isinstance(recovery_attempts, list) and recovery_attempts else 0
        if recovery_count > 0:
            st.metric("Recovery Attempts", recovery_count,
                     help="Number of recovery attempts made")
        else:
            if "recovery_attempts" in results:
                st.metric("Recovery Attempts", "0",
                         delta="No recovery needed",
                         delta_color="off", 
                         help="No recovery attempts were made (either no failures occurred or recovery wasn't triggered)")
            else:
                st.metric("Recovery Attempts", "N/A",
                         help="Recovery data not available in response")
    
    # Failure statistics
    failure_stats = results.get("failure_statistics", {})
    taxonomy_stats = results.get("taxonomy_statistics", {})
    
    render_section_header("Failure Analysis", icon="📈", level=2)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Recovery Timeline", "Failure Distribution", "Recovery Statistics", "Taxonomy Analysis"])
    
    with tab1:
        # Recovery timeline
        timeline = results.get("recovery_timeline", [])
        if timeline:
            timeline_df = pd.DataFrame(timeline)
            
            # Display timeline events
            for event in timeline:
                event_type = event.get("event", "unknown")
                timestamp = event.get("timestamp", "")
                
                if event_type == "failure":
                    st.markdown(f"""
                    <div class="timeline-event" style="border-left-color: #dc3545; background-color: #ffe6e6;">
                        <strong>❌ Failure</strong> - {event.get('failure_type', 'unknown')}<br>
                        <small>Tool: {event.get('tool', 'N/A')} | {timestamp}</small><br>
                        {event.get('message', '')}
                    </div>
                    """, unsafe_allow_html=True)
                elif event_type == "recovery_attempt":
                    success = event.get("success", False)
                    badge = "✅" if success else "❌"
                    st.markdown(f"""
                    <div class="timeline-event" style="border-left-color: {'#28a745' if success else '#dc3545'}; background-color: {'#e6ffe6' if success else '#ffe6e6'};">
                        <strong>{badge} Recovery Attempt</strong><br>
                        <small>{timestamp}</small><br>
                        Action: {event.get('action', 'N/A')}<br>
                        Success: {success}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No failures or recovery attempts recorded.")
    
    with tab2:
        # Failure distribution
        failure_counts = failure_stats.get("failure_counts", {})
        if failure_counts:
            failure_df = pd.DataFrame([
                {"Failure Type": k, "Count": v}
                for k, v in failure_counts.items()
            ])
            fig = px.bar(
                failure_df,
                x="Failure Type",
                y="Count",
                color="Count",
                color_continuous_scale="Reds"
            )
            fig.update_layout(
                height=400,
                title=None,
                margin=dict(l=60, r=60, t=40, b=60)
            )
            st.markdown("#### Failure Type Distribution")
            st.plotly_chart(fig, width="stretch")
        else:
            from components.ui_helpers import render_empty_state
            render_empty_state("No Failures Recorded", "📊", "Run a simulation to see failure data")
    
    with tab3:
        # Recovery statistics
        recovery_success_rate = failure_stats.get("recovery_success_rate", 0)
        recovery_attempts = failure_stats.get("recovery_attempts", 0)
        successful_recoveries = failure_stats.get("successful_recoveries", 0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Recovery Attempts", recovery_attempts if recovery_attempts > 0 else "N/A",
                     help="Total number of recovery attempts made")
        with col2:
            st.metric("Successful Recoveries", successful_recoveries if successful_recoveries > 0 else "N/A",
                     help="Number of successful recovery attempts")
        with col3:
            if recovery_success_rate > 0:
                st.metric("Recovery Success Rate", f"{recovery_success_rate:.1%}",
                         help="Percentage of recovery attempts that succeeded")
            else:
                st.metric("Recovery Success Rate", "N/A", help="No recovery data available")
        
        if recovery_attempts > 0:
            recovery_data = {
                "Successful": successful_recoveries,
                "Failed": recovery_attempts - successful_recoveries
            }
            fig = px.pie(
                values=list(recovery_data.values()),
                names=list(recovery_data.keys()),
                color_discrete_map={"Successful": "#28a745", "Failed": "#dc3545"}
            )
            fig.update_layout(
                height=400,
                title=None,
                margin=dict(l=60, r=60, t=40, b=60)
            )
            st.markdown("#### Recovery Success Distribution")
            st.plotly_chart(fig, width="stretch")
    
    with tab4:
        # Taxonomy analysis
        category_dist = taxonomy_stats.get("category_distribution", {})
        strategy_dist = taxonomy_stats.get("strategy_distribution", {})
        avg_retry_score = taxonomy_stats.get("average_retry_score", 0)
        
        st.metric("Average Retry Score", f"{avg_retry_score:.2f}")
        
        if category_dist:
            st.markdown("### Failure Category Distribution")
            category_df = pd.DataFrame([
                {"Category": k, "Count": v}
                for k, v in category_dist.items()
            ])
            fig = px.pie(
                category_df,
                values="Count",
                names="Category"
            )
            fig.update_layout(
                height=400,
                title=None,
                margin=dict(l=60, r=60, t=40, b=60)
            )
            st.markdown("#### Failure Categories")
            st.plotly_chart(fig, width="stretch")
        
        if strategy_dist:
            st.markdown("### Retry Strategy Distribution")
            strategy_df = pd.DataFrame([
                {"Strategy": k, "Count": v}
                for k, v in strategy_dist.items()
            ])
            fig = px.bar(
                strategy_df,
                x="Strategy",
                y="Count",
                color="Count",
                color_continuous_scale="Blues"
            )
            fig.update_layout(
                height=400,
                title=None,
                margin=dict(l=60, r=60, t=40, b=60)
            )
            st.markdown("#### Retry Strategies Used")
            st.plotly_chart(fig, width="stretch")
    
    # Detailed failure list
    render_section_header("Detailed Failures", icon="🔍", level=2)
    
    failures = results.get("failures", [])
    if failures:
        for i, failure in enumerate(failures):
            with st.expander(f"Failure {i+1}: {failure.get('type', 'unknown')}"):
                st.json(failure)
    else:
        st.info("No failures were injected.")
    
    # Execution result
    if results.get("result"):
        st.markdown("## 📋 Execution Result")
        with st.expander("View Full Execution Result"):
            st.json(results["result"])

# Enhanced Error Recovery Suite Section
if run_enhanced_button or st.session_state.enhanced_recovery_running:
    if not st.session_state.enhanced_recovery_running:
        st.session_state.enhanced_recovery_running = True
        st.session_state.enhanced_recovery_results = None
    
    # Prepare request for enhanced error recovery
    request_data = {}  # Empty dict - uses defaults
    
    # Show progress
    try:
        with st.spinner("Running enhanced error recovery suite... Testing all error types with retry logic. This may take a few minutes."):
            response = api_client.post("/api/v1/agentic/error-recovery", request_data, timeout=180)
        
        st.session_state.enhanced_recovery_running = False
        
        # Parse standardized agentic response
        status, results, error, timestamp = parseAgenticResponse(response)
        
        if status == "completed" and results:
            st.session_state.enhanced_recovery_results = results
            st.success(f"✅ Enhanced error recovery suite completed! (Completed at {timestamp or 'unknown'})")
        elif status == "timeout":
            st.error(f"⏱️ **Timeout**: {error or 'Error recovery suite timed out after 180 seconds'}")
            st.info("💡 **Tip**: Try again or check backend logs for issues.")
            st.session_state.enhanced_recovery_results = None
        elif status == "error":
            st.error(f"❌ **Error**: {error or 'Unknown error occurred'}")
            st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify your network connection\n3. Try again in a few moments")
            st.session_state.enhanced_recovery_results = None
        else:
            display_api_error(response)
            st.session_state.enhanced_recovery_results = None
    except Exception as e:
        st.session_state.enhanced_recovery_running = False
        st.error(f"❌ **API Error**: {str(e)}")
        st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify your network connection\n3. Try again in a few moments")
        st.session_state.enhanced_recovery_results = None

# Display enhanced recovery results
if st.session_state.enhanced_recovery_results:
    results = st.session_state.enhanced_recovery_results
    
    render_section_header("Enhanced Error Recovery Diagnostics", icon="🔧", level=2)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        recovery_rate = results.get("recovery_rate", 0.0)
        st.metric("Recovery Rate", f"{recovery_rate:.1%}",
                 help="Percentage of errors successfully recovered from")
    
    with col2:
        fallback_quality = results.get("fallback_quality", 0.0)
        st.metric("Fallback Quality", f"{fallback_quality:.1%}",
                 help="Average quality of fallback responses (0-1)")
    
    with col3:
        summary = results.get("summary", {})
        total_tests = summary.get("total_tests", 0)
        st.metric("Total Tests", total_tests,
                 help="Number of error types tested")
    
    with col4:
        avg_time = summary.get("avg_recovery_time_ms", 0.0)
        st.metric("Avg Recovery Time", f"{avg_time:.1f}ms",
                 help="Average time to recover per error type")
    
    # Waterfall visualization
    render_section_header("Recovery Waterfall", icon="🌊", level=2)
    
    raw_runs = results.get("raw_runs", [])
    if raw_runs:
        # Create waterfall data for each error type
        waterfall_data = []
        for run in raw_runs:
            error_type = run.get("error_type", "unknown")
            recovery_attempts = run.get("recovery_attempts", [])
            recovered = run.get("recovered", False)
            
            # Build waterfall steps
            steps = []
            for attempt in recovery_attempts:
                steps.append({
                    "error_type": error_type,
                    "attempt": attempt.get("attempt", 0),
                    "success": attempt.get("success", False),
                    "time_ms": attempt.get("time_ms", 0),
                    "fallback_used": attempt.get("fallback_used", False),
                    "error": attempt.get("error")
                })
            
            # Add final state
            if recovered:
                steps.append({
                    "error_type": error_type,
                    "attempt": "Final",
                    "success": True,
                    "time_ms": run.get("recovery_time_ms", 0),
                    "fallback_used": run.get("fallback_used", False),
                    "error": None
                })
            else:
                steps.append({
                    "error_type": error_type,
                    "attempt": "Final",
                    "success": False,
                    "time_ms": run.get("recovery_time_ms", 0),
                    "fallback_used": run.get("fallback_used", False),
                    "error": "Failed to recover"
                })
            
            waterfall_data.append({
                "error_type": error_type,
                "steps": steps
            })
        
        # Display waterfall for each error type
        for wf_item in waterfall_data[:5]:  # Show first 5
            error_type = wf_item["error_type"]
            steps = wf_item["steps"]
            
            with st.expander(f"Waterfall: {error_type}"):
                # Create visual representation
                html_content = """
                <div style="display: flex; flex-direction: column; gap: 10px; padding: 10px;">
                """
                for i, step in enumerate(steps):
                    attempt_num = step["attempt"]
                    success = step["success"]
                    time_ms = step["time_ms"]
                    fallback = step.get("fallback_used", False)
                    error = step.get("error")
                    
                    color = "#28a745" if success else "#dc3545"
                    icon = "✅" if success else "❌"
                    
                    error_text = f" | Error: {error}" if error else ""
                    fallback_text = " | Fallback Used" if fallback else ""
                    html_content += f"""
                    <div style="display: flex; align-items: center; gap: 10px; padding: 8px; background-color: {'#e6ffe6' if success else '#ffe6e6'}; border-left: 4px solid {color}; border-radius: 4px;">
                        <span style="font-size: 1.2em;">{icon}</span>
                        <div style="flex: 1;">
                            <strong>Attempt {attempt_num}</strong>
                            <div style="font-size: 0.9em; color: #666;">
                                Time: {time_ms:.1f}ms{fallback_text}{error_text}
                            </div>
                        </div>
                    </div>
                    """
                    if i < len(steps) - 1:
                        html_content += """
                        <div style="margin-left: 20px; border-left: 2px dashed #ccc; height: 20px;"></div>
                        """
                
                html_content += "</div>"
                st.markdown(html_content, unsafe_allow_html=True)
    
    # Charts section
    render_section_header("Recovery Analytics", icon="📊", level=2)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Recovery Rate", "Retry Counts", "Failure Mode Distribution", "Recovery Matrix"])
    
    with tab1:
        # Recovery rate chart
        recovery_rate = results.get("recovery_rate", 0.0)
        failed_rate = 1.0 - recovery_rate
        
        fig = go.Figure(data=[
            go.Bar(
                name="Recovered",
                x=["Recovery Rate"],
                y=[recovery_rate],
                marker_color="#28a745",
                text=f"{recovery_rate:.1%}",
                textposition="inside"
            ),
            go.Bar(
                name="Failed",
                x=["Recovery Rate"],
                y=[failed_rate],
                marker_color="#dc3545",
                text=f"{failed_rate:.1%}",
                textposition="inside"
            )
        ])
        fig.update_layout(
            barmode="stack",
            yaxis_title="Rate",
            yaxis=dict(range=[0, 1]),
            height=400,
            title=None,
            margin=dict(l=60, r=60, t=40, b=60),
            showlegend=True
        )
        st.markdown("#### Overall Recovery Rate")
        st.plotly_chart(fig, width="stretch")
        
        # Recovery rate by error type
        recovery_matrix = results.get("recovery_matrix", [])
        if recovery_matrix:
            matrix_df = pd.DataFrame(recovery_matrix)
            recovery_by_type = matrix_df.groupby("error_type")["recovered"].mean().reset_index()
            recovery_by_type.columns = ["Error Type", "Recovery Rate"]
            
            fig = px.bar(
                recovery_by_type,
                x="Error Type",
                y="Recovery Rate",
                color="Recovery Rate",
                color_continuous_scale="RdYlGn",
                text="Recovery Rate"
            )
            fig.update_traces(texttemplate="%{text:.1%}", textposition="inside")
            fig.update_layout(
                height=400,
                yaxis=dict(range=[0, 1]),
                title=None,
                margin=dict(l=60, r=60, t=40, b=60)
            )
            st.markdown("#### Recovery Rate by Error Type")
            st.plotly_chart(fig, width="stretch")
    
    with tab2:
        # Retry counts distribution
        retry_counts = results.get("retry_counts", {})
        if retry_counts:
            retry_df = pd.DataFrame([
                {"Retries Used": str(k), "Count": v}
                for k, v in retry_counts.items()
            ])
            fig = px.bar(
                retry_df,
                x="Retries Used",
                y="Count",
                color="Count",
                color_continuous_scale="Blues"
            )
            fig.update_layout(
                height=400,
                title=None,
                margin=dict(l=60, r=60, t=40, b=60)
            )
            st.markdown("#### Retry Count Distribution")
            st.plotly_chart(fig, width="stretch")
            
            # Pie chart
            fig = px.pie(
                retry_df,
                values="Count",
                names="Retries Used"
            )
            fig.update_layout(
                height=400,
                title=None,
                margin=dict(l=60, r=60, t=40, b=60)
            )
            st.markdown("#### Retry Usage Distribution")
            st.plotly_chart(fig, width="stretch")
        else:
            from components.ui_helpers import render_empty_state
            render_empty_state("No Retry Data Available", "📊", "Run error recovery suite to see retry metrics")
    
    with tab3:
        # Failure mode distribution
        failure_modes = results.get("failure_modes", {})
        if failure_modes:
            failure_df = pd.DataFrame([
                {"Failure Mode": k, "Count": v}
                for k, v in failure_modes.items()
            ])
            fig = px.bar(
                failure_df,
                x="Failure Mode",
                y="Count",
                color="Count",
                color_continuous_scale="Reds"
            )
            fig.update_layout(
                height=400,
                title=None,
                margin=dict(l=60, r=60, t=40, b=60)
            )
            st.markdown("#### Failure Mode Distribution")
            st.plotly_chart(fig, width="stretch")
            
            # Pie chart
            fig = px.pie(
                failure_df,
                values="Count",
                names="Failure Mode"
            )
            fig.update_layout(
                height=400,
                title=None,
                margin=dict(l=60, r=60, t=40, b=60)
            )
            st.markdown("#### Failure Modes")
            st.plotly_chart(fig, width="stretch")
        else:
            from components.ui_helpers import render_empty_state
            render_empty_state("No Failure Mode Data Available", "📊", "Run error recovery suite to see failure mode distribution")
    
    with tab4:
        # Recovery matrix table
        recovery_matrix = results.get("recovery_matrix", [])
        if recovery_matrix:
            matrix_df = pd.DataFrame(recovery_matrix)
            
            # Format for display
            display_df = matrix_df.copy()
            display_df["recovered"] = display_df["recovered"].apply(lambda x: "✅ Yes" if x else "❌ No")
            display_df["fallback_used"] = display_df["fallback_used"].apply(lambda x: "✅ Yes" if x else "❌ No")
            display_df["recovery_time_ms"] = display_df["recovery_time_ms"].apply(lambda x: f"{x:.1f}ms")
            
            display_df.columns = ["Error Type", "Recovered", "Retries Used", "Fallback Used", "Recovery Time"]
            st.dataframe(display_df, width="stretch", hide_index=True)
        else:
            st.info("No recovery matrix data available.")
    
    # Detailed results table
    render_section_header("Detailed Recovery Results", icon="📋", level=2)
    
    if raw_runs:
        # Create detailed table
        table_data = []
        for run in raw_runs:
            table_data.append({
                "Error Type": run.get("error_type", "unknown"),
                "Recovered": "✅ Yes" if run.get("recovered", False) else "❌ No",
                "Fallback Used": "✅ Yes" if run.get("fallback_used", False) else "❌ No",
                "Recovery Time (ms)": f"{run.get('recovery_time_ms', 0):.1f}",
                "Retries Used": run.get("retries_used", 0),
                "Failure Mode": run.get("failure_mode", "unknown"),
                "Fallback Quality": f"{run.get('fallback_quality', 0.0):.1%}"
            })
        
        results_df = pd.DataFrame(table_data)
        st.dataframe(results_df, width="stretch", hide_index=True)
        
        # Expandable detailed view
        with st.expander("View Raw Recovery Data"):
            for i, run in enumerate(raw_runs):
                st.markdown(f"### Error Type: {run.get('error_type', 'unknown')}")
                st.json(run)
    else:
        st.info("No detailed recovery data available.")
