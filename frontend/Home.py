"""
AI Compliance Assistant - Business Dashboard
=============================================
Get instant guidance on compliance decisions - no training needed!
"""

import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# Add frontend directory to path for imports
frontend_dir = Path(__file__).parent
sys.path.insert(0, str(frontend_dir))

from components.chat_assistant import render_chat_panel
from components.auth_utils import show_login_page, is_authenticated, logout
from components.api_client import APIClient, display_api_error
# Production-ready: No demo data - use real data only
from components.ui_helpers import apply_light_theme_css
from components.theme import apply_home_theme_css

# Page configuration
st.set_page_config(
    page_title="Compliance Assistant",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# AUTHENTICATION - JWT via backend
# ============================================================================
# Top-right logout
hdr_c1, hdr_c2 = st.columns([6, 1])
with hdr_c2:
    if is_authenticated():
        if st.button("Logout", width="stretch"):
            logout()

if not show_login_page():
    st.stop()
# ============================================================================

apply_light_theme_css()
apply_home_theme_css()

# Header with Clear Value Proposition
st.title("🛡️ AI Compliance Assistant")
st.markdown("""
<div style='background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem; border-left: 6px solid #3b82f6;'>
    <h2 style='color: #1e40af; margin-top: 0; font-size: 2rem;'>Get Instant Answers to Your Compliance Questions</h2>
    <p style='font-size: 1.3rem; color: #1e293b; margin: 1rem 0; line-height: 1.6;'>
        <strong>Not sure if you can handle a compliance task yourself?</strong> Our AI analyzes your situation and tells you:
    </p>
    <div style='display: flex; gap: 2rem; margin-top: 1.5rem; flex-wrap: wrap;'>
        <div style='flex: 1; min-width: 200px;'>
            <p style='font-size: 1.1rem; margin: 0.5rem 0;'><strong>✅ Go Ahead</strong> — Handle it yourself</p>
            <p style='font-size: 0.95rem; color: #64748b; margin: 0;'>Low risk, routine tasks</p>
        </div>
        <div style='flex: 1; min-width: 200px;'>
            <p style='font-size: 1.1rem; margin: 0.5rem 0;'><strong>⚠️ Get Approval</strong> — Have someone review</p>
            <p style='font-size: 0.95rem; color: #64748b; margin: 0;'>Moderate risk, needs oversight</p>
        </div>
        <div style='flex: 1; min-width: 200px;'>
            <p style='font-size: 1.1rem; margin: 0.5rem 0;'><strong>🚨 Escalate</strong> — Call an expert</p>
            <p style='font-size: 0.95rem; color: #64748b; margin: 0;'>High risk, requires specialist</p>
        </div>
    </div>
    <p style='font-size: 1.1rem; color: #1e40af; margin-top: 1.5rem; margin-bottom: 0; font-weight: 600;'>
        💡 Every decision includes detailed reasoning, risk assessment, and actionable next steps.
    </p>
</div>
""", unsafe_allow_html=True)

# First-time user detection and onboarding
if "has_seen_onboarding" not in st.session_state:
    st.session_state.has_seen_onboarding = False

if not st.session_state.has_seen_onboarding:
    st.info("""
        👋 **Welcome to the AI Compliance Assistant!**
        
        Complete these three steps to get guidance fast:
        1. Click “Check One Task” to describe what you’re handling.
        2. Fill in the form (use “Load Example” to preview).
        3. Review the AI’s decision, risk view, and recommended next steps.
        
        Tap “Got it!” when you’re ready to explore.
    """)
    if st.button("✅ Got it!", key="onboarding_ok", width="stretch"):
        st.session_state.has_seen_onboarding = True
        st.rerun()

with st.container():
    st.markdown("### 🚀 Get Started")
    ob_col1, ob_col2 = st.columns([2, 1])
    with ob_col1:
        st.markdown("""
        <div style='background-color: #f0f9ff; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #3b82f6;'>
            <p style='font-size: 1.2rem; color: #1e40af; margin: 0 0 1rem 0; font-weight: 600;'>
                🎯 Quick Start
            </p>
            <ol style='padding-left: 1.4rem; line-height: 1.9; font-size: 1.05rem; margin: 0;'>
                <li>Click <strong>Check One Task</strong> to describe the compliance question.</li>
                <li>Fill out the form (or load the example) with your context.</li>
                <li>Review the AI decision, risk level, confidence, and next steps.</li>
            </ol>
            <p style='font-size: 0.95rem; color: #475569; margin-top: 1rem;'>Every decision is saved in the audit trail—you can review it later.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎯 Start with a sample task", key="demo_task_btn", width="stretch", type="primary"):
            st.session_state["demo_task_text"] = "Review privacy policy updates for a new feature rollout across US/EU."
            st.switch_page("pages/1_Analyze_Task.py")
    with ob_col2:
        st.markdown("""
        <div style='background-color: #fef3c7; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #f59e0b;'>
            <p style='font-size: 1.1rem; color: #92400e; margin: 0; font-weight: 600;'>
                📋 Plan All Tasks
            </p>
            <p style='font-size: 1rem; color: #1e293b; margin-top: 0.5rem; margin-bottom: 0;'>
                Generate a compliance calendar that lists every required task, deadlines, frequencies, and priorities.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📋 Generate Calendar", key="option2_calendar_btn", width="stretch", type="secondary"):
            st.switch_page("pages/2_Compliance_Calendar.py")

# Check API connection (health endpoint is unprotected)
api = APIClient()
health = api.health_check()
if health.success:
    st.success("✅ System is ready and connected")
else:
    display_api_error(health)
    test_btn = st.button("🔄 Test Connection Again")
    if test_btn:
        st.rerun()

# Separator
st.markdown("---")

 
# Main action buttons
st.markdown("<h2>Choose What You Need Help With</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="large")
with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>🎯 Check One Task</h3>
        <p>Should I do this myself or get help?</p>
        <ul>
            <li>Answer simple questions</li>
            <li>Get instant guidance</li>
            <li>Know exactly what to do next</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🎯 START HERE →", key="analyze_task_btn", width="stretch", type="primary"):
        st.switch_page("pages/1_Analyze_Task.py")

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>📋 Plan All Tasks</h3>
        <p>Get a complete task list for your company</p>
        <ul>
            <li>See all required tasks</li>
            <li>Know when things are due</li>
            <li>Understand priority levels</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    if st.button("📋 CREATE TASK LIST →", key="compliance_calendar_btn", width="stretch", type="primary"):
        st.switch_page("pages/2_Compliance_Calendar.py")

with col3:
    st.markdown("""
    <div class="feature-card">
        <h3>📊 Review History</h3>
        <p>Look up past decisions and guidance</p>
        <ul>
            <li>Search by date or topic</li>
            <li>Download for your records</li>
            <li>Review previous guidance</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    if st.button("📊 VIEW HISTORY →", key="audit_trail_btn", width="stretch", type="primary"):
        st.switch_page("pages/3_Audit_Trail.py")

# Advanced Features (Collapsible)
st.markdown("### 🔧 Advanced Tools")
col_adv1, col_adv2 = st.columns(2)
with col_adv1:
    if st.button("📊 View Insights Dashboard", key="agent_insights_btn", width="stretch"):
        st.switch_page("pages/4_Agent_Insights.py")
with col_adv2:
    if st.button("🤖 Advanced Agentic Analysis", key="agentic_analysis_btn", width="stretch"):
        st.switch_page("pages/5_Agentic_Analysis.py")
st.caption("💡 These advanced features are optional—only dive in once you want deeper analytics.")

# Agent Activity Metrics
st.markdown("---")
st.markdown("<h2>📊 Your Activity Summary</h2>", unsafe_allow_html=True)

if not is_authenticated():
    st.info("""
    👋 **Welcome!**
    
    Sign in to see your decision history and activity metrics. Once you start analyzing tasks, you'll see:
    - Total decisions analyzed
    - Autonomy rate (how often you can proceed independently)
    - AI confidence insights
    - Feedback accuracy
    """)
else:
    st.caption("💡 These metrics help you understand how the AI is assisting with your compliance decisions.")

# Agent activity metrics - only load if authenticated
stats = None
if is_authenticated():
    try:
        with st.spinner("Loading statistics..."):
            stats_resp = api.get("/api/v1/audit/statistics")
        if stats_resp.success and isinstance(stats_resp.data, dict):
            stats = stats_resp.data
    except Exception:
        stats = None

status_text = "🟢 Active" if health.success else "🔴 Offline"
status_help = "Health check passed" if health.success else "Health check failed. Please verify backend connectivity."

if stats and stats.get("total_decisions", 0) > 0:
    total = stats.get("total_decisions", 0)
    autonomous = stats.get("autonomous_count", 0)
    autonomy_pct = (autonomous / total * 100) if total > 0 else 0
    escalation_count = stats.get("escalate_count", 0)
    escalation_rate = (escalation_count / total * 100) if total > 0 else 0
    high_priority = stats.get("high_risk_count", 0)
    avg_confidence = stats.get("avg_confidence", 0) or 0
    avg_confidence_pct = avg_confidence * 100 if isinstance(avg_confidence, (int, float)) else 0

    st.markdown("### Decision Performance")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Decisions Made", f"{total:,}", help="Total compliance questions analyzed by the AI agent")
    with col2:
        st.metric("Autonomy Rate", f"{autonomy_pct:.0f}%", help="Share of tasks handled without needing expert review.")
    with col3:
        st.metric("Agent Confidence", f"{avg_confidence_pct:.0f}%", help="How confident the AI is about its recommendations.")

    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("Escalation Rate", f"{escalation_rate:.0f}%", help="When uncertain, the AI escalates to an expert.")
    with col5:
        st.metric("🚨 High Risk Items", f"{high_priority:,}", help="Audit entries flagged as high risk.")
    with col6:
        st.metric("Status", status_text, help=status_help)
else:
    if is_authenticated():
        st.info("""
        💡 **Getting Started**
        
        Agent activity metrics will appear here once you start analyzing tasks:
        1. Go to **"Check One Task"** to analyze your first compliance question
        2. Return here to see your metrics and insights
        3. Metrics update automatically as you use the system
        """)

# Human Feedback & AI Accuracy
st.markdown("### 👤 Human Feedback & AI Accuracy")

feedback_stats = None
if is_authenticated():
    try:
        with st.spinner("Loading feedback statistics..."):
            feedback_resp = api.get("/api/v1/feedback/stats")
        if feedback_resp.success and isinstance(feedback_resp.data, dict):
            feedback_stats = feedback_resp.data
    except Exception:
        feedback_stats = None

if feedback_stats and feedback_stats.get('total_feedback_count', 0) > 0:
    total_feedback = feedback_stats.get('total_feedback_count', 0)
    accuracy = feedback_stats.get('accuracy_percent', 0)
    agreement = feedback_stats.get('agreement_count', 0)
    override = feedback_stats.get('override_count', 0)
    agreement_rate = (agreement / (agreement + override) * 100) if (agreement + override) > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("AI Accuracy", f"{accuracy:.1f}%",
                 help="How often your feedback confirmed the AI decision.")
    with col2:
        st.metric("Feedback Received", f"{total_feedback:,}",
                 help="Every review makes the AI smarter.")
    with col3:
        st.metric("Agreement Rate", f"{agreement_rate:.1f}%",
                 help="Percentage of reviews that agreed with the AI recommendation.")
else:
    st.info("""
    💬 **No Feedback Yet**
    
    Help improve the AI by providing feedback on decisions! After each task analysis, use the "Human Feedback" section to confirm or correct the AI's decision.
    
    Your guidance creates a learning loop that makes the AI smarter over time.
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #94a3b8; padding: 0.5rem; font-size: 0.95rem;'>
    Compliance Assistant v1.0 · Instant guidance for compliance decisions · Need help? Contact your compliance or IT team.
</div>
""", unsafe_allow_html=True)

# Chat Assistant in Sidebar
with st.sidebar:
    st.markdown("---")
    st.markdown("## 💬 AI Chat Assistant")
    st.caption("Ask questions anytime")
    
    # Render chat panel
    render_chat_panel(context_data={
        "page": "Home",
        "entity_name": "System Overview",
        "task_description": "Ask general questions about the compliance assistant"
    })
