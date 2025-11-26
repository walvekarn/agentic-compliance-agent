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

# ============================================================================
# MAIN FORM
# ============================================================================
with st.form("agentic_analysis_form", clear_on_submit=False):
    st.markdown("## 📋 Analysis Request")
    
    col1, col2 = st.columns(2)
    
    with col1:
        entity_name = st.text_input(
            "Entity Name *",
            value="",
            placeholder="Enter entity name",
            help="Name of the organization to analyze"
        )
        
        employee_count = st.number_input(
            "Employee Count",
            min_value=1,
            value=50,
            help="Approximate number of employees"
        )
        
        # Locations/Jurisdictions
        location_options = [loc for loc in LOCATION_OPTIONS if loc != "-- Please select --"]
        locations = st.multiselect(
            "Operating Locations *",
            options=location_options,
            default=[],
            help="Select all jurisdictions where the entity operates"
        )
    
    with col2:
        # Industry - simple dropdown without "-- Please select --"
        industry_options = [opt for opt in INDUSTRY_OPTIONS if opt != "-- Please select --"]
        industry = st.selectbox(
            "Industry *",
            options=industry_options,
            help="Industry category"
        )
        
        # Priority dropdown
        priority = st.selectbox(
            "Priority *",
            options=["Low", "Medium", "High"],
            index=1,  # Default to Medium
            help="Task priority level"
        )
    
    st.markdown("---")
    
    # Task Description
    task_description = st.text_area(
        "Task Description *",
        value="",
        placeholder="Describe the compliance task to analyze. For example: 'Implement GDPR Article 30 records of processing activities' or 'Review privacy policy updates for a new feature rollout'",
        height=120,
        help="Detailed description of what needs to be analyzed"
    )
    
    st.markdown("---")
    
    # Submit button
    submitted = st.form_submit_button("🚀 Run Agentic Analysis", type="primary", use_container_width=True)
    
    if submitted:
        # Validation
        errors = []
        if not entity_name.strip():
            errors.append("Entity name is required")
        if not industry:
            errors.append("Industry is required")
        if not locations:
            errors.append("At least one operating location is required")
        if not task_description.strip():
            errors.append("Task description is required")
        
        if errors:
            st.error("**Please fix the following errors:**\n\n" + "\n".join([f"• {e}" for e in errors]))
        else:
            # Prepare API request
            request_payload = {
                "entity": {
                    "entity_name": entity_name,
                    "entity_type": "PRIVATE_COMPANY",  # Default
                    "locations": locations,
                    "industry": industry,
                    "employee_count": employee_count,
                    "has_personal_data": True,  # Default
                    "is_regulated": False,  # Default
                    "previous_violations": 0  # Default
                },
                "task": {
                    "task_description": task_description,
                    "task_category": "DATA_PROTECTION",  # Default
                    "priority": priority.upper(),
                    "deadline": None
                },
                "max_iterations": 10  # Default
            }
            
            # Call API with spinner
            with st.spinner("🤖 Agent is analyzing... This may take 60-90 seconds"):
                try:
                    response = api_client.post("/api/v1/agentic/analyze", request_payload, timeout=120)
                    
                    # Parse response
                    status, results, error, timestamp = parseAgenticResponse(response)
                    
                    if status == "completed" and results:
                        st.session_state.agentic_results = results
                        st.session_state.agentic_form_data = {
                            "entity_name": entity_name,
                            "task_description": task_description
                        }
                        st.success(f"✅ Analysis complete!")
                        st.rerun()
                    elif status == "timeout":
                        st.error(f"⏱️ **Timeout**: {error or 'Analysis timed out after 120 seconds'}")
                        st.info("💡 **Tip**: Try simplifying the task description or try again later.")
                    elif status == "error":
                        error_msg = error or "Unknown error occurred"
                        st.error(f"❌ **Error**: {error_msg}")
                        st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify your network connection\n3. Try again with a simpler task")
                    else:
                        display_api_error(response)
                except Exception as e:
                    st.error(f"❌ **API Error**: {str(e)}")
                    st.info("💡 **Troubleshooting**:\n1. Check that the backend is running\n2. Verify your network connection\n3. Try again in a few moments")

# ============================================================================
# DISPLAY RESULTS
# ============================================================================
if st.session_state.agentic_results:
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
        st.rerun()
