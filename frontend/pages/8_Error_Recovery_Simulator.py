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
st.markdown('<div class="simulator-header"><h1>🔧 Error Recovery Simulator</h1><p>Simulate failures and test error recovery capabilities</p></div>', unsafe_allow_html=True)

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
        use_entity_context = st.checkbox("Include Entity Context")
        
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

# Run simulation button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_button = st.button("🚀 Run Failure Simulation", type="primary", width="stretch")

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
    
    # Summary metrics
    st.markdown("## 📊 Simulation Summary")
    
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
        failure_count = len(failures) if failures else 0
        st.metric("Failures Injected", failure_count if failure_count > 0 else "N/A",
                 help="Number of failures injected during simulation")
    
    with col4:
        recovery_attempts = results.get("recovery_attempts", [])
        recovery_count = len(recovery_attempts) if recovery_attempts else 0
        st.metric("Recovery Attempts", recovery_count if recovery_count > 0 else "N/A",
                 help="Number of recovery attempts made")
    
    # Failure statistics
    failure_stats = results.get("failure_statistics", {})
    taxonomy_stats = results.get("taxonomy_statistics", {})
    
    st.markdown("## 📈 Failure Analysis")
    
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
                title="Failure Type Distribution",
                color="Count",
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No failures recorded.")
    
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
                title="Recovery Success Distribution",
                color_discrete_map={"Successful": "#28a745", "Failed": "#dc3545"}
            )
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
                names="Category",
                title="Failure Categories"
            )
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
                title="Retry Strategies Used",
                color="Count",
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig, width="stretch")
    
    # Detailed failure list
    st.markdown("## 🔍 Detailed Failures")
    
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

