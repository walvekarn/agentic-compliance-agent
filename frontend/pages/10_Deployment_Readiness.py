"""
Deployment Readiness Checker
============================
Comprehensive system health check for deployment readiness.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

# Force light theme for all Plotly charts
pio.templates.default = "plotly_white"

# Add frontend directory to path
frontend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(frontend_dir))

from components.auth_utils import require_auth, show_logout_button
from components.session_manager import SessionManager
from components.api_client import APIClient, display_api_error

# Page config
st.set_page_config(page_title="Deployment Readiness", page_icon="✅", layout="wide")

# Apply light theme CSS
from components.ui_helpers import apply_light_theme_css, render_page_header, render_section_header
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
.readiness-header {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
}
.check-card {
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}
.check-pass {
    border-left: 4px solid #28a745;
}
.check-fail {
    border-left: 4px solid #dc3545;
}
.check-warning {
    border-left: 4px solid #ffc107;
}
.status-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    display: inline-block;
}
.status-pass {
    background-color: #28a745;
    color: white;
}
.status-fail {
    background-color: #dc3545;
    color: white;
}
.status-warning {
    background-color: #ffc107;
    color: #000;
}
</style>
""", unsafe_allow_html=True)

# Header
render_page_header(
    title="Deployment Readiness Checker",
    icon="✅",
    description="Comprehensive system health validation"
)

# Feature explanation
st.markdown("""
<div style='background-color: #d1f2eb; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #28a745; margin-bottom: 2rem;'>
    <h3 style='margin-top: 0; color: #155724;'>❓ What is This Tool?</h3>
    <p style='color: #1e293b; margin-bottom: 0.5rem;'><strong>Purpose:</strong> Validate that your system is properly configured and ready for production deployment. Checks all critical components and configurations.</p>
    <p style='color: #1e293b; margin-bottom: 0.5rem;'><strong>When to Use:</strong> Before deploying to production, after major configuration changes, or when troubleshooting deployment issues. Run this before going live.</p>
    <p style='color: #1e293b; margin-bottom: 0.5rem;'><strong>What It Does:</strong> Performs comprehensive health checks on database connectivity, API endpoints, authentication, OpenAI configuration, error handling, and system dependencies.</p>
    <p style='color: #1e293b; margin-bottom: 0.5rem;'><strong>Expected Output:</strong> A detailed report showing which checks passed, which failed, and which have warnings. Includes remediation steps for any issues found.</p>
    <p style='color: #1e293b; margin-bottom: 0;'><strong>Time Required:</strong> 10-30 seconds. Quick validation check that runs automatically.</p>
</div>
""", unsafe_allow_html=True)

# Session state
if "health_check_results" not in st.session_state:
    st.session_state.health_check_results = None
if "health_check_running" not in st.session_state:
    st.session_state.health_check_running = False

# Run health check button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_button = st.button("🔍 Run Health Check", type="primary", width="stretch")

if run_button or st.session_state.health_check_running:
    if not st.session_state.health_check_running:
        st.session_state.health_check_running = True
        st.session_state.health_check_results = None
    
    # Show progress
    with st.spinner("Running comprehensive health check... This may take a few seconds."):
        response = api_client.get("/api/v1/agentic/health/full")
    
    st.session_state.health_check_running = False
    
    if response and response.success:
        # Handle both direct data and nested response formats
        if isinstance(response.data, dict):
            st.session_state.health_check_results = response.data
        elif hasattr(response, 'data') and response.data:
            st.session_state.health_check_results = response.data
        else:
            st.session_state.health_check_results = None
            st.warning("⚠️ Health check completed but no data returned. Check backend logs.")
        
        if st.session_state.health_check_results:
            st.success("✅ Health check completed!")
    else:
        if response:
            display_api_error(response)
        else:
            st.error("❌ **Error**: No response from health check endpoint. Check that the backend is running.")
        st.session_state.health_check_results = None

# Display results
if st.session_state.health_check_results:
    results = st.session_state.health_check_results
    summary = results.get("summary", {})
    overall_status = results.get("overall_status", "unknown")
    readiness_score = results.get("readiness_score")
    readiness_components = results.get("readiness_components", {})
    details = results.get("details", {})
    
    # Overall status badge
    status_colors = {
        "pass": "#28a745",
        "fail": "#dc3545",
        "warning": "#ffc107"
    }
    
    # Readiness score gauge chart
    render_section_header("Deployment Readiness Score", icon="🎯", level=2)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if readiness_score is not None:
            # Determine readiness level and color
            if readiness_score >= 0.9:
                level = "🟢 Ready"
                color = "#28a745"
            elif readiness_score >= 0.7:
                level = "🟡 Needs Review"
                color = "#ffc107"
            else:
                level = "🔴 Failing"
                color = "#dc3545"
            
            # Create gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=readiness_score * 100,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"Readiness Score<br>{level}", 'font': {'size': 20}},
                delta={'reference': 90, 'position': "top"},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': color},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 70], 'color': "#ffe6e6"},
                        {'range': [70, 90], 'color': "#fff3cd"},
                        {'range': [90, 100], 'color': "#e6ffe6"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig.update_layout(height=350)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Readiness score not available. Run health check to compute.")
    
    with col2:
        st.markdown(f"""
        <div style="margin-top: 50px;">
            <h3 style="color: {status_colors.get(overall_status, '#6c757d')};">
                Overall Status: {overall_status.upper()}
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        if readiness_score is not None:
            st.metric("Readiness Score", f"{readiness_score:.1%}")
        
        # Component status badges
        if readiness_components:
            st.markdown("### Component Status")
            for component_name, component_data in readiness_components.items():
                status = component_data.get("status", "unknown")
                score = component_data.get("score", 0.0)
                
                if status == "pass":
                    badge = "🟢"
                elif status == "warning":
                    badge = "🟡"
                else:
                    badge = "🔴"
                
                st.markdown(f"{badge} **{component_name.replace('_', ' ').title()}**: {score:.1%}")
    
    # Component breakdown bar chart
    if readiness_components:
        render_section_header("Component Breakdown", icon="📊", level=2)
        
        component_df = pd.DataFrame([
            {
                "Component": k.replace("_", " ").title(),
                "Score": v.get("score", 0.0) * 100,
                "Weighted Score": v.get("weighted_score", 0.0) * 100,
                "Weight": v.get("weight", 0.0) * 100,
                "Status": v.get("status", "unknown")
            }
            for k, v in readiness_components.items()
        ])
        
        # Color map for status
        color_map = {
            "pass": "#28a745",
            "warning": "#ffc107",
            "fail": "#dc3545",
            "unknown": "#6c757d"
        }
        component_df["Color"] = component_df["Status"].map(color_map)
        
        # Bar chart
        fig = px.bar(
            component_df,
            x="Component",
            y="Score",
            color="Component",
            color_discrete_map=dict(zip(component_df["Component"], component_df["Color"])),
            text="Score"
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="inside")
        fig.update_layout(
            height=400,
            yaxis=dict(range=[0, 100], title="Score (%)"),
            title=None,
            margin=dict(l=60, r=60, t=40, b=60)
        )
        st.markdown("#### Component Health Scores")
        st.plotly_chart(fig, width="stretch")
        
        # Component details table
        st.markdown("### Component Details")
        display_df = component_df[["Component", "Score", "Weight", "Status"]].copy()
        display_df["Score"] = display_df["Score"].apply(lambda x: f"{x:.1f}%")
        display_df["Weight"] = display_df["Weight"].apply(lambda x: f"{x:.1f}%")
        display_df["Status"] = display_df["Status"].apply(
            lambda s: "🟢 Pass" if s == "pass" else ("🟡 Warning" if s == "warning" else "🔴 Fail")
        )
        st.dataframe(display_df, width="stretch", hide_index=True)
    
    # Summary metrics
    render_section_header("Health Check Summary", icon="📊", level=2)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Checks", summary.get("total_checks", 0))
    
    with col2:
        passed = summary.get("passed", 0)
        st.metric("Passed", passed, delta=None)
    
    with col3:
        failed = summary.get("failed", 0)
        st.metric("Failed", failed, delta=None, delta_color="inverse")
    
    with col4:
        warnings = summary.get("warnings", 0)
        st.metric("Warnings", warnings, delta=None)
    
    # Pass rate
    pass_rate = summary.get("pass_rate", 0)
    st.progress(pass_rate)
    st.caption(f"Pass Rate: {pass_rate:.1%}")
    
    # Detailed tables section
    render_section_header("Detailed Readiness Reports", icon="📋", level=2)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Health Checks", "Test Suite", "Error Recovery", "All Checks"])
    
    with tab1:
        # Health checks table
        checks = results.get("checks", [])
        if checks:
            health_df = pd.DataFrame([
                {
                    "Check": c.get("check_name", "unknown").replace("_", " ").title(),
                    "Status": "🟢 Pass" if c.get("status") == "pass" else ("🟡 Warning" if c.get("status") == "warning" else "🔴 Fail"),
                    "Message": c.get("message", ""),
                    "Details": str(c.get("details", {}))[:100] + "..." if len(str(c.get("details", {}))) > 100 else str(c.get("details", {}))
                }
                for c in checks
            ])
            st.dataframe(health_df, width="stretch", hide_index=True)
            
            # Expandable details for each check
            for check in checks:
                check_name = check.get("check_name", "unknown")
                status = check.get("status", "unknown")
                message = check.get("message", "")
                check_details = check.get("details", {})
                remediation = check.get("remediation")
                
                # Status badge
                if status == "pass":
                    badge = "🟢"
                elif status == "warning":
                    badge = "🟡"
                else:
                    badge = "🔴"
                
                with st.expander(f"{badge} {check_name.replace('_', ' ').title()}"):
                    st.markdown(f"**Message:** {message}")
                    if check_details:
                        st.json(check_details)
                    if remediation:
                        st.info(f"💡 **Remediation:** {remediation}")
        else:
            st.info("No health check data available.")
    
    with tab2:
        # Test suite metrics table
        test_suite_metrics = details.get("test_suite_metrics", {})
        if test_suite_metrics and test_suite_metrics.get("status") != "unavailable":
            if test_suite_metrics.get("pass_rate") is not None:
                col1, col2, col3 = st.columns(3)
                with col1:
                    pass_rate = test_suite_metrics.get("pass_rate", 0.0)
                    st.metric("Pass Rate", f"{pass_rate:.1%}")
                with col2:
                    total_tests = test_suite_metrics.get("total_tests", 0)
                    st.metric("Total Tests", total_tests)
                with col3:
                    confidence_adequacy = test_suite_metrics.get("confidence_deviations", 0.0)
                    st.metric("Confidence Adequacy", f"{confidence_adequacy:.1%}")
                
                # Test suite results table
                failures = test_suite_metrics.get("failures", [])
                if failures:
                    st.markdown("### Test Failures")
                    failures_df = pd.DataFrame([
                        {
                            "Test": f.get("scenario", {}).get("name", "Unknown"),
                            "Status": "❌ Failed" if not f.get("success", True) else "✅ Passed",
                            "Error": ", ".join(f.get("errors", []))[:100] if f.get("errors") else "None"
                        }
                        for f in failures[:10]  # Show first 10
                    ])
                    st.dataframe(failures_df, width="stretch", hide_index=True)
                else:
                    st.success("✅ No test failures recorded!")
            else:
                st.warning("Test suite metrics not available. Run test suite to get metrics.")
        else:
            st.info("Test suite metrics not available.")
    
    with tab3:
        # Error recovery metrics table
        error_recovery_metrics = details.get("error_recovery_metrics", {})
        if error_recovery_metrics and error_recovery_metrics.get("status") != "unavailable":
            if error_recovery_metrics.get("recovery_rate") is not None:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    recovery_rate = error_recovery_metrics.get("recovery_rate", 0.0)
                    st.metric("Recovery Rate", f"{recovery_rate:.1%}")
                with col2:
                    fallback_quality = error_recovery_metrics.get("fallback_quality", 0.0)
                    st.metric("Fallback Quality", f"{fallback_quality:.1%}")
                with col3:
                    retry_stability = error_recovery_metrics.get("retry_stability", 0.0)
                    st.metric("Retry Stability", f"{retry_stability:.2f}")
                with col4:
                    total_tests = error_recovery_metrics.get("total_tests", 0)
                    st.metric("Total Tests", total_tests)
                
                # Error recovery matrix
                if readiness_components and "error_recovery_health" in readiness_components:
                    recovery_component = readiness_components["error_recovery_health"]
                    if recovery_component.get("metrics"):
                        st.markdown("### Error Recovery Details")
                        with st.expander("View Error Recovery Metrics"):
                            st.json(recovery_component["metrics"])
            else:
                st.warning("Error recovery metrics not available. Run error recovery suite to get metrics.")
        else:
            st.info("Error recovery metrics not available.")
    
    with tab4:
        # All checks with color-coded badges
        checks = results.get("checks", [])
        for check in checks:
            check_name = check.get("check_name", "unknown")
            status = check.get("status", "unknown")
            message = check.get("message", "")
            check_details = check.get("details", {})
            remediation = check.get("remediation")
            
            # Determine badge and color
            if status == "pass":
                badge = "🟢"
                bg_color = "#e6ffe6"
                border_color = "#28a745"
            elif status == "warning":
                badge = "🟡"
                bg_color = "#fff3cd"
                border_color = "#ffc107"
            else:
                badge = "🔴"
                bg_color = "#ffe6e6"
                border_color = "#dc3545"
            
            st.markdown(f"""
            <div style="background-color: {bg_color}; border-left: 4px solid {border_color}; padding: 12px; border-radius: 4px; margin-bottom: 10px;">
                <h4>{badge} {check_name.replace('_', ' ').title()} - <span style="text-transform: uppercase;">{status}</span></h4>
                <p>{message}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show details if available
            if check_details:
                with st.expander(f"View Details for {check_name}"):
                    st.json(check_details)
            
            # Show remediation if available
            if remediation:
                st.info(f"💡 **Remediation:** {remediation}")
    
    # Remediation steps
    remediation_steps = results.get("remediation_steps", [])
    if remediation_steps:
        st.markdown("## 🔧 Remediation Steps")
        
        for i, step in enumerate(remediation_steps, 1):
            check_name = step.get("check", "unknown")
            remediation = step.get("remediation", "")
            
            st.markdown(f"""
            <div class="check-card check-warning">
                <h4>Step {i}: Fix {check_name.replace('_', ' ').title()}</h4>
                <p>{remediation}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Deployment readiness assessment
    render_section_header("Deployment Readiness Assessment", icon="🚀", level=2)
    
    if overall_status == "pass":
        st.success("""
        ✅ **System is ready for deployment!**
        
        All health checks have passed. The system appears to be properly configured
        and ready for production deployment.
        """)
    elif overall_status == "warning":
        st.warning("""
        ⚠️ **System has warnings but may be deployable**
        
        Some checks produced warnings. Review the issues above and address them
        before deployment if they are critical for your use case.
        """)
    else:
        st.error("""
        ❌ **System is NOT ready for deployment**
        
        One or more critical health checks have failed. Please review the
        remediation steps above and fix all issues before deploying to production.
        """)
    
    # Export results
    render_section_header("Export Results", icon="📥", level=2)
    if st.button("Download Health Check Report"):
        report_json = json.dumps(results, indent=2)
        st.download_button(
            label="Download JSON Report",
            data=report_json,
            file_name=f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

else:
    st.info("👆 Click 'Run Health Check' to perform a comprehensive system health check.")

