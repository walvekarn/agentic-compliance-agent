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

# Add frontend directory to path
frontend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(frontend_dir))

from components.auth_utils import require_auth, show_logout_button
from components.session_manager import SessionManager
from components.api_client import APIClient, display_api_error

# Page config
st.set_page_config(page_title="Deployment Readiness", page_icon="✅", layout="wide")

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
st.markdown('<div class="readiness-header"><h1>✅ Deployment Readiness Checker</h1><p>Comprehensive system health validation</p></div>', unsafe_allow_html=True)

# Session state
if "health_check_results" not in st.session_state:
    st.session_state.health_check_results = None
if "health_check_running" not in st.session_state:
    st.session_state.health_check_running = False

# Run health check button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_button = st.button("🔍 Run Health Check", type="primary", use_container_width=True)

if run_button or st.session_state.health_check_running:
    if not st.session_state.health_check_running:
        st.session_state.health_check_running = True
        st.session_state.health_check_results = None
    
    # Show progress
    with st.spinner("Running comprehensive health check... This may take a few seconds."):
        response = api_client.get("/api/v1/agentic/health/full")
    
    st.session_state.health_check_running = False
    
    if response:
        st.session_state.health_check_results = response.data
        st.success("✅ Health check completed!")
    else:
        display_api_error(response)
        st.session_state.health_check_results = None

# Display results
if st.session_state.health_check_results:
    results = st.session_state.health_check_results
    summary = results.get("summary", {})
    overall_status = results.get("overall_status", "unknown")
    
    # Overall status badge
    status_colors = {
        "pass": "#28a745",
        "fail": "#dc3545",
        "warning": "#ffc107"
    }
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <h2>Overall Status: 
            <span style="color: {status_colors.get(overall_status, '#6c757d')};">
                {overall_status.upper()}
            </span>
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary metrics
    st.markdown("## 📊 Health Check Summary")
    
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
    
    # Individual checks
    st.markdown("## 🔍 Individual Check Results")
    
    checks = results.get("checks", [])
    for check in checks:
        check_name = check.get("check_name", "unknown")
        status = check.get("status", "unknown")
        message = check.get("message", "")
        details = check.get("details", {})
        remediation = check.get("remediation")
        
        # Determine card class
        card_class = f"check-{status}"
        
        # Status badge
        status_badge_class = f"status-{status}"
        status_display = status.upper()
        
        with st.container():
            st.markdown(f"""
            <div class="check-card {card_class}">
                <h3>
                    {check_name.replace('_', ' ').title()}
                    <span class="status-badge {status_badge_class}">{status_display}</span>
                </h3>
                <p><strong>Message:</strong> {message}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show details if available
            if details:
                with st.expander(f"View Details for {check_name}"):
                    st.json(details)
            
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
    st.markdown("## 🚀 Deployment Readiness Assessment")
    
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
    st.markdown("## 📥 Export Results")
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

