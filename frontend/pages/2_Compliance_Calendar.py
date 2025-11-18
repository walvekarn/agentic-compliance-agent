"""
Compliance Calendar Page
=========================
Generate a complete compliance calendar for any organization.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import sys
from pathlib import Path

# Add frontend directory to path for imports
frontend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(frontend_dir))

from components.chat_assistant import render_chat_panel
from components.auth_utils import require_auth, show_logout_button
from components.export_utils import render_export_section, render_export_history
from components.api_client import APIClient, display_api_error
from components.constants import API_BASE_URL

st.set_page_config(page_title="Compliance Calendar", page_icon="📋", layout="wide")

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
    
    /* Input fields */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("📋 Generate Compliance Calendar")
st.markdown("Create a complete compliance calendar tailored to your organization.")

# Add informational context for users
st.info("""
💡 **About This Calendar**: This tool generates AI-powered compliance tasks based on your organization profile and operating jurisdictions. 

The tasks shown are **typical regulatory requirements** for organizations like yours. They serve as a starting point to help you:
- Identify potential compliance obligations
- Plan ahead for regulatory deadlines  
- Understand what actions may be required

**Note:** These are AI-generated suggestions. Always verify with your legal/compliance team for your specific situation.
""")

# Helper functions
def show_risk_badge(risk_level):
    colors = {
        "LOW": "🟢",
        "MEDIUM": "🟡",
        "HIGH": "🔴"
    }
    return f"{colors.get(risk_level, '⚪')} {risk_level}"

def show_decision_badge(decision):
    badges = {
        "AUTONOMOUS": "✅ Proceed",
        "REVIEW_REQUIRED": "⚠️ Review",
        "ESCALATE": "🚨 Escalate"
    }
    return badges.get(decision, decision)

# Initialize session state for form retention
# Parsing helpers -------------------------------------------------------------

def parse_positive_int(value: str, field_label: str, errors, minimum: int = 1):
    if not value or not value.strip():
        errors.append(f"**{field_label}**: Please enter a whole number (minimum {minimum}).")
        return None
    try:
        number = int(value.replace(",", "").strip())
        if number < minimum:
            errors.append(f"**{field_label}**: Please enter a value of at least {minimum}.")
            return None
        return number
    except ValueError:
        errors.append(f"**{field_label}**: Only whole numbers are allowed.")
        return None

def parse_optional_int(value: str, field_label: str, errors, minimum: int = 0):
    if not value or not value.strip():
        return None
    try:
        number = int(value.replace(",", "").strip())
        if number < minimum:
            errors.append(f"**{field_label}**: Cannot be less than {minimum}.")
            return None
        return number
    except ValueError:
        errors.append(f"**{field_label}**: Only whole numbers are allowed.")
        return None

def parse_positive_float(value: str, field_label: str, errors, minimum: float = 0.0):
    if not value or not value.strip():
        errors.append(f"**{field_label}**: Please enter a number (you can include commas).")
        return None
    try:
        number = float(value.replace(",", "").strip())
        if number < minimum:
            errors.append(f"**{field_label}**: Must be {minimum} or greater.")
            return None
        return number
    except ValueError:
        errors.append(f"**{field_label}**: Only numbers are allowed. Example: 1250000")
        return None

# Initialize session state for form defaults
if "calendar_form_defaults" not in st.session_state:
    st.session_state.calendar_form_defaults = {
        "entity_name": "",
        "entity_type": "-- Select organization type --",
        "locations": [],
        "industry": "-- Select industry --",
        "employee_count": "",
        "annual_revenue": "",
        "has_personal_data": False,
        "is_regulated": False,
        "previous_violations": ""
    }

# Load Example and Reset Form buttons (outside form)
action_col1, action_col2, action_col3 = st.columns([1, 1, 2])
with action_col1:
    if st.button("📝 Load Example", width='stretch', help="Pre-fill the form with sample data"):
        st.session_state.calendar_form_defaults = {
            "entity_name": "TechCorp Demo",
            "entity_type": "Private company",
            "locations": ["United States"],
            "industry": "Technology and software",
            "employee_count": "250",
            "annual_revenue": "5000000",
            "has_personal_data": True,
            "is_regulated": False,
            "previous_violations": "0"
        }
        st.rerun()
with action_col2:
    if st.button("🔄 Reset Form", width='stretch', help="Clear all fields"):
        st.session_state.calendar_form_defaults = {
            "entity_name": "",
            "entity_type": "-- Select organization type --",
            "locations": [],
            "industry": "-- Select industry --",
            "employee_count": "",
            "annual_revenue": "",
            "has_personal_data": False,
            "is_regulated": False,
            "previous_violations": ""
        }
        st.rerun()

st.markdown("---")

# Form -----------------------------------------------------------------------
with st.form("calendar_form"):
    st.markdown("### 🏢 Organization Information")
    st.markdown("<p style='color: #64748b;'>All fields marked with * are required</p>", unsafe_allow_html=True)
    
    defaults = st.session_state.calendar_form_defaults
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        entity_name = st.text_input(
            "Organization Name *",
            value=defaults.get("entity_name", ""),
            placeholder="Enter organization name (e.g., TechCorp Inc)",
            help="Enter your organization name (Required)"
        )
        
        entity_type_options = [
            "-- Select organization type --",
            "Startup (new business)",
            "Private company",
            "Public company (traded)",
            "Bank or financial institution",
            "Healthcare provider",
            "Non-profit organization",
            "Government agency"
        ]
        default_entity_type_index = (
            entity_type_options.index(defaults.get("entity_type", entity_type_options[0]))
            if defaults.get("entity_type", entity_type_options[0]) in entity_type_options
            else 0
        )
        entity_type = st.selectbox(
            "Organization Type *",
            options=entity_type_options,
            index=default_entity_type_index,
            help="Select the type of organization (Required)"
        )
    
    with col2:
        location_options = [
            "United States",
            "European Union",
            "United Kingdom",
            "Canada",
            "Australia",
            "Asia-Pacific (APAC)"
        ]
        from components.ui_helpers import multiselect_with_select_all
        locations = multiselect_with_select_all(
            "Operating Locations *",
            options=location_options,
            default=defaults.get("locations", []),
            key="calendar_operating_locations",
            help="Select every location where your organization operates (Required)"
        )
        
        industry_options = [
            "-- Select industry --",
            "Technology and software",
            "Banking and financial services",
            "Healthcare and life sciences",
            "Retail and e-commerce",
            "Manufacturing and logistics",
            "Education",
            "Government and public sector",
            "Other / mixed"
        ]
        default_industry_index = (
            industry_options.index(defaults.get("industry", industry_options[0]))
            if defaults.get("industry", industry_options[0]) in industry_options
            else 0
        )
        industry = st.selectbox(
            "Industry *",
            options=industry_options,
            index=default_industry_index,
            help="Choose the option that best describes your primary industry."
        )
    
    with col3:
        employee_count = st.text_input(
            "Number of Employees *",
            value=defaults.get("employee_count", ""),
            placeholder="Enter total employees (e.g., 250)",
            help="Enter the approximate number of employees. Whole numbers only."
        )
        
        annual_revenue = st.text_input(
            "Annual Revenue ($) *",
            value=defaults.get("annual_revenue", ""),
            placeholder="Enter annual revenue (e.g., 1250000)",
            help="Enter your approximate annual revenue in US dollars."
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        has_personal_data = st.checkbox(
            "We handle customer or user personal data",
            value=defaults.get("has_personal_data", False)
        )
        is_regulated = st.checkbox(
            "We are directly regulated by a government agency",
            value=defaults.get("is_regulated", False)
        )
    
    with col2:
        previous_violations = st.text_input(
            "Previous Compliance Violations",
            value=defaults.get("previous_violations", ""),
            placeholder="Enter number (leave blank if none)",
            help="How many compliance violations have occurred previously? Enter 0 if none."
        )
    
    st.markdown("---")
    submitted = st.form_submit_button("📋 Generate Calendar", width='stretch', type="primary")

if submitted:
    errors = []
    
    # Basic validation --------------------------------------------------------
    if not entity_name or not entity_name.strip():
        errors.append("**Organization Name**: Please enter your organization name.")
    elif len(entity_name.strip()) < 2:
        errors.append("**Organization Name**: Please enter a name that is at least 2 characters long.")
    
    if entity_type == "-- Select organization type --":
        errors.append("**Organization Type**: Please choose your organization type from the dropdown.")
    
    if not locations:
        errors.append("**Operating Locations**: Please select at least one location where you operate.")
    
    if industry == "-- Select industry --":
        errors.append("**Industry**: Please choose your primary industry.")
    
    employee_count_value = parse_positive_int(employee_count, "Number of Employees", errors, minimum=1)
    annual_revenue_value = parse_positive_float(annual_revenue, "Annual Revenue", errors, minimum=0)
    previous_violations_value = parse_optional_int(previous_violations, "Previous Compliance Violations", errors, minimum=0)
    if previous_violations_value is None:
        previous_violations_value = 0
    
    if errors:
        st.error("⚠️ **We need a little more information:**")
        for idx, error in enumerate(errors, 1):
            st.markdown(f"{idx}. {error}")
        st.info("💡 Scroll up, complete the missing fields, then press **Generate Calendar** again.")
    else:
        # Friendly-to-API mappings --------------------------------------------
        type_map = {
            "Startup (new business)": "STARTUP",
            "Private company": "PRIVATE_COMPANY",
            "Public company (traded)": "PUBLIC_COMPANY",
            "Bank or financial institution": "FINANCIAL_INSTITUTION",
            "Healthcare provider": "HEALTHCARE",
            "Non-profit organization": "NONPROFIT",
            "Government agency": "GOVERNMENT"
        }
        
        industry_map = {
            "Technology and software": "TECHNOLOGY",
            "Banking and financial services": "FINANCIAL_SERVICES",
            "Healthcare and life sciences": "HEALTHCARE",
            "Retail and e-commerce": "RETAIL",
            "Manufacturing and logistics": "MANUFACTURING",
            "Education": "EDUCATION",
            "Government and public sector": "GOVERNMENT",
            "Other / mixed": "OTHER"
        }
        
        location_map = {
            "United States": "US",
            "European Union": "EU",
            "United Kingdom": "UK",
            "Canada": "CANADA",
            "Australia": "APAC",
            "Asia-Pacific (APAC)": "APAC"
        }
        location_code_to_label = {code: label for label, code in location_map.items()}
        
        location_codes = [location_map[loc] for loc in locations]
        
        # Create placeholders for progress indicators
        progress_container = st.empty()
        steps_container = st.empty()
        
        with st.spinner("🤖 AI Agent is generating your compliance calendar..."):
            try:
                # Stage 1: Analyzing entity
                with progress_container.container():
                    st.info("📊 Analyzing entity profile and risk factors...")
                import time
                time.sleep(0.3)
                
                # Stage 2: Identifying regulations
                with progress_container.container():
                    st.info("📜 Identifying applicable regulations...")
                with steps_container.container():
                    st.caption(f"✓ Analyzing {len(location_codes)} jurisdiction(s): {', '.join(location_codes)}")
                time.sleep(0.3)
                
                # Stage 3: Calculating tasks
                with progress_container.container():
                    st.info("📋 Calculating task frequencies and requirements...")
                with steps_container.container():
                    st.caption(f"✓ {len(location_codes)} jurisdictions analyzed")
                    st.caption(f"✓ Entity type: {entity_type}")
                    st.caption(f"✓ Industry: {industry}")
                time.sleep(0.3)
                
                # Stage 4: Calling AI
                with progress_container.container():
                    st.info("🤖 AI Agent is evaluating compliance requirements...")
                with steps_container.container():
                    st.caption(f"✓ Profile complete")
                    st.caption(f"✓ Generating task recommendations...")
                
                payload = {
                    "entity_name": entity_name.strip(),
                    "locations": location_codes,
                    "entity_type": type_map.get(entity_type),
                    "industry": industry_map.get(industry),
                    "employee_count": employee_count_value,
                    "annual_revenue": annual_revenue_value,
                    "has_personal_data": has_personal_data,
                    "is_regulated": is_regulated,
                    "previous_violations": previous_violations_value
                }
                
                api = APIClient()
                try:
                    response = api.post("/api/v1/entity/analyze", payload, timeout=30)
                    
                    # Stage 5: Prioritizing
                    with progress_container.container():
                        st.info("🎯 Prioritizing deadlines and generating calendar...")
                    with steps_container.container():
                        st.caption(f"✓ Tasks generated")
                        st.caption(f"✓ Calculating priorities...")
                    time.sleep(0.2)
                    
                    # Clear progress indicators
                    progress_container.empty()
                    steps_container.empty()
                    
                    if not response.success:
                        display_api_error(response)
                        st.stop()
                    
                    result = response.data or {}
                    if not result:
                        st.error("❌ **Empty Response**: The API returned no data. Please try again.")
                        st.stop()
                except Exception as api_error:
                    progress_container.empty()
                    steps_container.empty()
                    st.error(f"❌ **API Error**: {str(api_error)}")
                    st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify your network connection\n3. Try again in a few moments")
                    st.stop()
                
                # Add timestamp for data freshness tracking if not present
                if "last_updated" not in result:
                    from datetime import datetime
                    result["last_updated"] = datetime.now().isoformat()
                
                st.success(f"✅ Calendar generated for {result['entity_name']}!")
                
                # Display data freshness
                if result.get("last_updated"):
                    try:
                        last_updated_dt = datetime.fromisoformat(result["last_updated"])
                        st.caption(f"📅 Calendar generated: {last_updated_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    except (ValueError, TypeError):
                        pass
                
                # Summary
                st.markdown("---")
                st.markdown("## 📊 Summary")
                
                summary = result["summary"]
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Tasks", summary["total_tasks"])
                with col2:
                    st.metric("Autonomous", summary["decisions"].get("AUTONOMOUS", 0))
                with col3:
                    st.metric("Review Required", summary["decisions"].get("REVIEW_REQUIRED", 0))
                with col4:
                    st.metric("Escalate", summary["decisions"].get("ESCALATE", 0))
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("High Risk", summary["high_risk_tasks"])
                with col2:
                    st.metric("Medium Risk", summary["medium_risk_tasks"])
                with col3:
                    st.metric("Low Risk", summary["low_risk_tasks"])
                with col4:
                    autonomy_pct = summary["autonomous_percentage"]
                    st.metric("Autonomy Rate", f"{autonomy_pct:.1f}%")
                
                # Applicable Regulations
                if result["applicable_regulations"]:
                    st.markdown("### 📜 Applicable Regulations")
                    for reg in result["applicable_regulations"]:
                        st.info(f"• {reg}")
                
                # Risk Analysis Section
                st.markdown("---")
                st.markdown("## ⚠️ Risk Analysis")
                
                high_risk_tasks = [task for task in result["tasks"] if task["risk_level"] == "HIGH"]
                
                # Generate entity-specific risk analysis
                entity_context = f"""
                **Entity-Specific Risk Assessment for {result['entity_name']}:**
                
                - **Organization Type:** {entity_type} with {employee_count_value} employees
                - **Industry:** {industry} (subject to industry-specific regulations)
                - **Operating Jurisdictions:** {len(location_codes)} jurisdiction(s) including {', '.join([location_code_to_label.get(code, code) for code in location_codes[:3]])}
                - **Data Handling:** {"Processes customer/user data" if has_personal_data else "No customer data processing"}{", operates under regulatory oversight" if is_regulated else ""}
                """
                
                if not high_risk_tasks:
                    st.success("✅ **No high-risk tasks identified** - Your compliance calendar contains only low to medium risk items.")
                    st.info(entity_context)
                    st.markdown(f"""
                    **Why this assessment:** Given your organization's profile ({industry}, {employee_count_value} employees), 
                    the identified compliance tasks are within normal operational bounds. Your {len(result['tasks'])} tasks are manageable 
                    with existing resources.
                    """)
                else:
                    st.warning(f"⚠️ **{len(high_risk_tasks)} high-risk tasks require immediate attention**")
                    st.info(entity_context)
                    st.markdown(f"""
                    **Why this matters for {result['entity_name']}:** 
                    As a {entity_type} in the {industry} sector with {employee_count_value} employees, 
                    you face elevated compliance requirements. Operating across {len(location_codes)} jurisdiction(s) increases regulatory complexity. 
                    {"Your handling of customer data amplifies privacy/security obligations." if has_personal_data else ""}
                    {"As a regulated entity, non-compliance carries significant penalties." if is_regulated else ""}
                    High-risk tasks require expert review or legal counsel before proceeding.
                    """)
                    
                    for task in high_risk_tasks[:3]:  # Show top 3 high-risk tasks
                        deadline = datetime.fromisoformat(task["deadline"]).strftime("%B %d, %Y") if task.get("deadline") else "No deadline set"
                        st.error(f"""
                        **{task['task_name']}**  
                        Due: {deadline}  
                        Action Required: {show_decision_badge(task['decision'])}
                        """)
                    
                    if len(high_risk_tasks) > 3:
                        st.caption(f"+ {len(high_risk_tasks) - 3} more high-risk tasks (see full calendar below)")
                
                # Tasks by Priority
                st.markdown("---")
                st.markdown("## 📋 Your Compliance Tasks by Priority")
                st.markdown("Tasks are organized by urgency based on deadlines and risk levels. Focus on high-priority items first.")
                
                # Helper function to calculate days until deadline
                def days_until_deadline(task):
                    if not task.get("deadline"):
                        return 999  # Tasks without deadlines go to low priority
                    try:
                        deadline_date = datetime.fromisoformat(task["deadline"])
                        today = datetime.now()
                        return (deadline_date - today).days
                    except:
                        return 999
                
                # Helper function to determine priority based on deadline AND risk
                def calculate_priority(task):
                    """
                    Priority calculation:
                    - HIGH: Due in ≤7 days OR High risk + due in ≤30 days
                    - MEDIUM: Due in 8-30 days OR Medium/High risk + due in ≤60 days
                    - LOW: Due in 31+ days OR no deadline
                    """
                    days_left = days_until_deadline(task)
                    risk_level = task.get("risk_level", "LOW")
                    
                    # HIGH PRIORITY rules
                    if days_left <= 7:
                        return "HIGH", days_left
                    if risk_level == "HIGH" and days_left <= 30:
                        return "HIGH", days_left
                    
                    # MEDIUM PRIORITY rules
                    if days_left <= 30:
                        return "MEDIUM", days_left
                    if risk_level in ["HIGH", "MEDIUM"] and days_left <= 60:
                        return "MEDIUM", days_left
                    
                    # LOW PRIORITY (everything else)
                    return "LOW", days_left
                
                # Categorize tasks by priority with enhanced logic
                high_priority = []
                medium_priority = []
                low_priority = []
                
                # Debug option - add at top of page for testing
                show_debug = st.checkbox("🔍 Show Priority Calculation Debug", value=False, help="See how each task is prioritized")
                
                for task in result["tasks"]:
                    days_left = days_until_deadline(task)
                    task["days_until_deadline"] = days_left
                    
                    priority, _ = calculate_priority(task)
                    task["calculated_priority"] = priority
                    
                    # Debug output
                    if show_debug:
                        st.write(f"**Task:** {task.get('task_name', 'Unknown')[:50]}... | **Risk:** {task.get('risk_level')} | **Days:** {days_left} → **Priority:** {priority}")
                    
                    if priority == "HIGH":
                        high_priority.append(task)
                    elif priority == "MEDIUM":
                        medium_priority.append(task)
                    else:
                        low_priority.append(task)
                
                # Sort each priority group by days left (most urgent first)
                high_priority.sort(key=lambda x: x["days_until_deadline"])
                medium_priority.sort(key=lambda x: x["days_until_deadline"])
                low_priority.sort(key=lambda x: x["days_until_deadline"])
                
                if show_debug:
                    st.info(f"✅ Priority Sorting Complete: {len(high_priority)} HIGH, {len(medium_priority)} MEDIUM, {len(low_priority)} LOW")
                    st.markdown("---")
                
                # Filtering Controls
                st.markdown("### 🔍 Filter Tasks")
                filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
                
                with filter_col1:
                    from components.ui_helpers import multiselect_with_select_all
                    filter_priority = multiselect_with_select_all(
                        "Priority",
                        options=["HIGH", "MEDIUM", "LOW"],
                        default=["HIGH", "MEDIUM", "LOW"],
                        key="filter_priority_calendar",
                        help="Filter by priority level"
                    )
                
                with filter_col2:
                    # Extract unique regulations
                    all_regs = set()
                    for task in result["tasks"]:
                        if task.get("reasoning_summary"):
                            # Try to extract regulation names from reasoning
                            for reg in ["GDPR", "HIPAA", "CCPA", "SOX", "PCI DSS", "ISO 27001"]:
                                if reg in task["reasoning_summary"].upper():
                                    all_regs.add(reg)
                    
                    regulation_options = sorted(list(all_regs)) if all_regs else ["All"]
                    filter_regulation = multiselect_with_select_all(
                        "Regulation",
                        options=regulation_options,
                        default=regulation_options,
                        key="filter_regulation_calendar",
                        help="Filter by regulation type"
                    )
                
                with filter_col3:
                    filter_risk = multiselect_with_select_all(
                        "Risk Level ℹ️",
                        options=["HIGH", "MEDIUM", "LOW"],
                        default=["HIGH", "MEDIUM", "LOW"],
                        key="filter_risk_calendar",
                        help="Filter by risk level. Risk levels (LOW/MEDIUM/HIGH) indicate the potential impact of non-compliance."
                    )
                
                with filter_col4:
                    filter_days = st.selectbox(
                        "Due Date",
                        options=["All", "Overdue", "This week (≤7 days)", "This month (≤30 days)", "Beyond 30 days"],
                        index=0,
                        help="Filter by due date range"
                    )
                
                # Apply filters
                def apply_filters(tasks, filter_priority, filter_risk, filter_regulation, filter_days):
                    filtered = []
                    for task in tasks:
                        # Priority filter
                        if task.get("calculated_priority") not in filter_priority:
                            continue
                        
                        # Risk filter
                        if task.get("risk_level") not in filter_risk:
                            continue
                        
                        # Regulation filter (if any regulations selected)
                        if filter_regulation and filter_regulation != ["All"]:
                            task_reasoning = task.get("reasoning_summary", "").upper()
                            if not any(reg in task_reasoning for reg in filter_regulation):
                                continue
                        
                        # Days filter
                        days_left = task.get("days_until_deadline", 999)
                        if filter_days == "Overdue" and days_left >= 0:
                            continue
                        elif filter_days == "This week (≤7 days)" and days_left > 7:
                            continue
                        elif filter_days == "This month (≤30 days)" and days_left > 30:
                            continue
                        elif filter_days == "Beyond 30 days" and days_left <= 30:
                            continue
                        
                        filtered.append(task)
                    
                    return filtered
                
                # Apply filters to each priority group
                high_priority = apply_filters(high_priority, filter_priority, filter_risk, filter_regulation, filter_days)
                medium_priority = apply_filters(medium_priority, filter_priority, filter_risk, filter_regulation, filter_days)
                low_priority = apply_filters(low_priority, filter_priority, filter_risk, filter_regulation, filter_days)
                
                # Show filter summary
                total_after_filter = len(high_priority) + len(medium_priority) + len(low_priority)
                if total_after_filter < len(result["tasks"]):
                    st.caption(f"📊 Showing {total_after_filter} of {len(result['tasks'])} tasks after filters")
                
                st.markdown("---")
                
                # Friendly category names
                category_friendly = {
                    "POLICY_REVIEW": "Policy Review & Update",
                    "SECURITY_AUDIT": "Security Check",
                    "DATA_PRIVACY": "Data Privacy Task",
                    "REGULATORY_FILING": "Government Filing",
                    "RISK_ASSESSMENT": "Risk Assessment",
                    "CONTRACT_REVIEW": "Contract Review",
                    "FINANCIAL_REPORTING": "Financial Reporting",
                    "INCIDENT_RESPONSE": "Incident Response",
                    "GENERAL_INQUIRY": "General Compliance Task"
                }
                
                # Helper function to get color-coded due date badge
                def get_due_date_badge(days_left):
                    if days_left < 0:
                        return "🔴", f"OVERDUE by {abs(days_left)} day{'s' if abs(days_left) != 1 else ''}", "#fee2e2"
                    elif days_left == 0:
                        return "🔴", "DUE TODAY", "#fee2e2"
                    elif days_left <= 3:
                        return "🔴", f"{days_left} day{'s' if days_left != 1 else ''} remaining", "#fee2e2"
                    elif days_left <= 7:
                        return "🟠", f"{days_left} days remaining", "#fed7aa"
                    elif days_left <= 14:
                        return "🟡", f"{days_left} days remaining", "#fef3c7"
                    elif days_left <= 30:
                        return "🟡", f"{days_left} days remaining", "#fef3c7"
                    else:
                        return "🟢", f"{days_left} days remaining", "#d1fae5"
                
                # Display HIGH PRIORITY tasks
                st.markdown("### 🔴 HIGH PRIORITY (Urgent - Action Required)")
                if not high_priority:
                    st.success("✅ No urgent tasks - you're all caught up for this week!")
                else:
                    # Note: This count uses frontend priority calculation (days + risk), not just risk level
                    # Priority calculation: HIGH = ≤7 days OR High risk + ≤30 days
                    st.warning(f"⚠️ **{len(high_priority)} high-priority tasks need immediate attention**")
                    st.caption(f"ℹ️ **High-Priority Tasks**: Tasks due in ≤7 days OR high-risk tasks due in ≤30 days. Based on calendar generated: {result.get('last_updated', 'N/A')}")
                    
                    for task in high_priority:
                        days_left = task["days_until_deadline"]
                        deadline_str = datetime.fromisoformat(task["deadline"]).strftime("%B %d, %Y") if task.get("deadline") else "No deadline"
                        
                        # Get color-coded badge
                        emoji, urgency_text, bg_color = get_due_date_badge(days_left)
                        
                        # Enhanced expander title with visual indicators
                        risk_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(task.get("risk_level"), "⚪")
                        expander_title = f"{risk_emoji} {task['task_name']} — {emoji} {urgency_text}"
                        
                        with st.expander(expander_title, expanded=True):
                            st.markdown(f"#### 📌 What")
                            st.markdown(f"**{task['task_name']}**")
                            st.markdown(task['description'])
                            
                            st.markdown(f"#### When")
                            st.markdown(f"**Deadline:** {deadline_str} ({urgency_text})")
                            st.markdown(f"**Frequency:** {task['frequency'].title()}")
                            
                            st.markdown(f"#### 📜 Why")
                            category_name = category_friendly.get(task['category'], task['category'])
                            st.markdown(f"**Category:** {category_name}")
                            if task.get("reasoning_summary"):
                                reasons = task["reasoning_summary"].split("|")
                                for reason in reasons[:2]:  # Show first 2 reasons
                                    if reason.strip():
                                        st.markdown(f"- {reason.strip()}")
                            
                            st.markdown(f"#### ✅ Action")
                            decision_actions = {
                                "AUTONOMOUS": "✅ **You can proceed independently** - Handle this task on your own",
                                "REVIEW_REQUIRED": "👥 **Get approval first** - Consult with your manager or compliance team before proceeding",
                                "ESCALATE": "🚨 **Expert required** - This needs a compliance specialist or legal counsel"
                            }
                            st.markdown(decision_actions.get(task['decision'], task['decision']))
                            st.markdown(f"**Risk Level:** {show_risk_badge(task['risk_level'])} | **Confidence:** {task['confidence']*100:.1f}%")
                
                st.markdown("---")
                
                # Display MEDIUM PRIORITY tasks
                st.markdown("### 🟡 MEDIUM PRIORITY (Plan Ahead)")
                if not medium_priority:
                    st.info("✅ No medium-priority tasks at this time")
                else:
                    st.info(f"📋 **{len(medium_priority)} tasks** to plan for this month")
                    
                    for task in medium_priority:
                        days_left = task["days_until_deadline"]
                        deadline_str = datetime.fromisoformat(task["deadline"]).strftime("%B %d, %Y") if task.get("deadline") else "No deadline"
                        
                        # Get color-coded badge
                        emoji, urgency_text, bg_color = get_due_date_badge(days_left)
                        
                        # Enhanced expander title with visual indicators
                        risk_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(task.get("risk_level"), "⚪")
                        expander_title = f"{risk_emoji} {task['task_name']} — {emoji} {urgency_text}"
                        
                        with st.expander(expander_title):
                            st.markdown(f"#### 📌 What")
                            st.markdown(f"**{task['task_name']}**")
                            st.markdown(task['description'])
                            
                            st.markdown(f"#### When")
                            st.markdown(f"**Deadline:** {deadline_str} (in {days_left} days)")
                            st.markdown(f"**Frequency:** {task['frequency'].title()}")
                            
                            st.markdown(f"#### 📜 Why")
                            category_name = category_friendly.get(task['category'], task['category'])
                            st.markdown(f"**Category:** {category_name}")
                            if task.get("reasoning_summary"):
                                reasons = task["reasoning_summary"].split("|")
                                for reason in reasons[:2]:
                                    if reason.strip():
                                        st.markdown(f"- {reason.strip()}")
                            
                            st.markdown(f"#### ✅ Action")
                            decision_actions = {
                                "AUTONOMOUS": "✅ **You can proceed independently** when ready",
                                "REVIEW_REQUIRED": "👥 **Get approval first** - Schedule time with your manager or compliance team",
                                "ESCALATE": "🚨 **Expert required** - Coordinate with compliance specialist or legal counsel"
                            }
                            st.markdown(decision_actions.get(task['decision'], task['decision']))
                            st.markdown(f"**Risk Level:** {show_risk_badge(task['risk_level'])} | **Confidence:** {task['confidence']*100:.1f}%")
                
                st.markdown("---")
                
                # Display LOW PRIORITY tasks - cleaned up UI
                st.markdown("### 🟢 LOW PRIORITY (Future Planning)")
                if not low_priority:
                    st.info("✅ No long-term tasks at this time")
                else:
                    st.caption(f"📋 {len(low_priority)} tasks for future planning — expand for details")
                    
                    # Show collapsed by default for low priority with cleaner layout
                    for idx, task in enumerate(low_priority):
                        days_left = task["days_until_deadline"]
                        if days_left == 999:
                            deadline_str = "No deadline"
                            urgency_text = "Ongoing"
                        else:
                            deadline_str = datetime.fromisoformat(task["deadline"]).strftime("%b %d, %Y")
                            urgency_text = f"Due in {days_left} days"
                        
                        # Cleaner expander title
                        risk_badge = show_risk_badge(task['risk_level'])
                        expander_title = f"{task['task_name']} — {urgency_text}"
                        
                        with st.expander(expander_title, expanded=False):
                            # Compact single-line info display
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.markdown(f"**{task['task_name']}**")
                                st.caption(task['description'])
                            
                            with col2:
                                st.markdown(f"**{deadline_str}**")
                                st.caption(f"{category_friendly.get(task['category'], task['category'])}")
                            
                            # Action & Risk in single line
                            decision_icon = {"AUTONOMOUS": "✅", "REVIEW_REQUIRED": "👥", "ESCALATE": "🚨"}.get(task['decision'], "•")
                            decision_text = {"AUTONOMOUS": "Proceed independently", "REVIEW_REQUIRED": "Get approval", "ESCALATE": "Expert required"}.get(task['decision'], task['decision'])
                            st.markdown(f"{decision_icon} {decision_text} • Risk: {risk_badge} • Confidence: {task['confidence']*100:.0f}%")
                        
                        # Add spacing between tasks
                        if idx < len(low_priority) - 1:
                            st.markdown("")
                
                # Export options
                st.markdown("---")
                st.markdown("## 💾 Export Calendar")
                st.markdown("Download your complete compliance calendar in multiple formats for easy sharing and project management.")
                
                # Priority summary for user
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🔴 High Priority", len(high_priority), help="Due in 7 days or less")
                with col2:
                    st.metric("🟡 Medium Priority", len(medium_priority), help="Due in 8-30 days")
                with col3:
                    st.metric("🟢 Low Priority", len(low_priority), help="Due in 31+ days")
                
                st.markdown("---")
                
                # Prepare data for export
                export_data = []
                for task in result["tasks"]:
                    deadline = datetime.fromisoformat(task["deadline"]).strftime("%Y-%m-%d") if task.get("deadline") else "N/A"
                    frequency_friendly = task["frequency"].title()
                    
                    # Determine priority based on deadline
                    days_left = days_until_deadline(task)
                    if days_left <= 7:
                        priority = "HIGH"
                    elif days_left <= 30:
                        priority = "MEDIUM"
                    else:
                        priority = "LOW"
                    
                    # Friendly decision labels
                    decision_labels = {
                        "AUTONOMOUS": "✅ Proceed",
                        "REVIEW_REQUIRED": "⚠️ Review",
                        "ESCALATE": "🚨 Escalate"
                    }
                    decision_label = decision_labels.get(task["decision"], task["decision"])
                    
                    export_data.append({
                        "Priority": priority,
                        "Days Until Due": days_left if days_left != 999 else "No deadline",
                        "Task ID": task["task_id"],
                        "Task Name": task["task_name"],
                        "Description": task["description"],
                        "Category": category_friendly.get(task["category"], task["category"]),
                        "Frequency": frequency_friendly,
                        "Deadline": deadline,
                        "Risk Level": task["risk_level"].title(),
                        "Decision": decision_label,
                        "Confidence": f"{task['confidence']*100:.1f}%"
                    })
                
                df = pd.DataFrame(export_data)
                
                # Create enhanced text report
                friendly_jurisdictions = [location_code_to_label.get(code, code) for code in result['jurisdictions']]
                enhanced_report = f"""
COMPLIANCE CALENDAR - PRIORITY VIEW
====================================
Organization: {result['entity_name']}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Jurisdictions: {', '.join(friendly_jurisdictions)}

SUMMARY
-------
Total Tasks: {summary['total_tasks']}
  - High Priority (≤7 days): {len(high_priority)}
  - Medium Priority (8-30 days): {len(medium_priority)}
  - Low Priority (31+ days): {len(low_priority)}

Risk Breakdown:
  - High Risk: {summary['high_risk_tasks']}
  - Medium Risk: {summary['medium_risk_tasks']}
  - Low Risk: {summary['low_risk_tasks']}

Decisions:
  - Autonomous: {summary['decisions'].get('AUTONOMOUS', 0)}
  - Review Required: {summary['decisions'].get('REVIEW_REQUIRED', 0)}
  - Escalate: {summary['decisions'].get('ESCALATE', 0)}
  - Autonomy Rate: {summary['autonomous_percentage']:.1f}%

HIGH PRIORITY TASKS (Due in 7 days or less)
--------------------------------------------
"""
                # Add high priority tasks
                if not high_priority:
                    enhanced_report += "✓ No urgent tasks - all caught up!\n"
                else:
                    for task in high_priority:
                        days_left = task["days_until_deadline"]
                        deadline_str = datetime.fromisoformat(task["deadline"]).strftime("%Y-%m-%d") if task.get("deadline") else "N/A"
                        decision_labels = {
                            "AUTONOMOUS": "✅ Proceed",
                            "REVIEW_REQUIRED": "⚠️ Review",
                            "ESCALATE": "🚨 Escalate"
                        }
                        decision_label = decision_labels.get(task["decision"], task["decision"])
                        
                        if days_left < 0:
                            urgency = f"OVERDUE by {abs(days_left)} days"
                        elif days_left == 0:
                            urgency = "DUE TODAY"
                        else:
                            urgency = f"Due in {days_left} days"
                        
                        enhanced_report += f"\n🔴 {task['task_name']}\n"
                        enhanced_report += f"   What: {task['description'][:100]}...\n"
                        enhanced_report += f"   When: {deadline_str} ({urgency})\n"
                        enhanced_report += f"   Why: {category_friendly.get(task['category'], task['category'])}\n"
                        enhanced_report += f"   Action: {decision_label} | Risk: {task['risk_level']}\n"
                
                enhanced_report += "\n\nMEDIUM PRIORITY TASKS (Due in 8-30 days)\n"
                enhanced_report += "-------------------------------------------\n"
                if not medium_priority:
                    enhanced_report += "✓ No medium-priority tasks\n"
                else:
                    for task in medium_priority:
                        days_left = task["days_until_deadline"]
                        deadline_str = datetime.fromisoformat(task["deadline"]).strftime("%Y-%m-%d") if task.get("deadline") else "N/A"
                        decision_labels = {
                            "AUTONOMOUS": "✅ Proceed",
                            "REVIEW_REQUIRED": "⚠️ Review",
                            "ESCALATE": "🚨 Escalate"
                        }
                        decision_label = decision_labels.get(task["decision"], task["decision"])
                        enhanced_report += f"\n🟡 {task['task_name']} (in {days_left} days)\n"
                        enhanced_report += f"   Category: {category_friendly.get(task['category'], task['category'])}\n"
                        enhanced_report += f"   Deadline: {deadline_str}\n"
                        enhanced_report += f"   Action: {decision_label} | Risk: {task['risk_level']}\n"
                
                enhanced_report += "\n\nLOW PRIORITY TASKS (Due in 31+ days)\n"
                enhanced_report += "--------------------------------------\n"
                if not low_priority:
                    enhanced_report += "✓ No long-term tasks\n"
                else:
                    for task in low_priority:
                        days_left = task["days_until_deadline"]
                        if days_left == 999:
                            deadline_str = "No deadline"
                        else:
                            deadline_str = datetime.fromisoformat(task["deadline"]).strftime("%Y-%m-%d")
                        decision_labels = {
                            "AUTONOMOUS": "✅ Proceed",
                            "REVIEW_REQUIRED": "⚠️ Review",
                            "ESCALATE": "🚨 Escalate"
                        }
                        decision_label = decision_labels.get(task["decision"], task["decision"])
                        enhanced_report += f"\n🟢 {task['task_name']}\n"
                        enhanced_report += f"   Category: {category_friendly.get(task['category'], task['category'])}\n"
                        enhanced_report += f"   Deadline: {deadline_str}\n"
                        enhanced_report += f"   Action: {decision_label} | Risk: {task['risk_level']}\n"
                
                # Enhanced JSON export with metadata
                export_json = {
                    "export_metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "version": "1.0",
                        "export_type": "compliance_calendar"
                    },
                    "calendar": result,
                    "statistics": {
                        "total_tasks": summary['total_tasks'],
                        "high_priority": len(high_priority),
                        "medium_priority": len(medium_priority),
                        "low_priority": len(low_priority),
                        "high_risk": summary['high_risk_tasks'],
                        "medium_risk": summary['medium_risk_tasks'],
                        "low_risk": summary['low_risk_tasks'],
                        "autonomous_percentage": summary['autonomous_percentage']
                    }
                }
                
                # Determine risk level for filename (based on overall risk)
                if summary['high_risk_tasks'] > summary['total_tasks'] * 0.3:
                    overall_risk = "HIGH"
                elif summary['medium_risk_tasks'] > summary['total_tasks'] * 0.3:
                    overall_risk = "MEDIUM"
                else:
                    overall_risk = "LOW"
                
                # Render enhanced export section
                render_export_section(
                    data=result,
                    dataframe=df,
                    text_report=enhanced_report,
                    json_data=export_json,
                    prefix="calendar",
                    entity_name=entity_name,
                    task_category="ComplianceCalendar",
                    risk_level=overall_risk,
                    show_email=True,
                    email_api_endpoint=f"{API_BASE_URL}/api/v1/export/email"
                )
                
                st.caption("💾 Files download immediately. Check your browser's downloads folder.")
            
            except Exception as e:
                st.error(f"❌ **Calendar Generation Error: {type(e).__name__}**")
                st.markdown("---")
                st.warning(str(e))
                st.markdown("### What to do:")
                st.markdown("1. 🔄 **Try again** - Click 'Generate Calendar'")
                st.markdown("2. 🌐 **Refresh** - Press F5 and resubmit")
                st.markdown("3. 📞 **Contact support** - Describe what happened")
                st.info("💡 **Common fixes:**\n1. Check backend is running: `make status`\n2. Restart everything: `make restart`")
                with st.expander("🐛 Full Error"):
                    import traceback
                    st.code(traceback.format_exc())
                st.info("💡 Your entries are saved above.")

# Sidebar: Export History and Chat Assistant
with st.sidebar:
    show_logout_button()
    st.markdown("---")
    
    # Export History
    render_export_history()
    
    st.markdown("---")
    st.markdown("## 💬 AI Chat Assistant")
    st.caption("Ask about compliance tasks")
    
    # Render chat panel
    render_chat_panel(context_data={
        "page": "Compliance Calendar",
        "entity_name": "Calendar Generation",
        "task_description": "Ask questions about compliance tasks, deadlines, or requirements"
    })

# Help section
with st.expander("❓ How does this work?"):
    st.markdown("""
    ### Compliance Calendar Generation
    
    Our AI analyzes your organization's profile and automatically generates a comprehensive compliance calendar including:
    
    - **Regular Tasks**: Annual reviews, quarterly audits, monthly checks
    - **Risk Assessment**: Each task is evaluated for risk level
    - **Autonomy Decisions**: AI determines if you can proceed independently or need review
    - **Deadlines**: Calculated based on task frequency and regulatory requirements
    - **Complete Audit Trail**: Every decision is logged for compliance
    
    ### Understanding the Results
    
    - **🟢 LOW RISK**: Can typically proceed autonomously
    - **🟡 MEDIUM RISK**: Review recommended before proceeding
    - **🔴 HIGH RISK**: Expert involvement required
    
    - **✅ AUTONOMOUS**: You can handle this independently
    - **⚠️ REVIEW_REQUIRED**: Get approval before proceeding  
    - **🚨 ESCALATE**: Requires compliance specialist or legal counsel
    
    ### Export Options
    
    - **Excel/CSV**: Import into your project management tools
    - **JSON**: Use with other systems or APIs
    - **Text Report**: Print or share with stakeholders
    """)

