"""
Agentic Analysis - Advanced AI Reasoning
=========================================
Experimental agentic AI engine with plan-execute-reflect capabilities.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import json
import requests

# Add frontend directory to path
frontend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(frontend_dir))

from components.auth_utils import require_auth, show_logout_button
from components.session_manager import SessionManager
from components.api_client import APIClient, display_api_error, parseAgenticResponse
from components.constants import (
    INDUSTRY_OPTIONS, LOCATION_OPTIONS
)
from components.ui_helpers import apply_light_theme_css

# Page config
st.set_page_config(page_title="Agentic Analysis", page_icon="🤖", layout="wide")

# Apply light theme CSS only
apply_light_theme_css()

# Authentication
require_auth()

# Initialize session
SessionManager.init()

# Initialize API client
api_client = APIClient()

# Header
st.title("🤖 Agentic Analysis")
st.markdown("Advanced AI reasoning with transparent plan-execute-reflect cycles for deep compliance analysis")
st.caption("ℹ️ **Agentic**: AI systems that can autonomously plan, execute, and reflect on tasks. This experimental feature uses multi-step reasoning to provide deeper analysis.")

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if "agentic_results" not in st.session_state:
    st.session_state.agentic_results = None
if "agentic_form_data" not in st.session_state:
    st.session_state.agentic_form_data = {}
if "agentic_form_persistent" not in st.session_state:
    st.session_state.agentic_form_persistent = {}
if "agentic_analysis_in_progress" not in st.session_state:
    st.session_state.agentic_analysis_in_progress = False

# ============================================================================
# LOAD EXAMPLE FUNCTION
# ============================================================================
def load_example_data():
    """Load example data for testing"""
    return {
        "entity_name": "TechCorp Inc.",
        "industry": "Technology and software",
        "employee_count": 50,
        "operating_locations": ["United States (Federal)"],
        "task_description": "We need to update our privacy policy to comply with GDPR requirements for our EU customers. This involves reviewing data collection practices, updating consent mechanisms, and ensuring proper data subject rights are implemented.",
        "priority": "Medium"
    }

# ============================================================================
# MAIN FORM
# ============================================================================
# Quick action buttons before form
action_col1, action_col2 = st.columns([1, 5])
with action_col1:
    if st.button("⚡ Load Example", use_container_width=True):
        example = load_example_data()
        
        # Validate and fix locations to match LOCATION_OPTIONS
        location_options = [loc for loc in LOCATION_OPTIONS if loc != "-- Please select --"]
        example_locations = example.get("operating_locations", [])
        # Filter to only valid options that exist in LOCATION_OPTIONS
        valid_locations = [loc for loc in example_locations if loc in location_options]
        example["operating_locations"] = valid_locations
        
        # Clear widget session state keys BEFORE setting new values to avoid modification errors
        # This ensures widgets will use the default values from form_defaults
        widget_keys_to_clear = [
            "agentic_locations_multiselect",
        ]
        for key in widget_keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # Store example data in session state for form to use
        st.session_state["example_loaded_agentic"] = True
        st.session_state["example_data_agentic"] = example
        st.success("✅ Example data loaded! Fill the form below.")
        st.rerun()

# Get form defaults - prioritize persistent form data, then example data, then empty
form_defaults = {}
# First, use persistent form data if available (survives form submissions)
if st.session_state.get("agentic_form_persistent"):
    form_defaults = st.session_state["agentic_form_persistent"]
# Then, if example was just loaded, use example data and save to persistent
elif st.session_state.get("example_loaded_agentic") and st.session_state.get("example_data_agentic"):
    form_defaults = st.session_state["example_data_agentic"]
    # Save to persistent storage so it survives form submissions
    st.session_state["agentic_form_persistent"] = form_defaults.copy()
    # Clear the flag after using
    st.session_state["example_loaded_agentic"] = False

with st.form("agentic_analysis_form", clear_on_submit=False):
    st.markdown("## 📋 Analysis Request")
    
    col1, col2 = st.columns(2)
    
    with col1:
        entity_name = st.text_input(
            "Entity Name *",
            value=form_defaults.get("entity_name", ""),
            placeholder="Enter entity name",
            help="Name of the organization to analyze"
        )
        
        employee_count = st.number_input(
            "Employee Count",
            min_value=1,
            value=form_defaults.get("employee_count", 50),
            help="Approximate number of employees"
        )
        
        # Locations/Jurisdictions
        location_options = [loc for loc in LOCATION_OPTIONS if loc != "-- Please select --"]
        default_locations = form_defaults.get("operating_locations", [])
        # Filter to only valid options that exist in location_options
        valid_default_locations = [loc for loc in default_locations if loc in location_options]
        locations = st.multiselect(
            "Operating Locations *",
            options=location_options,
            default=valid_default_locations,
            key="agentic_locations_multiselect",
            help="Select all jurisdictions where the entity operates"
        )
    
    with col2:
        # Industry - simple dropdown without "-- Please select --"
        industry_options = [opt for opt in INDUSTRY_OPTIONS if opt != "-- Please select --"]
        default_industry = form_defaults.get("industry", industry_options[0] if industry_options else "")
        industry_index = industry_options.index(default_industry) if default_industry in industry_options else 0
        industry = st.selectbox(
            "Industry *",
            options=industry_options,
            index=industry_index,
            help="Industry category"
        )
        
        # Priority dropdown
        priority_options = ["Low", "Medium", "High"]
        default_priority = form_defaults.get("priority", "Medium")
        priority_index = priority_options.index(default_priority) if default_priority in priority_options else 1
        priority = st.selectbox(
            "Priority *",
            options=priority_options,
            index=priority_index,
            help="Task priority level"
        )
    
    st.markdown("---")
    
    # Task Description
    task_description = st.text_area(
        "Task Description *",
        value=form_defaults.get("task_description", ""),
        placeholder="Describe the compliance task to analyze. For example: 'Implement GDPR Article 30 records of processing activities' or 'Review privacy policy updates for a new feature rollout'",
        height=120,
        help="Detailed description of what needs to be analyzed"
    )
    
    st.markdown("---")
    
    # Show status if analysis is in progress
    is_analyzing = st.session_state.get("agentic_analysis_in_progress", False)
    if is_analyzing:
        st.info("🔄 **Analysis in Progress**: Please wait while the agentic engine processes your request. This may take a few moments...")
    
    # Submit button - disable if analysis is already in progress
    submit_label = "🔄 Analysis in Progress..." if is_analyzing else "🚀 Run Agentic Analysis"
    submitted = st.form_submit_button(
        submit_label, 
        type="primary", 
        use_container_width=True,
        disabled=is_analyzing,
        help="Analysis is currently running. Please wait for it to complete." if is_analyzing else "Start the agentic analysis"
    )
    
    if submitted:
        # Save form data to persistent storage so it survives reruns
        form_data_current = {
            "entity_name": entity_name,
            "industry": industry,
            "employee_count": employee_count,
            "operating_locations": locations,
            "task_description": task_description,
            "priority": priority
        }
        st.session_state["agentic_form_persistent"] = form_data_current
        
        # Validation - use current widget values, not form_defaults
        errors = []
        if not entity_name or not entity_name.strip():
            errors.append("Entity name is required")
        if not industry:
            errors.append("Industry is required")
        if not locations or len(locations) == 0:
            errors.append("At least one operating location is required")
        if not task_description or not task_description.strip():
            errors.append("Task description is required")
        
        if errors:
            st.error("**Please fix the following errors:**\n\n" + "\n".join([f"• {e}" for e in errors]))
            # Don't proceed if validation fails
        else:
            # Store payload for async processing (outside form to avoid blocking)
            st.session_state["agentic_request_payload"] = {
                "entity": {
                    "entity_name": entity_name.strip(),
                    "entity_type": "PRIVATE_COMPANY",
                    "locations": locations,
                    "industry": industry,
                    "employee_count": employee_count,
                    "has_personal_data": True,
                    "is_regulated": False,
                    "previous_violations": 0
                },
                "task": {
                    "task_description": task_description.strip(),
                    "task_category": "DATA_PROTECTION",
                    "priority": priority.upper(),
                    "deadline": None
                },
                "max_iterations": 10
            }
            st.session_state["agentic_form_data"] = {
                "entity_name": entity_name,
                "task_description": task_description
            }
            st.session_state["agentic_analysis_in_progress"] = True
            st.rerun()  # Rerun immediately - API call happens on next render

# ============================================================================
# PROCESS API CALL (Outside form - handles long-running operation)
# ============================================================================
if st.session_state.get("agentic_analysis_in_progress") and st.session_state.get("agentic_request_payload"):
    request_payload = st.session_state["agentic_request_payload"]
    
    # Progress indicator (outside form, so it persists)
    with st.spinner("🤖 **Processing**: This may take up to 2 minutes..."):
        try:
            response = api_client.post("/api/v1/agentic/analyze", request_payload, timeout=130)
            
            if response.success and response.data:
                status, results, error, timestamp = parseAgenticResponse(response)
                
                # FIXED: Show results even if status is not "completed" or if some fields are missing
                if results and isinstance(results, dict):
                    # Check if we have any meaningful data to show
                    has_plan = results.get("plan") and len(results.get("plan", [])) > 0
                    has_outputs = results.get("step_outputs") and len(results.get("step_outputs", [])) > 0
                    has_reflections = results.get("reflections") and len(results.get("reflections", [])) > 0
                    has_recommendation = results.get("final_recommendation") and results.get("final_recommendation") != "No recommendation available"
                    
                    if has_plan or has_outputs or has_reflections or has_recommendation or status == "completed":
                        st.session_state.agentic_results = results
                        del st.session_state["agentic_request_payload"]
                        st.session_state["agentic_analysis_in_progress"] = False
                        if status != "completed":
                            st.warning(f"⚠️ **Partial Results**: Analysis status is '{status}'. Some data may be incomplete.")
                        st.rerun()
                    else:
                        # No meaningful data
                        del st.session_state["agentic_request_payload"]
                        st.session_state["agentic_analysis_in_progress"] = False
                        st.error(f"❌ **No Results**: {error or 'Analysis completed but returned no data'}")
                elif status == "timeout":
                    del st.session_state["agentic_request_payload"]
                    st.session_state["agentic_analysis_in_progress"] = False
                    st.error(f"⏱️ **Timeout**: {error or 'Analysis exceeded time limit'}")
                    st.info("💡 **Tip**: Try simplifying the task description or try again later.")
                else:
                    del st.session_state["agentic_request_payload"]
                    st.session_state["agentic_analysis_in_progress"] = False
                    st.error(f"❌ **Analysis Failed**: {error or 'Unknown error'}")
                    st.info("💡 **Troubleshooting**: Check backend logs and try again.")
            else:
                del st.session_state["agentic_request_payload"]
                st.session_state["agentic_analysis_in_progress"] = False
                st.error(f"❌ **API Error**: {response.error or 'Backend returned an error'}")
                st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify your network connection\n3. Check backend logs for details")
                
        except requests.exceptions.Timeout:
            del st.session_state["agentic_request_payload"]
            st.session_state["agentic_analysis_in_progress"] = False
            st.error("⏱️ **Request Timeout**: The backend took too long to respond.")
            st.info("💡 **Tip**: Try simplifying the task description or check backend logs for issues.")
        except requests.exceptions.ConnectionError:
            del st.session_state["agentic_request_payload"]
            st.session_state["agentic_analysis_in_progress"] = False
            st.error("🔌 **Connection Error**: Cannot reach the backend server.")
            st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify the API_BASE_URL setting\n3. Check your network connection")
        except Exception as e:
            del st.session_state["agentic_request_payload"]
            st.session_state["agentic_analysis_in_progress"] = False
            st.error(f"❌ **Error**: {str(e)}")
            st.info("💡 **Troubleshooting**: Check backend logs for detailed error information.")
            import traceback
            with st.expander("🔍 Technical Details"):
                st.code(traceback.format_exc(), language="text")

# ============================================================================
# DISPLAY RESULTS
# ============================================================================
if st.session_state.get("agentic_results"):
    results = st.session_state.agentic_results
    
    st.markdown("---")
    st.markdown("## 📊 Analysis Results")
    
    # Status check
    status = results.get("status", "unknown")
    if status == "error":
        st.error("❌ **Analysis Error**: The analysis encountered an error. Please try again.")
        if results.get("error"):
            st.code(results.get("error"), language="text")
        st.stop()
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Plan",
        "⚙️ Outputs",
        "🔍 Reflections",
        "💡 Final Recommendation"
    ])
    
    # TAB 1: PLAN
    with tab1:
        st.markdown("### Execution Plan")
        st.markdown("The agentic AI generated the following strategic plan:")
        
        plan = results.get("plan", [])
        if plan and len(plan) > 0:
            for i, step in enumerate(plan, 1):
                st.markdown(f"#### Step {i}: {step.get('description', 'N/A')}")
                st.markdown(f"**Rationale:** {step.get('rationale', 'N/A')}")
                
                expected_tools = step.get('expected_tools', []) or step.get('tools', [])
                if expected_tools:
                    st.markdown(f"**Expected Tools:** {', '.join(expected_tools)}")
                
                dependencies = step.get('dependencies', [])
                if dependencies:
                    st.markdown(f"**Dependencies:** {', '.join(dependencies)}")
                
                st.markdown("---")
        else:
            st.info("📋 **No Plan Generated**: The execution plan will appear here once you run an analysis.")
    
    # TAB 2: STEP OUTPUTS
    with tab2:
        st.markdown("### Step Execution Results")
        st.markdown("Results from each step in the execution:")
        
        step_outputs = results.get("step_outputs", [])
        if step_outputs and len(step_outputs) > 0:
            for output in step_outputs:
                step_id = output.get("step_id", "unknown")
                status = output.get("status", "unknown")
                
                # Status icon
                status_icon = "✅" if status == "success" else "⏳" if status == "placeholder" else "❌"
                
                with st.expander(f"{status_icon} {step_id.replace('_', ' ').title()}", expanded=False):
                    st.markdown(f"**Status:** `{status}`")
                    
                    st.markdown("**Output:**")
                    if status == "failure" and output.get("error"):
                        st.error(output.get("error"))
                    output_text = output.get("output", "No output")
                    st.text(output_text)
                    
                    # Display findings
                    metrics = output.get("metrics", {})
                    findings = metrics.get("findings", []) or output.get("findings", [])
                    if findings:
                        st.markdown("**🔍 Key Findings:**")
                        for finding in findings:
                            st.markdown(f"- {finding}")
                    
                    # Display risks
                    risks = metrics.get("risks", []) or output.get("risks", [])
                    if risks:
                        st.markdown("**⚠️ Risks Identified:**")
                        for risk in risks:
                            st.markdown(f"- {risk}")
                    
                    # Display confidence
                    confidence = metrics.get("confidence", 0.0) or output.get("confidence", 0.0)
                    if confidence and confidence > 0:
                        st.metric("Confidence", f"{confidence:.2%}")
                    
                    tools_used = output.get("tools_used", [])
                    if tools_used:
                        st.markdown(f"**🔧 Tools Used:** {', '.join(tools_used)}")
        else:
            st.info("⚙️ **No Step Outputs Yet**: Step execution results will appear here once you run an analysis.")
    
    # TAB 3: REFLECTIONS
    with tab3:
        st.markdown("### Quality Reflections")
        st.markdown("AI critic's evaluation of each step:")
        
        reflections = results.get("reflections", [])
        if reflections and len(reflections) > 0:
            for reflection in reflections:
                step_id = reflection.get("step_id", "unknown")
                quality_score = reflection.get("quality_score", 0.0)
                
                st.markdown(f"#### {step_id.replace('_', ' ').title()}")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    correctness_score = reflection.get("correctness_score", None)
                    if correctness_score is not None:
                        st.metric("Correctness", f"{correctness_score:.2%}")
                    else:
                        st.metric("Correctness", "✅" if reflection.get("correctness") else "❌")
                with col2:
                    completeness_score = reflection.get("completeness_score", None)
                    if completeness_score is not None:
                        st.metric("Completeness", f"{completeness_score:.2%}")
                    else:
                        st.metric("Completeness", "✅" if reflection.get("completeness") else "❌")
                with col3:
                    st.metric("Confidence", f"{reflection.get('confidence', 0.0):.2%}")
                with col4:
                    st.metric("Quality Score", f"{quality_score:.2%}")
                
                issues = reflection.get("issues", [])
                if issues:
                    st.markdown("**⚠️ Issues Identified:**")
                    for issue in issues:
                        st.markdown(f"- {issue}")
                
                suggestions = reflection.get("suggestions", [])
                if suggestions:
                    st.markdown("**💡 Suggestions:**")
                    for suggestion in suggestions:
                        st.markdown(f"- {suggestion}")
                
                st.markdown("---")
        else:
            st.info("🔍 **No Reflections Yet**: Quality reflections will appear here once you run an analysis.")
    
    # TAB 4: FINAL RECOMMENDATION
    with tab4:
        st.markdown("### Final Recommendation")
        
        final_recommendation = results.get("final_recommendation", "")
        confidence_score = results.get("confidence_score", 0.0)
        
        if not final_recommendation or final_recommendation == "No recommendation available":
            st.info("💡 **No Recommendation Yet**: The final recommendation will appear here once you run an analysis.")
        else:
            st.markdown(f"**🎯 AI Recommendation:**")
            st.markdown(final_recommendation)
            st.markdown("---")
            st.metric("Confidence Score", f"{confidence_score:.2%}")
            
            # Download option
            st.markdown("---")
            form_data = st.session_state.agentic_form_data
            download_data = {
                "entity_name": form_data.get("entity_name", "Unknown"),
                "task_description": form_data.get("task_description", ""),
                "timestamp": datetime.now().isoformat(),
                "results": results
            }
            st.download_button(
                label="📥 Download Full Report",
                data=json.dumps(download_data, indent=2),
                file_name=f"agentic_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

# ============================================================================
# SIDEBAR INFO
# ============================================================================
with st.sidebar:
    show_logout_button()
    st.markdown("### 🤖 About Agentic Analysis")
    st.markdown("""
    This experimental feature uses an advanced agentic AI architecture with:
    
    **🎯 Planning Phase**
    - Strategic task decomposition
    - Tool selection
    - Dependency mapping
    
    **⚙️ Execution Phase**
    - Tool-augmented reasoning
    - Data gathering
    - Progressive analysis
    
    **🔍 Reflection Phase**
    - Quality assessment
    - Correctness validation
    - Iterative improvement
    """)
    
    if st.button("🔄 Reset Form", use_container_width=True):
        st.session_state.agentic_results = None
        st.session_state.agentic_form_data = {}
        st.session_state.agentic_form_persistent = {}
        st.session_state.agentic_analysis_in_progress = False
        # Clear example data flags
        if "example_loaded_agentic" in st.session_state:
            del st.session_state["example_loaded_agentic"]
        if "example_data_agentic" in st.session_state:
            del st.session_state["example_data_agentic"]
        st.rerun()
