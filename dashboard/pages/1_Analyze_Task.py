"""
Check a Task - Get Instant Guidance
====================================
Streamlined orchestrator for task analysis.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add dashboard directory to path
dashboard_dir = Path(__file__).parent.parent
sys.path.insert(0, str(dashboard_dir))

from components.auth_utils import require_auth
from components.session_manager import SessionManager
from components.api_client import APIClient, display_api_error
from components.constants import (
    TYPE_MAP, INDUSTRY_MAP, TASK_MAP, IMPACT_MAP,
    JURISDICTION_DISPLAY_TO_CODE,
    COMPANY_TYPE_OPTIONS, INDUSTRY_OPTIONS, TASK_TYPE_OPTIONS,
    IMPACT_OPTIONS, LOCATION_OPTIONS, EXAMPLE_FORM_VALUES
)
from components.analyze_task.form_validator import FormValidator
from components.analyze_task.results_display import render_results
from components.ui_helpers import multiselect_with_select_all, add_tooltip, get_aria_label

# Page config
st.set_page_config(page_title="Check a Task", page_icon="✅", layout="wide")

# Authentication
require_auth()

# Initialize session
SessionManager.init()

# Initialize API client
api_client = APIClient()

st.title("✅ Check a Task - Get Instant Guidance")
st.markdown("Answer a few questions and get instant guidance on whether you can handle this task yourself.")

# ============================================================================
# SHOW PREVIOUS ANALYSIS NOTICE
# ============================================================================
if SessionManager.has_results():
    age_minutes = SessionManager.get_analysis_age_minutes()
    if age_minutes and age_minutes < 60:
        st.info(f"🤖 **Agent Memory Active**: Last analysis from {age_minutes} minute(s) ago is displayed below.")

# ============================================================================
# QUICK ACTIONS
# ============================================================================
action_col1, action_col2, action_col3 = st.columns([1, 1, 3])
with action_col1:
    if st.button("⚡ Load Example", use_container_width=True):
        SessionManager.save_form_data(EXAMPLE_FORM_VALUES)
        st.rerun()
with action_col2:
    if st.button("🔄 Reset Form", use_container_width=True):
        SessionManager.reset_form()
        st.rerun()

# ============================================================================
# MAIN FORM
# ============================================================================
with st.form("task_check_form", clear_on_submit=False):
    form_defaults = SessionManager.get_form_data()
    
    st.markdown("## 📋 Step 1: Your Company Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        company_name = st.text_input(
            "Company Name *",
            value=form_defaults.get("company_name", ""),
            placeholder="Enter your company name",
            key="company_name_input",
            help="Enter the name of your organization"
        )
        
        company_type_index = COMPANY_TYPE_OPTIONS.index(form_defaults.get("company_type", COMPANY_TYPE_OPTIONS[0])) if form_defaults.get("company_type") in COMPANY_TYPE_OPTIONS else 0
        company_type = st.selectbox(
            "Type of Organization *",
            options=COMPANY_TYPE_OPTIONS,
            index=company_type_index,
            key="company_type_select",
            help="Select the type of organization you represent"
        )
        
        industry_index = INDUSTRY_OPTIONS.index(form_defaults.get("industry", INDUSTRY_OPTIONS[0])) if form_defaults.get("industry") in INDUSTRY_OPTIONS else 0
        industry = st.selectbox(
            "Industry or Sector *",
            options=INDUSTRY_OPTIONS,
            index=industry_index,
            key="industry_select",
            help="Select your industry or sector"
        )
    
    with col2:
        employee_count = st.text_input(
            "Number of Employees *",
            value=form_defaults.get("employee_count", ""),
            placeholder="e.g., 50",
            key="employee_count_input",
            help="Enter the number of employees in your organization"
        )
        
        default_locations = form_defaults.get("locations", [])
        locations = multiselect_with_select_all(
            "Where do you operate? *",
            options=LOCATION_OPTIONS,
            default=default_locations,
            key="locations_multiselect",
            help="Select all locations where your organization operates. Required field."
        )
        
        handles_customer_data = st.checkbox(
            "We handle customer or user data",
            value=form_defaults.get("handles_data", False),
            key="handles_data_checkbox",
            help="Check if your organization processes customer or user data"
        )
        
        is_regulated = st.checkbox(
            "We're a regulated entity (bank, healthcare, etc.)",
            value=form_defaults.get("is_regulated", False),
            key="is_regulated_checkbox",
            help="Check if your organization is directly regulated (e.g., bank, healthcare provider)"
        )
    
    st.markdown("---")
    st.markdown("## 📝 Step 2: About This Task")
    
    task_description = st.text_area(
        "What do you need to do? *",
        value=form_defaults.get("task_description", ""),
        placeholder="Describe the task in your own words...",
        height=120,
        key="task_description_textarea",
        help="Describe the compliance task you need help with"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        task_type_index = TASK_TYPE_OPTIONS.index(form_defaults.get("task_type", TASK_TYPE_OPTIONS[0])) if form_defaults.get("task_type") in TASK_TYPE_OPTIONS else 0
        task_type = st.selectbox(
            "What Kind of Task Is This? *",
            options=TASK_TYPE_OPTIONS,
            index=task_type_index,
            key="task_type_select",
            help="Select the category that best describes your task"
        )
        
        involves_personal_info = st.checkbox(
            "This task involves customer personal information",
            value=form_defaults.get("involves_personal", False),
            key="involves_personal_checkbox",
            help="Check if this task involves personal information (PII, names, addresses, etc.)"
        )
        
        involves_financial_info = st.checkbox(
            "This task involves financial or payment information",
            value=form_defaults.get("involves_financial", False),
            key="involves_financial_checkbox",
            help="Check if this task involves financial data or payment information"
        )
        
        crosses_borders = st.checkbox(
            "This task involves sending data to another country",
            value=form_defaults.get("crosses_borders", False),
            key="crosses_borders_checkbox",
            help="Check if this task involves cross-border data transfer"
        )
    
    with col2:
        has_deadline = st.checkbox(
            "There's a specific deadline for this task",
            value=form_defaults.get("has_deadline", False),
            key="has_deadline_checkbox",
            help="Check this box if the task has a specific deadline"
        )
        
        # Always show date field - never disabled for better UX and keyboard accessibility
        stored_deadline = form_defaults.get("deadline_date")
        if isinstance(stored_deadline, str):
            try:
                stored_deadline = datetime.fromisoformat(stored_deadline).date()
            except ValueError:
                stored_deadline = None
        
        default_deadline = stored_deadline if stored_deadline else (datetime.now() + timedelta(days=30)).date()
        deadline_date = st.date_input(
            "When Is It Due?" + (" *" if has_deadline else " (Optional)"),
            value=default_deadline,
            min_value=datetime.now().date(),
            disabled=False,  # Always enabled for accessibility
            key="deadline_date_input",
            help="Select your task deadline. Required if deadline checkbox is checked." if has_deadline else "Select your task deadline (optional). You can check the box above to mark it as required."
        )
        
        impact_index = IMPACT_OPTIONS.index(form_defaults.get("impact_level", IMPACT_OPTIONS[0])) if form_defaults.get("impact_level") in IMPACT_OPTIONS else 0
        impact_level = st.selectbox(
            "What Happens If This Goes Wrong? ℹ️ *",
            options=IMPACT_OPTIONS,
            index=impact_index,
            key="impact_level_select",
            help="Select the potential impact level if something goes wrong. This helps assess risk."
        )
        
        people_affected = st.text_input(
            "How Many People Could Be Affected?",
            value=form_defaults.get("people_affected", ""),
            placeholder="Optional - enter a number",
            key="people_affected_input",
            help="Optional: Enter the number of people who could be affected if something goes wrong"
        )
    
    st.markdown("---")
    st.markdown("<p style='font-size: 1.3rem; text-align: center; color: #3b82f6; margin: 1.5rem 0; font-weight: 600;'>Ready to get your answer? Click below:</p>", unsafe_allow_html=True)
    
    submitted = st.form_submit_button(
        "🚀 Get My Answer Now", 
        use_container_width=True, 
        type="primary",
        help="Submit the form to analyze your compliance task"
    )

# ============================================================================
# PROCESS SUBMISSION
# ============================================================================
if submitted:
    # Clear previous validation errors on new submission
    if "form_errors" in st.session_state:
        del st.session_state.form_errors
    if "form_warnings" in st.session_state:
        del st.session_state.form_warnings
    
    # Convert locations to codes
    selected_location_codes = [JURISDICTION_DISPLAY_TO_CODE[loc] for loc in locations if loc in JURISDICTION_DISPLAY_TO_CODE]
    
    # Save form data
    form_data = {
        'company_name': company_name,
        'company_type': company_type,
        'industry': industry,
        'employee_count': employee_count,
        'locations': locations,
        'handles_data': handles_customer_data,
        'is_regulated': is_regulated,
        'task_description': task_description,
        'task_type': task_type,
        'involves_personal': involves_personal_info,
        'involves_financial': involves_financial_info,
        'crosses_borders': crosses_borders,
        'has_deadline': has_deadline,
        'deadline_date': deadline_date if has_deadline else None,  # Only include if checkbox checked
        'impact_level': impact_level,
        'people_affected': people_affected
    }
    SessionManager.save_form_data(form_data)
    
    # Validate
    errors, warnings = FormValidator.validate(form_data)
    
    if errors:
        # Store errors in session state to clear on next submit
        st.session_state.form_errors = errors
        st.session_state.form_warnings = warnings
        
        st.error("⚠️ **We need a bit more information:**")
        for i, error in enumerate(errors, 1):
            st.markdown(f"{i}. {error}")
        st.info("💡 **Tip**: All fields marked with * are required.")
    else:
        # Clear any previous errors on successful validation
        if "form_errors" in st.session_state:
            del st.session_state.form_errors
        if "form_warnings" in st.session_state:
            del st.session_state.form_warnings
        
        if warnings:
            st.warning("⚠️ **Please note:**")
            for warning in warnings:
                st.markdown(f"- {warning}")
        
        # Create payload
        payload = FormValidator.create_api_payload(
            form_data, TYPE_MAP, INDUSTRY_MAP, TASK_MAP, IMPACT_MAP, selected_location_codes
        )
        
        # Show progress
        with st.spinner("🤖 AI Agent is analyzing your task..."):
            response = api_client.analyze_decision(payload)
        
        if response.success:
            SessionManager.save_analysis(response.data)
            st.success("✅ Analysis complete! Results below:")
            st.rerun()  # Rerun to show results cleanly and clear any errors
        else:
            display_api_error(response)

# ============================================================================
# DISPLAY RESULTS
# ============================================================================
if SessionManager.has_results():
    analysis = SessionManager.get_analysis()
    
    # Render all results through centralized orchestrator
    render_results(analysis)
    
    # New Analysis Button
    if st.button("📝 Analyze Another Task"):
        SessionManager.reset_form()
        st.rerun()

# ============================================================================
# HELP SECTION
# ============================================================================
st.markdown("---")
with st.expander("❓ Need Help?"):
    st.markdown("""
    ### How to Use This Form
    
    **Step 1**: Tell us about your company
    - Enter basic information
    - Select all locations where you operate
    
    **Step 2**: Describe your task
    - Use your own words
    - Be specific about what data you're handling
    - Tell us if there's a deadline
    
    **Get Your Answer**: Click the button and the AI will analyze your situation instantly.
    """)

