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
from components.demo_data import get_demo_audit_statistics, get_demo_feedback_stats, should_use_demo_data
from components.ui_helpers import apply_light_theme_css

# Page configuration
st.set_page_config(
    page_title="Compliance Assistant",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"  # Show chat by default
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

# Apply centralized light theme CSS
apply_light_theme_css()

# Home page-specific styling (enhanced headers, feature cards, etc.)
st.markdown("""
<style>
    /* Main container with better padding for Home page */
    .main {
        padding: 1rem 2rem 2rem 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* Much larger, bolder headers for Home page - DARKER for better contrast */
    h1 {
        font-size: 4rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        text-align: center;
        margin-bottom: 0.75rem !important;
        line-height: 1.1 !important;
    }
    
    h2 {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #1e40af !important;
        margin-top: 2.5rem !important;
        margin-bottom: 1.5rem !important;
        text-align: center;
    }
    
    h3 {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #2563eb !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* Bigger body text for Home page - DARKER for readability */
    p, li, div {
        font-size: 1.25rem !important;
        line-height: 1.7 !important;
        color: #1e293b !important;
    }
    
    /* Feature cards - Home page specific */
    .feature-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        padding: 2.5rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        border: 3px solid #7dd3fc;
        transition: all 0.3s;
        min-height: 280px;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.15);
        border-color: #3b82f6;
    }
    
    .feature-card h3 {
        font-size: 2.25rem !important;
        font-weight: 800 !important;
        margin-bottom: 1.25rem !important;
        color: #0f172a !important;
        text-align: center;
    }
    
    .feature-card p {
        font-size: 1.35rem !important;
        color: #1e40af !important;
        margin-bottom: 1.25rem !important;
        font-weight: 500;
        text-align: center;
    }
    
    .feature-card ul {
        font-size: 1.2rem !important;
        color: #1e293b !important;
        list-style-position: inside;
    }
    
    .feature-card ul li {
        font-size: 1.2rem !important;
        padding: 0.5rem 0;
        color: #1e293b !important;
    }
    
    /* Enhanced button styling for Home page */
    .stButton button {
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        padding: 1.25rem 2.5rem !important;
        border-radius: 15px !important;
        transition: all 0.3s !important;
        text-transform: none !important;
        box-shadow: 0 6px 12px rgba(59, 130, 246, 0.3) !important;
    }
    
    .stButton button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 10px 20px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* Enhanced alerts for Home page */
    .stAlert {
        font-size: 1.3rem !important;
        padding: 1.5rem !important;
        border-radius: 15px !important;
        margin: 1.5rem 0 !important;
    }
    
    /* Enhanced metrics for Home page */
    .stMetric {
        background-color: #f8fafc !important;
        padding: 2rem !important;
        border-radius: 15px !important;
        border: 3px solid #cbd5e1 !important;
    }
    
    .stMetric label {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        color: #0f172a !important;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
    }
</style>
""", unsafe_allow_html=True)

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
    with st.container():
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 2.5rem; border-radius: 15px; margin-bottom: 2rem; box-shadow: 0 8px 16px rgba(0,0,0,0.15);'>
            <h2 style='color: white; margin-top: 0; font-size: 2.5rem;'>👋 Welcome! First Time Here?</h2>
            <p style='font-size: 1.3rem; margin-bottom: 2rem; line-height: 1.6;'>
                This AI assistant helps you make smart compliance decisions. Here's how to get started:
            </p>
            <div style='background: rgba(255,255,255,0.15); padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;'>
                <ol style='font-size: 1.2rem; line-height: 2.2; margin: 0; padding-left: 1.5rem;'>
                    <li style='margin-bottom: 0.75rem;'><strong>Click "Check One Task"</strong> below to analyze a compliance question</li>
                    <li style='margin-bottom: 0.75rem;'><strong>Fill out the form</strong> with your company and task details (or use "Load Example" for a demo)</li>
                    <li style='margin-bottom: 0.75rem;'><strong>Get instant guidance</strong> with a clear decision, risk assessment, and action plan</li>
            </ol>
            </div>
            <p style='font-size: 1.1rem; margin-top: 1.5rem; margin-bottom: 0; background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px;'>
                💡 <strong>Pro Tip:</strong> The AI learns from your feedback. After each analysis, you can confirm or correct the decision to help it improve!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("✅ Got it!", type="primary", width="stretch"):
                st.session_state.has_seen_onboarding = True
                st.rerun()
        with col2:
            if st.button("📖 Show me a quick tour", width="stretch"):
                st.session_state.show_tour = True
                st.session_state.tour_step = 0
                st.rerun()

# Onboarding tour
if st.session_state.get("show_tour", False):
    tour_step = st.session_state.get("tour_step", 0)
    
    tour_steps = [
        {
            "title": "🎯 Step 1: Analyze a Task",
            "content": "Click 'Check One Task' to get instant guidance on any compliance question. The AI will tell you if you can proceed, need approval, or should escalate.",
            "action": "Go to Analyze Task page"
        },
        {
            "title": "📋 Step 2: Generate Calendar",
            "content": "Use 'Compliance Calendar' to get a complete list of compliance tasks for your organization, prioritized by deadline and risk.",
            "action": "Go to Compliance Calendar page"
        },
        {
            "title": "📊 Step 3: Review History",
            "content": "Check 'Audit Trail' to see all past decisions, filter by date/risk/decision type, and export for your records.",
            "action": "Go to Audit Trail page"
        },
        {
            "title": "💬 Step 4: Ask Questions",
            "content": "Use the chat assistant in the sidebar on any page to ask questions about compliance, decisions, or how to use features.",
            "action": "Try the chat assistant"
        }
    ]
    
    if tour_step < len(tour_steps):
        current_step = tour_steps[tour_step]
        
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 2rem; border-radius: 15px; margin: 2rem 0;'>
            <h2 style='color: white; margin-top: 0;'>{}</h2>
            <p style='font-size: 1.2rem; color: white; margin-bottom: 1.5rem;'>{}</p>
            <p style='font-size: 1rem; color: white; font-weight: 600;'>{}</p>
        </div>
        """.format(current_step["title"], current_step["content"], current_step["action"]), unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if tour_step > 0:
                if st.button("⬅️ Previous", width="stretch"):
                    st.session_state.tour_step = tour_step - 1
                    st.rerun()
        with col2:
            if st.button("✅ Got it, skip tour", width="stretch", type="primary"):
                st.session_state.show_tour = False
                st.session_state.has_seen_onboarding = True
                st.session_state.tour_step = 0
                st.rerun()
        with col3:
            if tour_step < len(tour_steps) - 1:
                if st.button("Next ➡️", width="stretch", type="primary"):
                    st.session_state.tour_step = tour_step + 1
                    st.rerun()
            else:
                if st.button("✅ Finish Tour", width="stretch", type="primary"):
                    st.session_state.show_tour = False
                    st.session_state.has_seen_onboarding = True
                    st.session_state.tour_step = 0
                    st.rerun()
        
        st.caption(f"Step {tour_step + 1} of {len(tour_steps)}")

# Onboarding panel
with st.container():
    st.markdown("### 🚀 Get Started")
    ob_col1, ob_col2 = st.columns([2, 1])
    with ob_col1:
        st.markdown("""
        <div style='background-color: #f0f9ff; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #3b82f6; margin-bottom: 1rem;'>
            <p style='font-size: 1.2rem; color: #1e40af; margin: 0 0 1rem 0; font-weight: 600;'>
                🎯 Quick Start Options
            </p>
            <p style='font-size: 1.1rem; color: #1e293b; margin: 0;'>
                <strong>Option 1:</strong> Analyze a single task to get instant guidance on whether you can proceed independently, need approval, or should escalate to an expert.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎯 Start with a sample task", key="demo_task_btn", width="stretch", type="primary"):
            # Provide a demo hint for Analyze Task page (non-invasive)
            st.session_state["demo_task_text"] = "Review privacy policy updates for a new feature rollout across US/EU."
            st.switch_page("pages/1_Analyze_Task.py")
    with ob_col2:
        st.markdown("""
        <div style='background-color: #fef3c7; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #f59e0b; margin-bottom: 1rem;'>
            <p style='font-size: 1.1rem; color: #92400e; margin: 0; font-weight: 600;'>
                📋 Option 2
            </p>
            <p style='font-size: 1rem; color: #1e293b; margin-top: 0.5rem; margin-bottom: 0;'>
                Generate a complete compliance calendar with all tasks prioritized by deadline and risk level.
            </p>
        </div>
        """, unsafe_allow_html=True)

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

# Quick Start Guide
st.markdown("""
<div class="feature-card">
    <h2>🚀 Quick Start Guide</h2>
    <p style="font-size: 1.3rem; margin-bottom: 1.5rem;">Get started in 3 simple steps:</p>
    <ol style="font-size: 1.2rem; line-height: 2;">
        <li><strong>Click "Check One Task"</strong> below to analyze a compliance question</li>
        <li><strong>Fill out the form</strong> with your company and task details (or use "Load Example")</li>
        <li><strong>Get instant guidance</strong> with a clear decision, risk assessment, and action plan</li>
    </ol>
    <p style="font-size: 1.1rem; margin-top: 1.5rem; color: #64748b;">
        💾 All decisions are automatically saved. You can review them anytime in "Review History".
    </p>
</div>
""", unsafe_allow_html=True)

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
with st.expander("🔧 Advanced Features & Analytics", expanded=False):
    st.markdown("""
    <div style='padding: 1rem;'>
        <h3 style='color: #1e40af;'>📊 Agent Insights Dashboard</h3>
        <p style='font-size: 1.1rem; color: #64748b; margin-bottom: 1rem;'>
            Visualize agent performance, patterns, and learning progress with interactive charts and analytics.
        </p>
        <p style='font-size: 0.95rem; color: #94a3b8; margin-bottom: 1.5rem;'>
            <em>Note: This feature is most useful after you've made several decisions.</em>
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 View Insights Dashboard", key="agent_insights_btn", width="stretch", use_container_width=True):
            st.switch_page("pages/4_Agent_Insights.py")

    with col2:
        if st.button("🤖 Advanced Agentic Analysis", key="agentic_analysis_btn", width="stretch", use_container_width=True):
            st.switch_page("pages/5_Agentic_Analysis.py")
    
    st.caption("💡 These advanced features use experimental AI reasoning. For most users, 'Check One Task' provides everything you need.")

# Agent Activity Metrics
st.markdown("---")
st.markdown("<h2>📊 Your Activity Summary</h2>", unsafe_allow_html=True)

# Better empty state messaging
if not is_authenticated():
    st.info("""
    👋 **Welcome!** 
    
    Sign in to see your decision history and activity metrics. Once you start analyzing tasks, you'll see:
    - Total decisions made
    - Autonomy rate (how often you can proceed independently)
    - AI confidence trends
    - Feedback accuracy
    """)
else:
    st.caption("💡 These metrics help you understand how the AI is assisting with your compliance decisions.")

# Agent activity metrics - only load if authenticated
stats = None
is_demo_data = False

if is_authenticated():
    try:
        with st.spinner("Loading statistics..."):
            stats_resp = api.get("/api/v1/audit/statistics")
        
        if stats_resp.success and isinstance(stats_resp.data, dict):
            stats = stats_resp.data
            # Check if we should use demo data (empty database)
            if should_use_demo_data(stats_resp, None) or stats.get("total_decisions", 0) == 0:
                stats = get_demo_audit_statistics()
                is_demo_data = True
        else:
            # Use demo data on error
            stats = get_demo_audit_statistics()
            is_demo_data = True
    except Exception as e:
        # Use demo data on exception
        stats = get_demo_audit_statistics()
        is_demo_data = True

if stats:
    total = stats.get("total_decisions", 0)
    
    # Show demo data notice if applicable
    if is_demo_data:
        st.info("""
        📊 **Getting Started**
        
        These are sample metrics to show you what the dashboard looks like. 
        **Start analyzing tasks** to see your real data here!
        
        👉 Click "Check One Task" above to get started.
        """)
    
    # Decision Performance Metrics
    if total > 0 or is_demo_data:
        st.markdown("### Decision Performance")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Decisions Made", f"{total:,}", help="Total compliance questions analyzed by the AI agent")
        
        with col2:
            autonomous = stats.get("autonomous_count", 0)
            autonomy_pct = (autonomous/total*100) if total > 0 else 0
            st.metric("✅ Handled Independently", f"{autonomous:,}", 
                     delta=f"{autonomy_pct:.0f}% autonomy",
                     help="Tasks you completed on your own without needing expert review. Higher is better for efficiency!")
        
        with col3:
            avg_confidence = stats.get("avg_confidence", 0) * 100
            st.metric("Agent Confidence", f"{avg_confidence:.0f}%", 
                     help="How sure the AI is about its recommendations. Higher confidence means more reliable guidance.")
        
        with col4:
            high_priority = stats.get("high_risk_count", 0)
            st.metric("🚨 High Risk Items", f"{high_priority:,}",
                     help="Audit trail entries with HIGH risk level. Note: This differs from 'High Priority' in Compliance Calendar which considers deadlines.")
        
        # Agent Learning Status
        st.markdown("### 🧠 Agent Learning Status")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if total > 0:
                st.metric("Scenarios Analyzed", f"{total:,} scenarios", 
                         help="The AI learns from each situation it reviews. More scenarios = smarter recommendations.")
            else:
                st.metric("Scenarios Analyzed", "No data yet", 
                         help="Start analyzing tasks to see scenarios here")
        
        with col2:
            st.metric("Status", "🟢 Active", help="The AI agent is running and continuously learning from your organization's compliance patterns.")
        
        with col3:
            escalation_count = stats.get("escalate_count", 0)
            escalation_rate = (escalation_count / total * 100) if total > 0 else 0
            st.metric("Careful Decision Rate", f"{escalation_rate:.0f}%",
                     help="When uncertain, the AI recommends expert review. This shows the AI is being cautious to protect you.")
else:
    if is_authenticated():
        st.info("""
        💡 **Getting Started**
        
        Agent activity metrics will appear here once you start analyzing tasks:
        1. Go to **"Check a Task"** to analyze your first compliance task
        2. Return here to see your metrics and insights
        3. Metrics update automatically as you use the system
        """)

# Human Feedback & AI Accuracy
st.markdown("### 👤 Human Feedback & AI Accuracy")

# Human Feedback & AI Accuracy - only load if authenticated
feedback_stats = None
is_feedback_demo = False

if is_authenticated():
    try:
        with st.spinner("Loading feedback statistics..."):
            feedback_resp = api.get("/api/v1/feedback/stats")
        
        if feedback_resp.success and isinstance(feedback_resp.data, dict):
            feedback_stats = feedback_resp.data
            # Check if we should use demo data
            if should_use_demo_data(feedback_resp, None) or feedback_stats.get('total_feedback_count', 0) == 0:
                feedback_stats = get_demo_feedback_stats()
                is_feedback_demo = True
        else:
            # Use demo data on error
            feedback_stats = get_demo_feedback_stats()
            is_feedback_demo = True
    except Exception as e:
        # Use demo data on exception
        feedback_stats = get_demo_feedback_stats()
        is_feedback_demo = True
else:
    feedback_stats = None

if feedback_stats:
    total_feedback = feedback_stats.get('total_feedback_count', 0)
    
    if total_feedback > 0:
        # Show demo notice if applicable
        if is_feedback_demo:
            st.info("📊 **Demo Data**: Showing sample feedback metrics. Real metrics will appear once you submit feedback on decisions.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            accuracy = feedback_stats.get('accuracy_percent', 0)
            st.metric("AI Accuracy", f"{accuracy:.1f}%",
                     help="When you review AI decisions, this shows how often they were correct. Higher accuracy = more trustworthy AI.")
        
        with col2:
            st.metric("Feedback Received", f"{total_feedback:,}",
                     help="Your feedback helps the AI learn! Each review makes future recommendations better.")
        
        with col3:
            agreement = feedback_stats.get('agreement_count', 0)
            override = feedback_stats.get('override_count', 0)
            agreement_rate = (agreement/(agreement+override)*100) if (agreement+override) > 0 else 0
            st.metric("Agreement Rate", f"{agreement_rate:.1f}%",
                     help="How often you agree with the AI's recommendations. High agreement means the AI understands your needs.")
    else:
        st.info("""
        💬 **No Feedback Yet**
        
        Help improve the AI by providing feedback on decisions! After each task analysis, use the "Human Feedback" section to confirm or correct the AI's decision.
        
        Your feedback creates a learning loop that makes the AI smarter over time.
        """)
else:
    if is_authenticated():
        st.info("""
        💬 **No Feedback Yet**
        
        Help improve the AI by providing feedback on decisions! After each task analysis, use the "Human Feedback" section to confirm or correct the AI's decision.
        
        Your feedback creates a learning loop that makes the AI smarter over time.
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 2rem; font-size: 1.1rem;'>
    <p style='font-weight: 600;'>Compliance Assistant v1.0</p>
    <p>Instant guidance for compliance decisions</p>
    <p>Questions? Contact your compliance team or IT support</p>
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
