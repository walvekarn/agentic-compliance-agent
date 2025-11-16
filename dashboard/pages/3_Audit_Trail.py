"""
Audit Trail Page
================
View and filter all past compliance decisions.
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

# Add dashboard directory to path for imports
dashboard_dir = Path(__file__).parent.parent
sys.path.insert(0, str(dashboard_dir))

from components.chat_assistant import render_chat_panel
from components.auth_utils import require_auth
from components.export_utils import render_export_section, render_export_history
from components.constants import API_BASE_URL

st.set_page_config(page_title="Audit Trail", page_icon="📊", layout="wide")

# ============================================================================
# AUTHENTICATION CHECK
# ============================================================================
require_auth()
# ============================================================================

# Fix dropdown text visibility
st.markdown("""
<style>
    /* Fix selectbox text visibility */
    .stSelectbox [data-baseweb="select"] > div {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }
    
    .stSelectbox [data-baseweb="select"] span {
        color: #1f2937 !important;
    }
    
    /* Fix multiselect text visibility */
    .stMultiSelect [data-baseweb="select"] > div {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }
    
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #3b82f6 !important;
        color: #ffffff !important;
    }
    
    .stMultiSelect span {
        color: #1f2937 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Audit Trail")
st.markdown("View all past decisions with complete reasoning and context.")

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

# Filters
st.markdown("### 🔍 Filters")
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
    "🚨 Escalate": "ESCALATE",
    "💬 Response provided": "RESPONSE_PROVIDED"
}
decision_code_to_label = {code: label for label, code in decision_labels.items()}

with col2:
    from components.ui_helpers import multiselect_with_select_all
    decision_choices = multiselect_with_select_all(
        "Decision Type",
        options=list(decision_labels.keys()),
        default=list(decision_labels.keys()),
        key="decision_multiselect_audit",
        help="Pick the decisions you want to review."
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
        help="Show only records at the risk level you care about. Risk levels (LOW/MEDIUM/HIGH) indicate the potential impact of non-compliance."
    )
    filter_risk = [risk_labels[label] for label in risk_choices]

with col4:
    limit = st.selectbox(
        "Show Records",
        options=[10, 25, 50, 100],
        index=1,
        help="How many recent records would you like to display?"
    )

st.caption("💡 Tip: Combine the filters above to focus on the decisions you need to review right now.")

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
    
    response = requests.get(
        f"{API_BASE_URL}/api/v1/audit/entries",
        params=params,
        timeout=10
    )
    response.raise_for_status()  # Raise exception for bad status codes
    
    # If we get here, status is 200
    data = response.json()
    entries = data.get("entries", [])
    
    # Filter by decision and risk
    filtered_entries = [
        e for e in entries
        if e["decision"]["outcome"] in filter_decision
        and (e["decision"].get("risk_level") in filter_risk or not e["decision"].get("risk_level"))
    ]
    
    # Display summary
    st.markdown("---")
    total_count = data.get('total_count', data.get('count', len(entries)))
    st.markdown(f"### 📈 Showing {len(filtered_entries)} of {total_count} records")
    
    if filtered_entries:
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
        st.markdown("---")
        st.markdown("### 📋 Audit Records")
        
        for entry in filtered_entries:
            with st.expander(
                f"{entry['audit_id']} | {entry['task']['description'][:60]}... | "
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
                        st.markdown(f"**Risk Score (0–100):** {entry['decision'].get('risk_score', 0)*100:.0f}")
                    st.markdown(f"**Confidence Level:** {entry['decision']['confidence_score']*100:.1f}%")
                
                # Use tabs instead of nested expanders
                st.markdown("---")
                tab1, tab2, tab3 = st.tabs(["🤔 Reasoning", "📊 Risk Factors", "💡 Recommendations"])
                
                # Reasoning chain
                with tab1:
                    if entry.get("reasoning_chain"):
                        for reason in entry["reasoning_chain"]:
                            st.markdown(f"- {reason}")
                    else:
                        st.info("No reasoning chain available for this entry.")
                
                # Risk factors
                with tab2:
                    if entry.get("risk_factors"):
                        rf = entry["risk_factors"]
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Jurisdiction", f"{rf.get('jurisdiction_risk', 0)*100:.0f}%")
                            st.metric("Entity", f"{rf.get('entity_risk', 0)*100:.0f}%")
                        with col2:
                            st.metric("Task", f"{rf.get('task_risk', 0)*100:.0f}%")
                            st.metric("Data Sensitivity", f"{rf.get('data_sensitivity_risk', 0)*100:.0f}%")
                        with col3:
                            st.metric("Regulatory", f"{rf.get('regulatory_risk', 0)*100:.0f}%")
                            st.metric("Impact", f"{rf.get('impact_risk', 0)*100:.0f}%")
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
        st.markdown("---")
        st.markdown("### 💾 Export Audit Trail")
        
        # Prepare export data
        export_data = []
        for entry in filtered_entries:
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
                "Audit ID": entry["audit_id"],
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
            decision_label = DECISION_NAMES.get(entry["decision"]["outcome"], entry["decision"]["outcome"].title())
            risk_label = RISK_NAMES.get(entry["decision"].get("risk_level"), "Not set")
            text_report += f"""
Entry #{i}
----------
ID: {entry["audit_id"]}
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
            show_email=True,
            email_api_endpoint=f"{API_BASE_URL}/api/v1/export/email"
        )
        
        st.caption("💾 Files download immediately. Check your browser's downloads folder.")
        
        # Manual refresh button (optional - filters auto-apply)
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🔄 Refresh Data", type="secondary", use_container_width=True):
                st.rerun()
        
    else:
        st.warning("No audit records match these filters. Try expanding the time period or selecting additional decision types above.")

except requests.exceptions.ConnectionError:
    st.error("❌ **Cannot connect to backend API**")
    st.markdown("---")
    st.info("💡 **Solution:** Run `make start` to start the backend")
    st.code("# Terminal command:\nmake start", language="bash")
    st.markdown("### What to do:")
    st.markdown("1. 🔌 **Check your network** - Make sure you're connected")
    st.markdown("2. 🔄 **Start the backend** - Run `make start` or `python main.py` in a terminal")
    st.markdown("3. 🔄 **Refresh and try again** - Press F5 and resubmit")
    st.markdown("4. 📞 **Still offline?** - Contact IT support")
    st.warning("⚠️ **For IT Support**: Backend API may not be running. Start with `python main.py`")
    if st.button("🔄 Test Connection"):
        st.rerun()
except requests.exceptions.Timeout:
    st.error("⏱️ **Request Timed Out**")
    st.markdown("---")
    st.warning("The request is taking longer than expected.")
    st.markdown("### What to do:")
    st.markdown("1. ⏱️ **Wait 10-15 seconds** - The system might be processing other requests")
    st.markdown("2. 🔄 **Try again** - Click 'Refresh Data'")
    st.markdown("3. 📞 **If it times out again** - Contact IT support")
    if st.button("🔄 Try Again"):
        st.rerun()
except requests.exceptions.HTTPError as e:
    st.error(f"❌ **API Error: {response.status_code}**")
    st.markdown("---")
    st.warning(f"Backend returned an error. Check the details below.")
    with st.expander("🔍 Technical Details"):
        try:
            st.json(response.json() if response.text else {"error": "No response body"})
        except:
            st.code(response.text[:500] if response.text else "No response body")
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
st.markdown("---")
st.markdown("### 📈 Overall Statistics")

try:
    stats_response = requests.get(f"{API_BASE_URL}/api/v1/audit/statistics")
    if stats_response.status_code == 200:
        stats = stats_response.json()
        
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
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Decisions by Outcome")
            by_outcome = stats.get("by_outcome", {})
            if by_outcome:
                df_outcome = pd.DataFrame(list(by_outcome.items()), columns=["Decision", "Count"])
                st.bar_chart(df_outcome.set_index("Decision"))
        
        with col2:
            st.markdown("#### Decisions by Risk Level")
            by_risk = stats.get("by_risk_level", {})
            if by_risk:
                df_risk = pd.DataFrame(list(by_risk.items()), columns=["Risk Level", "Count"])
                st.bar_chart(df_risk.set_index("Risk Level"))

except:
    st.info("Statistics not available")

# Sidebar: Export History and Chat Assistant
with st.sidebar:
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

