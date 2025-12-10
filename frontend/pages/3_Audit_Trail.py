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
import requests
from pathlib import Path
from typing import Dict, Any

# Add frontend directory to path for imports
frontend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(frontend_dir))

from components.chat_assistant import render_chat_panel
from components.auth_utils import require_auth, show_logout_button
from components.export_utils import render_export_section, render_export_history
from components.api_client import APIClient, display_api_error
from components.constants import API_BASE_URL

st.set_page_config(page_title="Audit Trail", page_icon="📊", layout="wide")

# Apply light theme CSS (comprehensive styling already includes all necessary overrides)
from components.ui_helpers import apply_light_theme_css, render_page_header, render_section_header, render_divider
apply_light_theme_css()

# ============================================================================
# AUTHENTICATION CHECK
# ============================================================================
require_auth()
# ============================================================================

# ============================================================================
# SESSION-BASED AUDIT RECORDS (10 items per session)
# ============================================================================
# Initialize session audit records - resets on each new login session
if "session_audit_records" not in st.session_state:
    st.session_state["session_audit_records"] = []
SESSION_AUDIT_LIMIT = 10  # Fixed limit - no user selection

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


def transform_entry_to_nested_format(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform flat API entry format to nested format expected by frontend display logic.
    
    API returns: {decision_outcome, task_description, entity_name, ...}
    Frontend expects: {decision: {outcome, risk_level}, task: {description, category}, entity: {name, type}, ...}
    """
    if not isinstance(entry, dict):
        return entry
    
    # If already in nested format, return as-is
    if "decision" in entry and isinstance(entry.get("decision"), dict):
        return entry
    
    # Transform flat format to nested format
    transformed = entry.copy()
    
    # Create nested decision structure
    decision_outcome = entry.get("decision_outcome") or entry.get("decision", {}).get("outcome")
    risk_level = entry.get("risk_level") or entry.get("decision", {}).get("risk_level")
    risk_score = entry.get("risk_score") or entry.get("decision", {}).get("risk_score")
    confidence_score = entry.get("confidence_score") or entry.get("decision", {}).get("confidence_score")
    
    transformed["decision"] = {
        "outcome": decision_outcome,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "confidence_score": confidence_score
    }
    
    # Create nested task structure
    task_description = entry.get("task_description") or entry.get("task", {}).get("description", "")
    task_category = entry.get("task_category") or entry.get("task", {}).get("category")
    
    transformed["task"] = {
        "description": task_description,
        "category": task_category
    }
    
    # Create nested entity structure
    entity_name = entry.get("entity_name") or entry.get("entity", {}).get("name")
    entity_type = entry.get("entity_type") or entry.get("entity", {}).get("type")
    
    transformed["entity"] = {
        "name": entity_name,
        "type": entity_type
    }
    
    # Add other fields that might be needed
    if "id" not in transformed and "audit_id" in transformed:
        transformed["id"] = transformed["audit_id"]
    
    # Add reasoning chain to "why" structure if needed
    reasoning_chain = entry.get("reasoning_chain") or entry.get("why", {}).get("reasoning_steps", [])
    if reasoning_chain:
        transformed["why"] = {
            "reasoning_steps": reasoning_chain if isinstance(reasoning_chain, list) else [reasoning_chain]
        }
    
    # Add risk_factors to risk_analysis structure
    risk_factors = entry.get("risk_factors") or entry.get("risk_analysis", [])
    if risk_factors:
        transformed["risk_analysis"] = risk_factors if isinstance(risk_factors, list) else []
    
    return transformed

render_section_header("Search & Filters", icon="🔍", level=3)

# Define filter options
decision_labels = {
    "✅ Go ahead": "AUTONOMOUS",
    "⚠️ Needs review": "REVIEW_REQUIRED",
    "🚨 Escalate": "ESCALATE"
}
decision_code_to_label = {code: label for label, code in decision_labels.items()}

risk_labels = {
    "🟢 Low": "LOW",
    "🟡 Medium": "MEDIUM",
    "🔴 High": "HIGH"
}

# Check if reset filters button was clicked (must check BEFORE initializing widgets)
if "reset_filters_audit" in st.session_state and st.session_state["reset_filters_audit"]:
    # Clear all filter-related session state keys (before widgets are created)
    filter_keys_to_clear = [
        "decision_multiselect_audit",
        "risk_multiselect_audit",
        "multiselect_state_decision_multiselect_audit",
        "multiselect_state_risk_multiselect_audit",
        "decision_multiselect_audit_select_all_toggle",
        "risk_multiselect_audit_select_all_toggle"
    ]
    for key in filter_keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    # Clear the reset flag
    del st.session_state["reset_filters_audit"]
    st.rerun()

# Initialize session state keys for multiselect widgets BEFORE they are instantiated
if "decision_multiselect_audit" not in st.session_state:
    st.session_state["decision_multiselect_audit"] = list(decision_labels.keys())
if "risk_multiselect_audit" not in st.session_state:
    st.session_state["risk_multiselect_audit"] = list(risk_labels.keys())

# Also initialize internal state keys used by multiselect_with_select_all
if "multiselect_state_decision_multiselect_audit" not in st.session_state:
    st.session_state["multiselect_state_decision_multiselect_audit"] = list(decision_labels.keys())
if "multiselect_state_risk_multiselect_audit" not in st.session_state:
    st.session_state["multiselect_state_risk_multiselect_audit"] = list(risk_labels.keys())

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
    # Session-based: Always show last 10 records from current session
    st.caption(f"📋 Showing last {SESSION_AUDIT_LIMIT} session records")

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
    
    # Fetch entries from API (we'll filter to session records)
    params = {"limit": 100}  # Fetch enough to populate session
    if date_filter:
        params["start_date"] = date_filter
    
    api = APIClient()
    data = {}
    entries = []
    try:
        # Show spinner only on first load or when cache expires
        if "audit_entries_loaded" not in st.session_state:
            with st.spinner("Loading audit trail entries..."):
                response = api.get("/api/v1/audit/entries", params=params)
                st.session_state["audit_entries_loaded"] = True
        else:
            # Subsequent loads are faster without spinner
            response = api.get("/api/v1/audit/entries", params=params)
        
        if not response.success:
            display_api_error(response)
            # Don't stop, show empty state instead
            entries = []
            data = {}
        else:
            data = response.data or {}
            entries_raw = data.get("entries", [])
            
            if not isinstance(entries_raw, list):
                st.warning("⚠️ **Unexpected Response Format**: Expected a list of entries.")
                entries = []
            else:
                # Transform entries from flat API format to nested format expected by frontend
                entries = []
                for e in entries_raw:
                    if isinstance(e, dict):
                        try:
                            transformed = transform_entry_to_nested_format(e)
                            entries.append(transformed)
                        except Exception as transform_error:
                            # Log transformation error but continue with other entries
                            st.warning(f"⚠️ Failed to transform entry: {str(transform_error)[:100]}")
                            continue
                
                # Debug: Log if transformation issues occurred
                if len(entries) != len(entries_raw) and len(entries_raw) > 0:
                    st.warning(f"⚠️ **Data Transformation**: {len(entries_raw)} entries returned, {len(entries)} transformed successfully.")
                
                # Track entries in session and maintain only last 10
                for entry in entries:
                    entry_id = get_audit_id(entry)
                    if entry_id:
                        # Check if entry already exists in session (avoid duplicates)
                        existing_ids = [get_audit_id(e) for e in st.session_state["session_audit_records"]]
                        if entry_id not in existing_ids:
                            st.session_state["session_audit_records"].append(entry)
                
                # Show only last 10 from session
                entries = st.session_state["session_audit_records"][-SESSION_AUDIT_LIMIT:]
    except requests.exceptions.Timeout:
        st.error("⏱️ **Timeout**: Request to backend timed out.")
        st.info("💡 **Troubleshooting**:\n1. The backend may be overloaded\n2. Try again in a few moments\n3. Check backend logs for issues")
        entries = []
    except requests.exceptions.ConnectionError:
        st.error("🔌 **Connection Error**: Could not connect to the backend server.")
        st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify the API_BASE_URL setting\n3. Check your network connection")
        entries = []
    except Exception as e:
        st.error(f"❌ **Error Loading Audit Trail**: {str(e)}")
        st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify your network connection\n3. Try refreshing the page")
        # Show technical details for debugging
        import traceback
        with st.expander("🔍 Technical Details"):
            st.code(traceback.format_exc(), language="text")
        entries = []  # Set to empty list instead of stopping
    
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
        
        # Get decision and risk from nested structure (already transformed)
        decision = e.get("decision", {})
        if not isinstance(decision, dict):
            # Fallback to flat structure if transformation didn't work
            outcome = e.get("decision_outcome")
            risk_level = e.get("risk_level")
        else:
            outcome = decision.get("outcome")
            risk_level = decision.get("risk_level")
        
        # Skip if outcome is missing
        if not outcome:
            continue
        
        # Apply decision filter - handle both string values and codes
        if outcome not in filter_decision:
            continue
        
        # Apply risk filter - only filter if risk_level exists and filter includes it
        if risk_level and filter_risk and risk_level not in filter_risk:
            continue
        
        # Apply keyword search if provided
        if search_query and search_query.strip():
            search_lower = search_query.lower().strip()
            
            # Get searchable text from nested structure
            task = e.get("task", {})
            entity = e.get("entity", {})
            searchable_text = " ".join([
                str(task.get("description", "")),
                str(entity.get("name", "")),
                str(task.get("category", "")),
                str(e.get("agent_type", "")),
                str(outcome),
                str(risk_level or ""),
            ]).lower()
            
            if search_lower not in searchable_text:
                continue
        
        # Add entry if it passed all filters
        filtered_entries.append(e)
    
    # Display summary
    st.markdown("---")
    # Get total count from API response if available, otherwise use entries length
    if 'data' in locals() and isinstance(data, dict):
        total_count = data.get("total_count", len(entries))
    else:
        total_count = len(entries)
    
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
            if st.button("🔄 Reset filters", help="Clear filters and show all records", key="reset_filters_button_audit"):
                # Set flag to trigger reset on next rerun (before widgets are created)
                st.session_state["reset_filters_audit"] = True
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
        # Summary metrics - safely extract decision and risk from nested structure
        col1, col2, col3, col4 = st.columns(4)
        
        decisions = []
        risks = []
        for e in filtered_entries:
            decision = e.get("decision", {})
            if isinstance(decision, dict):
                outcome = decision.get("outcome")
                risk = decision.get("risk_level")
            else:
                # Fallback to flat format
                outcome = e.get("decision_outcome")
                risk = e.get("risk_level")
            
            if outcome:
                decisions.append(outcome)
            if risk:
                risks.append(risk)
        
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
            
            # Safely get nested values with fallbacks
            task = entry.get('task', {})
            entity = entry.get('entity', {})
            decision = entry.get('decision', {})
            
            # Get task description with fallback
            task_description = task.get('description') if isinstance(task, dict) else entry.get('task_description', 'N/A')
            
            # FIX: Extract better description from system prompts or metadata
            def extract_better_description(desc, entry):
                """Extract a more meaningful description from system prompts or metadata"""
                if not desc or desc == 'N/A':
                    return desc
                
                desc_str = str(desc)
                # Check if it's a system prompt
                system_indicators = ["you are helping a user", "you are an expert", "system:", "your role is", "current page:"]
                is_system_prompt = any(indicator in desc_str.lower() for indicator in system_indicators)
                
                if is_system_prompt:
                    # Try to get original task from metadata
                    metadata = entry.get('metadata', {}) or entry.get('meta_data', {})
                    if isinstance(metadata, dict):
                        original_task = metadata.get('original_task_description')
                        if original_task and len(str(original_task)) > 10:
                            return str(original_task)
                    
                    # Try to extract from common patterns
                    markers = ["user question:", "user query:", "current query:", "query:", "task:"]
                    for marker in markers:
                        if marker.lower() in desc_str.lower():
                            idx = desc_str.lower().index(marker.lower()) + len(marker)
                            extracted = desc_str[idx:].strip()
                            # Clean up trailing phrases
                            for trailing in ["please provide", "based on", "explain"]:
                                if extracted.lower().startswith(trailing):
                                    extracted = extracted[len(trailing):].strip()
                            if len(extracted) > 10:
                                return extracted[:200]  # Limit length
                    
                    # If it's clearly a system prompt, use entity name or category as fallback
                    entity_name = entity.get('name') if isinstance(entity, dict) else entry.get('entity_name')
                    category = task.get('category') if isinstance(task, dict) else entry.get('task_category')
                    if entity_name:
                        return f"Query for {entity_name}"
                    elif category:
                        return f"{category.replace('_', ' ').title()} Query"
                    else:
                        return "Compliance Query"
                
                return desc_str
            
            # Get improved task description
            improved_task_description = extract_better_description(task_description, entry)
            task_desc_display = improved_task_description[:80] + '...' if len(str(improved_task_description)) > 80 else improved_task_description
            
            # Get entity name for display
            entity_name = entity.get('name') if isinstance(entity, dict) else entry.get('entity_name')
            
            # FIX: Include entity name in display if available to make records more distinguishable
            if entity_name and entity_name != 'N/A' and entity_name:
                display_label = f"{audit_id} | {entity_name}: {task_desc_display}"
            else:
                display_label = f"{audit_id} | {task_desc_display}"
            
            # Get decision outcome with fallback
            outcome = decision.get('outcome') if isinstance(decision, dict) else entry.get('decision_outcome', 'UNKNOWN')
            risk_level = decision.get('risk_level') if isinstance(decision, dict) else entry.get('risk_level')
            
            with st.expander(
                f"{display_label} | "
                f"{show_decision_badge(outcome)} "
                f"{show_risk_badge(risk_level or 'N/A')}"
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Use improved task description for display
                    st.markdown(f"**Task:** {improved_task_description}")
                    # Handle None category gracefully
                    category = task.get('category') if isinstance(task, dict) else entry.get('task_category')
                    category_label = category.replace('_', ' ').title() if category else 'N/A'
                    st.markdown(f"**Category:** {category_label}")
                    
                    entity_name = entity.get('name') if isinstance(entity, dict) else entry.get('entity_name')
                    if entity_name:
                        # Handle None entity type gracefully
                        entity_type = entity.get('type') if isinstance(entity, dict) else entry.get('entity_type')
                        entity_type_label = entity_type.replace('_', ' ').title() if entity_type else 'N/A'
                        st.markdown(f"**Entity:** {entity_name} ({entity_type_label})")
                    
                    agent_type = entry.get('agent_type', 'N/A')
                    st.markdown(f"**Agent:** {agent_type}")
                    timestamp = entry.get('timestamp', 'N/A')
                    st.markdown(f"**Timestamp:** {timestamp}")
                
                with col2:
                    st.markdown(f"**Decision:** {show_decision_badge(outcome)}")
                    if risk_level:
                        st.markdown(f"**Risk:** {show_risk_badge(risk_level)}")
                        risk_score = decision.get('risk_score') if isinstance(decision, dict) else entry.get('risk_score')
                        if risk_score is not None:
                            st.markdown(f"**Risk Score (0–100):** {risk_score*100:.0f}")
                        else:
                            st.markdown(f"**Risk Score (0–100):** N/A")
                    # Unified schema uses "confidence" at top level, legacy uses "decision.confidence_score"
                    confidence_score = entry.get('confidence_score') or (decision.get('confidence_score') if isinstance(decision, dict) else None)
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
            
            # Safely get nested values with fallbacks
            task = entry.get('task', {})
            entity = entry.get('entity', {})
            decision = entry.get('decision', {})
            
            outcome = decision.get('outcome') if isinstance(decision, dict) else entry.get('decision_outcome', 'UNKNOWN')
            decision_label = DECISION_NAMES.get(outcome, outcome.title())
            
            risk_level = decision.get('risk_level') if isinstance(decision, dict) else entry.get('risk_level')
            risk_label = RISK_NAMES.get(risk_level, "Not set") if risk_level else "Not set"
            
            # Handle None values gracefully
            category = task.get('category') if isinstance(task, dict) else entry.get('task_category')
            category_label = category.replace('_', ' ').title() if category else 'N/A'
            
            # Handle None values in numeric fields before multiplication
            risk_score = decision.get('risk_score') if isinstance(decision, dict) else entry.get('risk_score')
            risk_score_display = f"{(risk_score or 0) * 100:.0f}" if risk_score is not None else "N/A"
            
            confidence_score = entry.get('confidence_score') or (decision.get('confidence_score') if isinstance(decision, dict) else None)
            if confidence_score is not None:
                # Normalize to 0-1 range if needed
                if confidence_score > 1.0:
                    confidence_score = confidence_score / 100.0
                confidence_display = f"{confidence_score * 100:.1f}%"
            else:
                confidence_display = "N/A"
            
            task_description = task.get('description') if isinstance(task, dict) else entry.get('task_description', 'N/A')
            entity_name = entity.get('name') if isinstance(entity, dict) else entry.get('entity_name', 'N/A')
            
            export_data.append({
                "Audit ID": audit_id,
                "Timestamp": entry.get("timestamp", "N/A"),
                "Entity": entity_name,
                "Task": task_description,
                "Category": category_label,
                "Decision": decision_label,
                "Risk Level": risk_label,
                "Risk Score (0-100)": risk_score_display,
                "Confidence Level": confidence_display,
                "Agent": entry.get("agent_type", "N/A")
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
            
            # Safely get nested values with fallbacks
            task = entry.get('task', {})
            entity = entry.get('entity', {})
            decision = entry.get('decision', {})
            
            outcome = decision.get('outcome') if isinstance(decision, dict) else entry.get("decision_outcome", 'UNKNOWN')
            decision_label = DECISION_NAMES.get(outcome, outcome.title())
            
            risk_level = decision.get('risk_level') if isinstance(decision, dict) else entry.get('risk_level')
            risk_label = RISK_NAMES.get(risk_level, "Not set") if risk_level else "Not set"
            
            task_description = task.get('description') if isinstance(task, dict) else entry.get('task_description', 'N/A')
            entity_name = entity.get('name') if isinstance(entity, dict) else entry.get('entity_name', 'N/A')
            
            confidence_score = entry.get('confidence_score') or (decision.get('confidence_score') if isinstance(decision, dict) else None)
            if confidence_score is not None:
                if confidence_score > 1.0:
                    confidence_score = confidence_score / 100.0
                confidence_display = f"{confidence_score*100:.1f}%"
            else:
                confidence_display = "N/A"
            
            text_report += f"""
Entry #{i}
----------
ID: {audit_id}
Timestamp: {entry.get("timestamp", "N/A")}
Entity: {entity_name}
Task: {task_description}
Decision: {decision_label}
Risk: {risk_label}
Confidence: {confidence_display}
Agent: {entry.get("agent_type", "N/A")}

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
                "high_risk": len([
                    e for e in filtered_entries 
                    if (e.get("decision", {}).get("risk_level") if isinstance(e.get("decision"), dict) else e.get("risk_level")) == "HIGH"
                ]),
                "medium_risk": len([
                    e for e in filtered_entries 
                    if (e.get("decision", {}).get("risk_level") if isinstance(e.get("decision"), dict) else e.get("risk_level")) == "MEDIUM"
                ]),
                "low_risk": len([
                    e for e in filtered_entries 
                    if (e.get("decision", {}).get("risk_level") if isinstance(e.get("decision"), dict) else e.get("risk_level")) == "LOW"
                ])
            },
            "entries": filtered_entries
        }
        
        # Determine overall risk for filename
        high_risk_count = len([
            e for e in filtered_entries 
            if (e.get("decision", {}).get("risk_level") if isinstance(e.get("decision"), dict) else e.get("risk_level")) == "HIGH"
        ])
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

# Statistics - CACHED for performance
render_divider()
render_section_header("Overall Statistics", icon="📈", level=3)

@st.cache_data(ttl=60)  # Cache for 60 seconds to improve performance
def get_cached_statistics():
    """Cached statistics to improve performance"""
    try:
        stats_response = APIClient().get("/api/v1/audit/statistics")
        if stats_response.success and isinstance(stats_response.data, dict):
            return stats_response.data
    except Exception:
        pass
    return None

# Use cached statistics instead of blocking call
stats = get_cached_statistics()

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
        
        # Charts - COMPLETELY REWRITTEN: Direct Plotly rendering with explicit styling
        st.markdown("### 📊 Decision Statistics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Decisions by Outcome**")
            by_outcome = stats.get("by_outcome", {})
            if by_outcome and isinstance(by_outcome, dict) and len(by_outcome) > 0:
                try:
                    import plotly.express as px
                    df_outcome = pd.DataFrame(list(by_outcome.items()), columns=["Decision", "Count"])
                    fig = px.bar(
                        df_outcome,
                        x="Decision",
                        y="Count",
                        color="Decision",
                        color_discrete_map={
                            "AUTONOMOUS": "#059669",  # Much darker green for visibility
                            "REVIEW_REQUIRED": "#d97706",  # Much darker orange for visibility
                            "ESCALATE": "#dc2626"  # Much darker red for visibility
                        },
                        labels={"Decision": "Decision Type", "Count": "Number of Decisions"}
                    )
                    # FIXED: Much darker colors, thicker borders, better contrast
                    fig.update_layout(
                        title={"text": "Decisions by Outcome", "font": {"color": "#0f172a", "size": 18, "weight": "bold"}},
                        height=400,
                        paper_bgcolor='#ffffff',
                        plot_bgcolor='#ffffff',
                        font={"color": "#0f172a", "size": 14},
                        margin=dict(l=60, r=20, t=50, b=60),
                        xaxis={
                            "title": {"text": "Decision Type", "font": {"color": "#0f172a", "size": 14, "weight": "bold"}},
                            "tickfont": {"color": "#0f172a", "size": 12},
                            "gridcolor": "#64748b",
                            "showline": True,
                            "linecolor": "#475569",
                            "linewidth": 3
                        },
                        yaxis={
                            "title": {"text": "Count", "font": {"color": "#0f172a", "size": 14, "weight": "bold"}},
                            "tickfont": {"color": "#0f172a", "size": 12},
                            "gridcolor": "#64748b",
                            "showline": True,
                            "linecolor": "#475569",
                            "linewidth": 3
                        },
                        showlegend=False
                    )
                    # FIXED: Add thick borders to bars and dark text
                    fig.update_traces(
                        marker_line_width=3,
                        marker_line_color="#0f172a",
                        textfont_color="#0f172a",
                        textfont_size=14
                    )
                    st.plotly_chart(fig, use_container_width=True, key="audit_outcome_chart")
                except Exception as e:
                    st.error(f"Chart rendering error: {str(e)}")
                    st.info("📊 Chart data: " + str(by_outcome))
            else:
                st.info("📊 No outcome data available for chart.")
        
        with col2:
            st.markdown("**Decisions by Risk Level**")
            by_risk = stats.get("by_risk_level", {})
            if by_risk and isinstance(by_risk, dict) and len(by_risk) > 0:
                try:
                    import plotly.express as px
                    df_risk = pd.DataFrame(list(by_risk.items()), columns=["Risk Level", "Count"])
                    fig = px.bar(
                        df_risk,
                        x="Risk Level",
                        y="Count",
                        color="Risk Level",
                        color_discrete_map={
                            "LOW": "#059669",  # Much darker green for visibility
                            "MEDIUM": "#d97706",  # Much darker orange for visibility
                            "HIGH": "#dc2626"  # Much darker red for visibility
                        },
                        labels={"Risk Level": "Risk Level", "Count": "Number of Decisions"}
                    )
                    # FIXED: Much darker colors, thicker borders, better contrast
                    fig.update_layout(
                        title={"text": "Decisions by Risk Level", "font": {"color": "#0f172a", "size": 18, "weight": "bold"}},
                        height=400,
                        paper_bgcolor='#ffffff',
                        plot_bgcolor='#ffffff',
                        font={"color": "#0f172a", "size": 14},
                        margin=dict(l=60, r=20, t=50, b=60),
                        xaxis={
                            "title": {"text": "Risk Level", "font": {"color": "#0f172a", "size": 14, "weight": "bold"}},
                            "tickfont": {"color": "#0f172a", "size": 12},
                            "gridcolor": "#64748b",
                            "showline": True,
                            "linecolor": "#475569",
                            "linewidth": 3
                        },
                        yaxis={
                            "title": {"text": "Count", "font": {"color": "#0f172a", "size": 14, "weight": "bold"}},
                            "tickfont": {"color": "#0f172a", "size": 12},
                            "gridcolor": "#64748b",
                            "showline": True,
                            "linecolor": "#475569",
                            "linewidth": 3
                        },
                        showlegend=False
                    )
                    # FIXED: Add thick borders to bars and dark text
                    fig.update_traces(
                        marker_line_width=3,
                        marker_line_color="#0f172a",
                        textfont_color="#0f172a",
                        textfont_size=14
                    )
                    st.plotly_chart(fig, use_container_width=True, key="audit_risk_chart")
                except Exception as e:
                    st.error(f"Chart rendering error: {str(e)}")
                    st.info("📊 Chart data: " + str(by_risk))
            else:
                st.info("📊 No risk level data available for chart.")
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
