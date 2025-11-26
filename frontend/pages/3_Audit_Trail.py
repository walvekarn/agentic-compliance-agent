"""
Audit Trail Page
================
View and filter all past compliance decisions.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import sys
import os
from pathlib import Path

# Add frontend directory to path for imports
frontend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(frontend_dir))

from components.chat_assistant import render_chat_panel
from components.auth_utils import require_auth, show_logout_button
from components.export_utils import render_export_section, render_export_history
from components.api_client import APIClient, display_api_error
from components.constants import API_BASE_URL

st.set_page_config(page_title="Audit Trail", page_icon="📊", layout="wide")

# Apply light theme CSS
from components.ui_helpers import apply_light_theme_css, render_page_header, render_section_header, render_divider, render_plotly_chart
apply_light_theme_css()

# Additional light theme overrides for this page
st.markdown("""
<style>
    /* Force sidebar to be light */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #1e293b !important;
    }
    
    /* Force main content area */
    .main .block-container {
        background-color: #ffffff !important;
    }
    
    /* Ensure all text is readable */
    .stDataFrame,
    .stDataFrame table,
    .stDataFrame th,
    .stDataFrame td {
        background-color: #ffffff !important;
        color: #1e293b !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# AUTHENTICATION CHECK
# ============================================================================
require_auth()
# ============================================================================

# Note: All component styling is now handled by apply_light_theme_css() in ui_helpers.py
# No duplicate CSS needed here - base theme covers all components

api_key_present = bool(os.getenv("OPENAI_API_KEY"))
db_url_present = bool(os.getenv("DATABASE_URL"))
if not api_key_present:
    st.info("Running in mock mode: LLM connectivity is not configured. Audit trail entries may be limited.")
if not db_url_present:
    st.warning("DATABASE_URL is not set or not writable. Audit trail persistence may be empty.")

render_page_header(
    title="Audit Trail",
    icon="📊",
    description="View all past decisions with complete reasoning and context"
)

# Helper functions
DECISION_NAMES = {
    "AUTONOMOUS": "Go ahead",
    "REVIEW_REQUIRED": "Needs review",
    "ESCALATE": "Escalate",
    "RESPONSE_PROVIDED": "Response provided"
}
DECISION_ICONS = {
    "AUTONOMOUS": "✅",
    "REVIEW_REQUIRED": "⚠️",
    "ESCALATE": "🚨",
    "RESPONSE_PROVIDED": "💬"
}
RISK_NAMES = {
    "LOW": "Low",
    "MEDIUM": "Medium",
    "HIGH": "High"
}
RISK_ICONS = {
    "LOW": "🟢",
    "MEDIUM": "🟡",
    "HIGH": "🔴"
}


def show_risk_badge(risk_level):
    return f"{RISK_ICONS.get(risk_level, '⚪')} {RISK_NAMES.get(risk_level, 'Not set')}"


def show_decision_badge(decision):
    return f"{DECISION_ICONS.get(decision, '❓')} {DECISION_NAMES.get(decision, decision.title())}"


def get_audit_id(entry):
    """
    Get audit ID from entry, supporting both old and new backend fields.
    Prefers 'id' over 'audit_id' for backwards compatibility.
    Returns None if neither is present.
    """
    # Support both old/new backend fields
    audit_id = entry.get("id", None)
    if not audit_id:
        audit_id = entry.get("audit_id", None)
    return audit_id

render_section_header("Search & Filters", icon="🔍", level=3)

# Keyword search
search_query = st.text_input(
    "🔎 Search by keyword",
    placeholder="Search by company name, task description, or any text...",
    help="Search across all fields in the audit trail",
    key="audit_search_input"
)

# Filters row
col1, col2, col3, col4 = st.columns(4)

with col1:
    date_range = st.selectbox(
        "Time Period",
        options=["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
        index=2,
        help="Choose how far back you want to review decisions."
    )

decision_labels = {
    "✅ Go ahead": "AUTONOMOUS",
    "⚠️ Needs review": "REVIEW_REQUIRED",
    "🚨 Escalate": "ESCALATE"
}
decision_code_to_label = {code: label for label, code in decision_labels.items()}

with col2:
    from components.ui_helpers import multiselect_with_select_all
    decision_choices = multiselect_with_select_all(
        "Decision Type",
        options=list(decision_labels.keys()),
        default=list(decision_labels.keys()),
        key="decision_multiselect_audit",
        help="Pick the decisions you want to review.",
        inside_form=False
    )
    filter_decision = [decision_labels[label] for label in decision_choices]

risk_labels = {
    "🟢 Low": "LOW",
    "🟡 Medium": "MEDIUM",
    "🔴 High": "HIGH"
}
with col3:
    risk_choices = multiselect_with_select_all(
        "Risk Level ℹ️",
        options=list(risk_labels.keys()),
        default=list(risk_labels.keys()),
        key="risk_multiselect_audit",
        help="Show only records at the risk level you care about. Risk levels (LOW/MEDIUM/HIGH) indicate the potential impact of non-compliance.",
        inside_form=False
    )
    filter_risk = [risk_labels[label] for label in risk_choices]

with col4:
    limit = st.selectbox(
        "Show Records",
        options=[10, 25, 50, 100],
        index=1,
        help="How many recent records would you like to display?"
    )

if search_query and search_query.strip():
    st.caption(f"🔎 Searching for: **{search_query}** | 💡 Tip: Combine search with filters to find exactly what you need.")
else:
    st.caption("💡 Tip: Use search to find specific tasks, companies, or keywords. Combine with filters for precise results.")

# ✅ AGENTIC AI: Filters apply automatically (agent responds immediately)
try:
    # Get date filter
    date_filter = None
    if date_range == "Last 24 Hours":
        date_filter = (datetime.now() - timedelta(days=1)).isoformat()
    elif date_range == "Last 7 Days":
        date_filter = (datetime.now() - timedelta(days=7)).isoformat()
    elif date_range == "Last 30 Days":
        date_filter = (datetime.now() - timedelta(days=30)).isoformat()
    
    # Build query parameters
    params = {"limit": limit}
    if date_filter:
        params["start_date"] = date_filter
    
    api = APIClient()
    try:
        with st.spinner("Loading audit trail entries..."):
            response = api.get("/api/v1/audit/entries", params=params)
        
        if not response.success:
            display_api_error(response)
            st.stop()
        
        data = response.data or {}
        entries = data.get("entries", [])
        
        if not isinstance(entries, list):
            st.warning("⚠️ **Unexpected Response Format**: Expected a list of entries.")
            entries = []
    except Exception as e:
        st.error(f"❌ **Error Loading Audit Trail**: {str(e)}")
        st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify your network connection\n3. Try refreshing the page")
        st.stop()
    
    # Warn if no entries found (common when running in mock mode or empty DB)
    if not entries:
        env_msg = []
        if not os.getenv("DATABASE_URL"):
            env_msg.append("DATABASE_URL not set (using default SQLite)")
        if not os.getenv("OPENAI_API_KEY"):
            env_msg.append("OPENAI_API_KEY not set (mock mode)")
        tip = "; ".join(env_msg) if env_msg else "Backend may be running with an empty database."
        st.info(f"ℹ️ No audit entries found yet. {tip}\nSubmit a task or decision to generate audit logs.")
    
    # Filter by decision and risk (with safe access)
    filtered_entries = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        decision = e.get("decision", {})
        if not isinstance(decision, dict):
            continue
        outcome = decision.get("outcome")
        risk_level = decision.get("risk_level")
        
        # Apply decision and risk filters
        if outcome not in filter_decision:
            continue
        if risk_level and risk_level not in filter_risk:
            continue
        
        # Apply keyword search if provided
        if search_query and search_query.strip():
            search_lower = search_query.lower().strip()
            # Search across multiple fields
            searchable_text = " ".join([
                str(e.get("task", {}).get("description", "")),
                str(e.get("entity", {}).get("name", "")),
                str(e.get("task", {}).get("category", "")),
                str(e.get("agent_type", "")),
                str(outcome),
                str(risk_level),
            ]).lower()
            
            if search_lower not in searchable_text:
                continue
        
        # Add entry if it passed all filters
        filtered_entries.append(e)
    
    # Display summary
    st.markdown("---")
    # Use actual entries count, not API total_count which may be incorrect
    total_count = len(entries)  # Actual entries returned from API
    
    # Show search results summary
    if search_query and search_query.strip():
        if len(filtered_entries) == 0:
            st.info(f"🔍 No results found for **'{search_query}'**. Try different keywords or clear the search.")
        else:
            st.markdown(f"**Found {len(filtered_entries)} matching record(s) out of {total_count} total**")
    else:
        st.markdown(f"**Showing {len(filtered_entries)} of {total_count} records**")
    
    if not filtered_entries:
        # Better empty state
        if entries:
            st.caption("Filters returned no results. Showing all available entries instead.")
            filtered_entries = entries
            if st.button("🔄 Reset filters", help="Clear filters and show all records"):
                st.session_state["decision_multiselect_audit"] = list(decision_labels.keys())
                st.session_state["risk_multiselect_audit"] = list(risk_labels.keys())
                st.rerun()
        if search_query and search_query.strip():
            st.warning(f"🔍 No results found matching **'{search_query}'** with your current filters.")
            st.markdown("""
            **Try:**
            - Clearing the search box
            - Using different keywords
            - Adjusting your filters
            - Checking a different time period
            """)
        else:
            st.info("""
            📊 **No audit trail entries found**
            
            This could mean:
            - You haven't analyzed any tasks yet
            - Your filters are too restrictive
            - No entries match the selected time period
            
            **Get started:** Go to "Check One Task" to analyze your first compliance question!
            """)
    else:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        decisions = [e["decision"]["outcome"] for e in filtered_entries]
        risks = [e["decision"].get("risk_level") for e in filtered_entries if e["decision"].get("risk_level")]
        
        with col1:
            autonomous = decisions.count("AUTONOMOUS")
            st.metric("Go ahead (✅)", autonomous)
        with col2:
            review_req = decisions.count("REVIEW_REQUIRED")
            st.metric("Needs review (⚠️)", review_req)
        with col3:
            escalate = decisions.count("ESCALATE")
            st.metric("Escalate (🚨)", escalate)
        with col4:
            if risks:
                high_risk = risks.count("HIGH")
                st.metric("High risk (🔴)", high_risk)
        
        # Display entries
        render_divider()
        render_section_header("Audit Records", icon="📋", level=3)
        
        for entry in filtered_entries:
            # Support both old/new backend fields
            audit_id = get_audit_id(entry)
            if audit_id is None:
                continue  # skip invalid rows
            
            with st.expander(
                f"{audit_id} | {entry['task']['description'][:60]}... | "
                f"{show_decision_badge(entry['decision']['outcome'])} "
                f"{show_risk_badge(entry['decision'].get('risk_level', 'N/A'))}"
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Task:** {entry['task']['description']}")
                    # Handle None category gracefully
                    category = entry['task'].get('category')
                    category_label = category.replace('_', ' ').title() if category else 'N/A'
                    st.markdown(f"**Category:** {category_label}")
                    if entry.get('entity') and entry['entity'].get('name'):
                        # Handle None entity type gracefully
                        entity_type = entry['entity'].get('type')
                        entity_type_label = entity_type.replace('_', ' ').title() if entity_type else 'N/A'
                        st.markdown(f"**Entity:** {entry['entity']['name']} ({entity_type_label})")
                    st.markdown(f"**Agent:** {entry['agent_type']}")
                    st.markdown(f"**Timestamp:** {entry['timestamp']}")
                
                with col2:
                    st.markdown(f"**Decision:** {show_decision_badge(entry['decision']['outcome'])}")
                    if entry['decision'].get('risk_level'):
                        st.markdown(f"**Risk:** {show_risk_badge(entry['decision']['risk_level'])}")
                        risk_score = entry['decision'].get('risk_score')
                        if risk_score is not None:
                            st.markdown(f"**Risk Score (0–100):** {risk_score*100:.0f}")
                        else:
                            st.markdown(f"**Risk Score (0–100):** N/A")
                    # Unified schema uses "confidence" at top level, legacy uses "decision.confidence_score"
                    confidence_score = entry.get('confidence_score') or entry['decision'].get('confidence_score')
                    if confidence_score is not None and isinstance(confidence_score, (int, float)):
                        # Normalize to 0-1 range if needed
                        if confidence_score > 1.0:
                            confidence_score = confidence_score / 100.0
                        st.markdown(f"**Confidence Level:** {confidence_score*100:.1f}%")
                    else:
                        st.markdown(f"**Confidence Level:** N/A")
                
                # Use tabs instead of nested expanders
                st.markdown("---")
                tab1, tab2, tab3 = st.tabs(["🤔 Reasoning", "📊 Risk Factors", "💡 Recommendations"])
                
                # Reasoning chain (unified schema uses why.reasoning_steps)
                with tab1:
                    reasoning_steps = []
                    # Try unified schema format first
                    if entry.get("why") and isinstance(entry["why"], dict):
                        reasoning_steps = entry["why"].get("reasoning_steps", [])
                    # Fallback to legacy format
                    if not reasoning_steps:
                        reasoning_steps = entry.get("reasoning_chain", [])
                    
                    if reasoning_steps and isinstance(reasoning_steps, list) and len(reasoning_steps) > 0:
                        for reason in reasoning_steps:
                            if reason and str(reason).strip():
                                st.markdown(f"- {reason}")
                    else:
                        st.info("No reasoning chain available for this entry.")
                
                # Risk factors (unified schema uses risk_analysis list)
                with tab2:
                    risk_analysis = entry.get("risk_analysis", [])
                    risk_factors = entry.get("risk_factors", {})
                    
                    # Convert unified schema format if needed
                    if risk_analysis and isinstance(risk_analysis, list) and len(risk_analysis) > 0:
                        risk_factors = {}
                        for item in risk_analysis:
                            if isinstance(item, dict):
                                factor_name = item.get('factor', '')
                                score = item.get('score', 0.0)
                                if factor_name:
                                    risk_factors[factor_name] = score
                    
                    if risk_factors and isinstance(risk_factors, dict) and len(risk_factors) > 0:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            j_risk = risk_factors.get('jurisdiction_risk', 0) or 0
                            e_risk = risk_factors.get('entity_risk', 0) or 0
                            st.metric("Jurisdiction", f"{j_risk*100:.0f}%")
                            st.metric("Entity", f"{e_risk*100:.0f}%")
                        with col2:
                            t_risk = risk_factors.get('task_risk', 0) or 0
                            d_risk = risk_factors.get('data_sensitivity_risk', 0) or 0
                            st.metric("Task", f"{t_risk*100:.0f}%")
                            st.metric("Data Sensitivity", f"{d_risk*100:.0f}%")
                        with col3:
                            r_risk = risk_factors.get('regulatory_risk', 0) or 0
                            i_risk = risk_factors.get('impact_risk', 0) or 0
                            st.metric("Regulatory", f"{r_risk*100:.0f}%")
                            st.metric("Impact", f"{i_risk*100:.0f}%")
                    else:
                        st.info("No risk factors available for this entry.")
                
                # Recommendations
                with tab3:
                    if entry.get("recommendations"):
                        for rec in entry["recommendations"]:
                            st.info(rec)
                    else:
                        st.info("No recommendations available for this entry.")
        
        # Export options
        render_divider()
        render_section_header("Export Audit Trail", icon="💾", level=3)
        
        # Prepare export data
        export_data = []
        for entry in filtered_entries:
            # Support both old/new backend fields
            audit_id = get_audit_id(entry)
            if audit_id is None:
                continue  # skip invalid rows
            
            decision_label = DECISION_NAMES.get(entry["decision"]["outcome"], entry["decision"]["outcome"].title())
            risk_label = RISK_NAMES.get(entry["decision"].get("risk_level"), "Not set")
            # Handle None values gracefully
            category = entry["task"].get("category")
            category_label = category.replace('_', ' ').title() if category else 'N/A'
            
            # Handle None values in numeric fields before multiplication
            risk_score = entry['decision'].get('risk_score', 0)
            risk_score_display = f"{(risk_score or 0) * 100:.0f}"
            
            confidence_score = entry['decision'].get('confidence_score', 0)
            confidence_display = f"{(confidence_score or 0) * 100:.1f}%"
            
            export_data.append({
                "Audit ID": audit_id,
                "Timestamp": entry["timestamp"],
                "Entity": entry["entity"]["name"] if entry.get("entity") and entry["entity"].get("name") else "N/A",
                "Task": entry["task"]["description"],
                "Category": category_label,
                "Decision": decision_label,
                "Risk Level": risk_label,
                "Risk Score (0-100)": risk_score_display,
                "Confidence Level": confidence_display,
                "Agent": entry["agent_type"]
            })
        
        df = pd.DataFrame(export_data)
        
        # Create enhanced text report
        text_report = f"""
AUDIT TRAIL EXPORT
==================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Records: {len(filtered_entries)}

SUMMARY
-------
This audit trail contains {len(filtered_entries)} compliance decision(s) matching your selected filters.

FILTERS APPLIED
---------------
Date Range: {date_range}
Risk Level: {", ".join(risk_choices) if risk_choices else "All levels"}
Decision: {", ".join(decision_choices) if decision_choices else "All decisions"}

ENTRIES
-------
"""
        for i, entry in enumerate(filtered_entries, 1):
            # Support both old/new backend fields
            audit_id = get_audit_id(entry)
            if audit_id is None:
                continue  # skip invalid rows
            
            decision_label = DECISION_NAMES.get(entry["decision"]["outcome"], entry["decision"]["outcome"].title())
            risk_label = RISK_NAMES.get(entry["decision"].get("risk_level"), "Not set")
            text_report += f"""
Entry #{i}
----------
ID: {audit_id}
Timestamp: {entry["timestamp"]}
Entity: {entry["entity"]["name"] if entry.get("entity") and entry["entity"].get("name") else "N/A"}
Task: {entry["task"]["description"]}
Decision: {decision_label}
Risk: {risk_label}
Confidence: {entry['decision'].get('confidence_score', 0)*100:.1f}%
Agent: {entry["agent_type"]}

"""
        
        # Enhanced JSON export
        export_json = {
            "export_metadata": {
                "generated_at": datetime.now().isoformat(),
                "version": "1.0",
                "export_type": "audit_trail",
                "filters": {
                    "date_range": date_range,
                    "risk_level": filter_risk,
                    "decision": filter_decision
                }
            },
            "summary": {
                "total_records": len(filtered_entries),
                "high_risk": len([e for e in filtered_entries if e["decision"].get("risk_level") == "HIGH"]),
                "medium_risk": len([e for e in filtered_entries if e["decision"].get("risk_level") == "MEDIUM"]),
                "low_risk": len([e for e in filtered_entries if e["decision"].get("risk_level") == "LOW"])
            },
            "entries": filtered_entries
        }
        
        # Determine overall risk for filename
        high_risk_count = len([e for e in filtered_entries if e["decision"].get("risk_level") == "HIGH"])
        if high_risk_count > len(filtered_entries) * 0.3:
            overall_risk = "HIGH"
        elif high_risk_count > len(filtered_entries) * 0.1:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        # Render enhanced export section
        render_export_section(
            data=filtered_entries,
            dataframe=df,
            text_report=text_report,
            json_data=export_json,
            prefix="audit",
            entity_name=f"{len(filtered_entries)}Records",
            task_category="AuditTrail",
            risk_level=overall_risk,
            show_email=True
            # email_api_endpoint not needed - email export shows as disabled
        )
        
        st.caption("💾 Files download immediately. Check your browser's downloads folder.")
        
        # Manual refresh button (optional - filters auto-apply)
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🔄 Refresh Data", type="secondary", width="stretch"):
                st.rerun()

except Exception as e:
    st.error(f"❌ **Unexpected Error: {type(e).__name__}**")
    st.markdown("---")
    st.warning(str(e))
    st.markdown("### What to do:")
    st.markdown("1. 🔄 **Try again** - Click 'Refresh Data'")
    st.markdown("2. 🌐 **Refresh** - Press F5 and resubmit")
    st.markdown("3. 📞 **Contact support** - Describe what happened")
    with st.expander("🐛 Debug Information"):
        import traceback
        st.code(traceback.format_exc())

# Statistics
render_divider()
render_section_header("Overall Statistics", icon="📈", level=3)

try:
    with st.spinner("Loading statistics..."):
        stats_response = APIClient().get("/api/v1/audit/statistics")
    if stats_response.success and isinstance(stats_response.data, dict):
        stats = stats_response.data
    else:
        st.info("Statistics not available at this time.")
        stats = None
except Exception as e:
    st.info(f"Statistics not available: {str(e)}")
    stats = None

if stats:
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Decisions", stats.get("total_decisions", 0))
        with col2:
            avg_conf = stats.get("average_confidence", 0) * 100
            st.metric("Avg Confidence", f"{avg_conf:.1f}%")
        with col3:
            avg_risk = stats.get("average_risk_score", 0)
            st.metric("Avg Risk Score", f"{avg_risk*100:.0f}%")
        with col4:
            high_risk = stats.get("by_risk_level", {}).get("HIGH", 0)
            st.metric("High Risk Items", high_risk)
        
        # Charts - Using Plotly with plotly_white theme
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            import plotly.io as pio
            pio.templates.default = "plotly_white"
            
            col1, col2 = st.columns(2)
            
            with col1:
                by_outcome = stats.get("by_outcome", {})
                if by_outcome:
                    df_outcome = pd.DataFrame(list(by_outcome.items()), columns=["Decision", "Count"])
                    fig = px.bar(
                        df_outcome,
                        x="Decision",
                        y="Count",
                        color="Decision",
                        color_discrete_map={
                            "AUTONOMOUS": "#10b981",
                            "REVIEW_REQUIRED": "#f59e0b",
                            "ESCALATE": "#ef4444"
                        }
                    )
                    fig.update_layout(showlegend=False, xaxis_title="Decision Type", yaxis_title="Count")
                    render_plotly_chart(fig, title="Decisions by Outcome", height=400, show_title=True)
            
            with col2:
                by_risk = stats.get("by_risk_level", {})
                if by_risk:
                    df_risk = pd.DataFrame(list(by_risk.items()), columns=["Risk Level", "Count"])
                    fig = px.bar(
                        df_risk,
                        x="Risk Level",
                        y="Count",
                        color="Risk Level",
                        color_discrete_map={
                            "LOW": "#10b981",
                            "MEDIUM": "#f59e0b",
                            "HIGH": "#ef4444"
                        }
                    )
                    fig.update_layout(showlegend=False, xaxis_title="Risk Level", yaxis_title="Count")
                    render_plotly_chart(fig, title="Decisions by Risk Level", height=400, show_title=True)
        except ImportError:
            # Fallback to simple text if Plotly not available
            st.info("📊 Charts require Plotly. Install with: pip install plotly")
else:
    st.info("Statistics not available at this time.")

# Sidebar: Export History and Chat Assistant
with st.sidebar:
    show_logout_button()
    st.markdown("---")
    
    # Export History
    render_export_history()
    
    st.markdown("---")
    st.markdown("## 💬 AI Chat Assistant")
    st.caption("Ask about audit records")
    
    # Render chat panel
    render_chat_panel(context_data={
        "page": "Audit Trail",
        "entity_name": "Audit Records",
        "task_description": "Ask questions about past decisions, patterns, or specific audit entries"
    })

# Help
with st.expander("❓ Understanding the Audit Trail"):
    st.markdown("""
    ### What is the Audit Trail?
    
    The audit trail is a complete, immutable record of every decision made by the AI Compliance Agent.
    It provides full transparency and accountability for regulatory compliance.
    
    ### What's Included?
    
    Each audit record contains:
    - **Complete reasoning chain** - Step-by-step logic
    - **Risk factor breakdown** - All 6 factors analyzed
    - **Confidence scores** - AI's confidence in the decision
    - **Recommendations** - Actionable next steps
    - **Full context** - Entity and task information
    - **Timestamp** - Exact time of decision
    
    ### Why is this important?
    
    - **Regulatory Compliance**: Demonstrate due diligence to auditors
    - **Quality Assurance**: Review AI decisions for accuracy
    - **Process Improvement**: Identify patterns and optimize workflows
    - **Legal Protection**: Evidence of proper procedures followed
    
    ### Export Options
    
    - **CSV**: Import into Excel or data analysis tools
    - **JSON**: Integrate with other systems or APIs
    - **Full Export**: Download complete audit trail via API
    """)
