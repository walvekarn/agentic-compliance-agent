"""
Results Display Orchestrator
=============================
Centralized rendering for ALL analysis results.

This module prevents accidental feature removals by providing a single,
structured entry point for displaying decision analysis results.

Architecture:
- render_results() is the main orchestrator
- Each feature has its own sub-component function
- Implemented components are imported from separate modules
- Missing components are placeholders with TODO notices
- No business logic - only display orchestration

Status:
- ✅ Implemented: confidence_meter, risk_breakdown, similar_cases, 
  proactive_suggestions, pattern_analysis, escalation_reason, action_plan,
  stakeholders, confidence_warnings, feedback_form, export_section,
  agent_explainability, counterfactuals, chat_integration
- ⚠️ Partial: decision_banner, risk_level_display, recommendations
"""

import streamlit as st
from typing import TYPE_CHECKING, Dict, Any, Optional, List

if TYPE_CHECKING:
    from backend.agent.risk_models import DecisionAnalysis

# Import sub-components
from .confidence_display import render_confidence_meter
from .risk_display import render_risk_breakdown
from .similar_cases_display import render_similar_cases
from .suggestions_display import render_proactive_suggestions


def _clean_reasoning_text(value: Any) -> str:
    """
    Normalize a reasoning string for display: strip whitespace/newlines and collapse multiple lines.
    """
    if value is None:
        return ""

    raw_text = str(value).strip()
    if not raw_text:
        return ""

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    return " ".join(lines).strip()


def _get_reasoning_steps(analysis: Dict[str, Any]) -> List[str]:
    why = analysis.get("why", {})
    steps = why.get("reasoning_steps") if isinstance(why, dict) else []
    if not isinstance(steps, list):
        return []
    cleaned = []
    for step in steps:
        sanitized = _clean_reasoning_text(step)
        if sanitized:
            cleaned.append(sanitized)
    return cleaned


def _render_decision_summary(analysis: Dict[str, Any], reasoning_steps: List[str]) -> None:
    decision = analysis.get("decision", "UNKNOWN")
    decision_display = decision.replace("_", " ").title() if isinstance(decision, str) else str(decision)
    decision_icon = {"AUTONOMOUS": "🟢", "REVIEW_REQUIRED": "🟡", "ESCALATE": "🔴"}.get(decision, "⚪")

    risk_level = analysis.get("risk_level", "UNKNOWN")
    risk_score = analysis.get("risk_score")
    risk_text = f"{risk_level.title()} ({risk_score:.2f})" if isinstance(risk_score, (int, float)) else risk_level.title()

    confidence = analysis.get("confidence", 0)
    confidence_pct = confidence * 100 if isinstance(confidence, (int, float)) else 0
    confidence_text = f"{confidence_pct:.0f}%"
    confidence_factors = (analysis.get("why", {}) or {}).get("confidence_factors") or []

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"### {decision_icon} **{decision_display}**")
        st.caption("Final decision")
    with col2:
        st.markdown(f"### ⚖️ Risk Level: **{risk_text}**")
        if reasoning_steps:
            st.caption(reasoning_steps[0])
    with col3:
        st.markdown(f"### 📍 Confidence: **{confidence_text}**")
        if confidence_factors:
            st.caption(" · ".join(confidence_factors[:2]))


def _render_why_section(reasoning_steps: List[str], is_simple_view: bool) -> None:
    st.markdown("### 💬 Why This Decision?")
    if not reasoning_steps:
        st.info("Reasoning steps are not available for this analysis.")
        return

    max_steps = len(reasoning_steps) if is_simple_view else len(reasoning_steps)
    display_steps = reasoning_steps[:3] if is_simple_view else reasoning_steps

    for idx, step in enumerate(display_steps, 1):
        st.markdown(f"{idx}. {step}")

    if is_simple_view and len(reasoning_steps) > 3:
        st.caption(f"...and {len(reasoning_steps) - 3} more steps in Detailed View.")


def _render_risk_section(analysis: Dict[str, Any], is_simple_view: bool) -> None:
    if is_simple_view:
        with st.expander("📊 Risk Factors (Detailed View)", expanded=False):
            render_risk_breakdown(analysis)
    else:
        render_risk_breakdown(analysis)


def _render_confidence_section(analysis: Dict[str, Any], is_simple_view: bool) -> None:
    if is_simple_view:
        with st.expander("📈 Confidence Details", expanded=False):
            render_confidence_meter(analysis)
    else:
        render_confidence_meter(analysis)


def render_reasoning_chain(analysis: Dict[str, Any]) -> None:
    """
    Wrapper for compatibility tests; renders the sanitized reasoning section.
    """
    is_simple_view = st.session_state.get("results_view_mode") == "Simple View"
    reasoning_steps = _get_reasoning_steps(analysis)
    _render_why_section(reasoning_steps, is_simple_view)


def render_results(analysis: Dict[str, Any]) -> None:
    """
    Main orchestrator for rendering all analysis results.
    
    This function calls sub-components in the correct order to display
    a complete, feature-rich analysis view.
    
    Args:
        analysis: Dictionary containing DecisionAnalysis data from API
    
    Architecture Note:
        Each sub-component is called unconditionally to ensure no features
        are accidentally dropped during refactoring. Components handle their
        own existence checks and graceful degradation.
    """
    
    if not analysis:
        st.warning("⚠️ No analysis results available")
        return
    
    # Add Simple/Detailed view toggle with persistent state
    if "results_view_mode" not in st.session_state:
        st.session_state.results_view_mode = "Simple View"
    
    view_mode = st.radio(
        "View Mode:",
        options=["Simple View", "Detailed View"],
        index=0 if st.session_state.results_view_mode == "Simple View" else 1,
        horizontal=True,
        key="results_view_mode_radio",
        help="Simple View: Shows decision, confidence, and risk level. Additional details (risk breakdown, recommendations, similar cases) are in expandable sections. Detailed View: Shows all sections expanded including full reasoning chain, action plan, pattern analysis, and AI transparency features."
    )
    
    # Update session state
    st.session_state.results_view_mode = view_mode
    is_simple_view = (view_mode == "Simple View")
    st.caption(
        "Simple View keeps the essentials top-of-mind; Detailed View expands every analytics section."
    )
    
    # Render results header with clearer structure
    st.markdown("---")
    st.markdown("## 🎯 Your Results")
    
    reasoning_steps = _get_reasoning_steps(analysis)
    render_decision_banner(analysis)
    _render_decision_summary(analysis, reasoning_steps)
    st.markdown("---")
    render_reasoning_chain(analysis)
    st.markdown("---")
    render_recommendations(analysis)
    st.markdown("---")
    _render_risk_section(analysis, is_simple_view)
    st.markdown("---")
    _render_confidence_section(analysis, is_simple_view)

    if not is_simple_view:
        render_proactive_suggestions(analysis)
        render_similar_cases(analysis)
        render_pattern_analysis(analysis)
        render_action_plan(analysis)
        render_stakeholders(analysis)
        render_escalation_reason(analysis)
        render_confidence_warnings(analysis)
        render_agent_explainability(analysis)
        render_counterfactual_explanations(analysis)
    else:
        st.info("💡 Switch to 'Detailed View' above to access advanced analytics, similar cases, and the full action plan.")
    
    # =========================================================================
    # USER INTERACTION (Always shown in both views)
    # =========================================================================
    # P0 - Missing: Human feedback for learning loop
    render_feedback_form(analysis)
    
    # P1 - Missing: Export options
    render_export_section(analysis)
    
    # P2 - Missing: Chat assistant context
    render_chat_integration(analysis)


# =============================================================================
# SUB-COMPONENT FUNCTIONS
# =============================================================================
# Each function is responsible for rendering one logical section.
# Components check for data availability and degrade gracefully.
# =============================================================================


def render_decision_banner(analysis: Dict[str, Any]) -> None:
    """
    Render the main decision outcome banner.
    
    Status: ⚠️ PARTIAL - Simplified in new UI
    Priority: P0 - Critical
    
    Note: Future enhancements could include:
    - Custom HTML/CSS styling with gradients and shadows
    - Detailed explanation text specific to decision type
    - Action-oriented messaging
    """
    decision = analysis.get('decision', 'UNKNOWN')
    
    if decision == "AUTONOMOUS":
        st.success("✅ **You Can Handle This Yourself**")
        st.markdown("This task is within normal bounds. Follow the guidance below and proceed confidently.")
    elif decision == "REVIEW_REQUIRED":
        st.warning("⚠️ **Get Approval Before Proceeding**")
        st.markdown("This task has moderate risk factors. Have your manager or compliance team review the details below before you take action. This is a precaution to ensure everything is handled properly.")
    else:
        st.error("🚨 **Expert Review Required**")
        st.markdown("This task has significant compliance implications. Please escalate to your compliance team or legal department before proceeding.")


# render_confidence_meter is now imported from confidence_display.py
# See: frontend/components/analyze_task/confidence_display.py


def render_risk_level_display(analysis: Dict[str, Any]) -> None:
    """
    Render risk level assessment.
    
    Status: ⚠️ PARTIAL - Basic display
    Priority: P0 - Critical
    
    Note: Future enhancements could include:
    - More detailed risk descriptions
    - Visual risk indicators
    - Risk score percentage
    """
    risk_level = analysis.get('risk_level', 'UNKNOWN')
    
    risk_map = {
        'LOW': ("🟢 Low", "Routine"),
        'MEDIUM': ("🟡 Medium", "Moderate"),
        'HIGH': ("🔴 High", "Complex")
    }
    
    risk_label, risk_desc = risk_map.get(risk_level, ("⚪ Unknown", "Not set"))
    st.metric("Risk Level", f"{risk_label} - {risk_desc}")


# render_proactive_suggestions is now imported from suggestions_display.py
# See: frontend/components/analyze_task/suggestions_display.py


# render_similar_cases is now imported from similar_cases_display.py
# See: frontend/components/analyze_task/similar_cases_display.py


def render_pattern_analysis(analysis: Dict[str, Any]) -> None:
    """
    Render pattern analysis summary.
    
    Status: ✅ IMPLEMENTED
    Priority: P1 - Important
    
    Displays historical pattern insights about organizational behavior
    when analyzing similar tasks.
    
    Args:
        analysis: Dictionary containing analysis results
                  Expected keys: pattern_analysis (Optional[str])
    
    Graceful degradation:
        - Missing pattern_analysis: shows nothing
        - Empty string: shows nothing
    """
    pattern_analysis = analysis.get('pattern_analysis')
    
    # Graceful exit if no pattern analysis
    if not pattern_analysis:
        return
    
    # Check if string is empty or whitespace only
    if not pattern_analysis.strip():
        return
    
    st.markdown("---")
    st.markdown("### 🧩 Pattern Analysis")
    st.markdown(pattern_analysis)


# render_risk_breakdown is now imported from risk_display.py
# See: frontend/components/analyze_task/risk_display.py


def render_recommendations(analysis: Dict[str, Any]) -> None:
    """
    Render action recommendations with sources.
    
    Status: ✅ IMPROVED
    Priority: P0 - Critical
    
    Provides specific, actionable recommendations based on actual analysis data.
    """
    decision = analysis.get('decision', '')
    task_type = analysis.get('task', {}).get('category', '') if isinstance(analysis.get('task'), dict) else ''
    task_description = analysis.get('task', {}).get('description', '') if isinstance(analysis.get('task'), dict) else ''
    risk_level = analysis.get('risk_level', 'MEDIUM')
    jurisdictions = analysis.get('entity_context', {}).get('jurisdictions', []) if isinstance(analysis.get('entity_context'), dict) else []
    industry = analysis.get('entity_context', {}).get('industry', '') if isinstance(analysis.get('entity_context'), dict) else ''
    
    # Get recommendations from API or generate context-specific ones
    recommendations = analysis.get('recommendations', [])
    
    # If no recommendations from API, generate context-specific ones
    if not recommendations:
        recommendations = _generate_context_specific_recommendations(
            decision, task_type, task_description, risk_level, jurisdictions, industry
        )
    
    if recommendations:
        st.markdown("---")
        st.markdown("## 💡 What To Do Next")
        
        for i, rec in enumerate(recommendations, 1):
            if isinstance(rec, dict):
                # Handle structured recommendation
                title = rec.get('title', f"Step {i}")
                description = rec.get('description', '')
                priority = rec.get('priority', 'MEDIUM')
                
                priority_emoji = "🔴" if priority == "HIGH" else "🟡" if priority == "MEDIUM" else "🟢"
                st.markdown(f"""
                <div style='background-color: #f8fafc; padding: 1rem; border-radius: 8px; margin: 0.75rem 0; border-left: 4px solid #3b82f6; color: #0f172a;'>
                    <strong>{priority_emoji} {i}. {title}</strong><br>
                    <span style='color: #0f172a;'>{description}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Handle string recommendation
                st.markdown(f"""
                <div style='background-color: #f8fafc; padding: 1rem; border-radius: 8px; margin: 0.75rem 0; border-left: 4px solid #3b82f6; color: #0f172a;'>
                    <strong>{i}.</strong> {rec}
                </div>
                """, unsafe_allow_html=True)
        
        # Add regulatory references if available
        regulatory_refs = analysis.get('regulatory_references', [])
        if regulatory_refs:
            st.markdown("---")
            st.markdown("### 📜 Regulatory References")
            for ref in regulatory_refs:
                if isinstance(ref, dict):
                    regulation = ref.get('regulation', 'N/A')
                    article = ref.get('article', '')
                    description = ref.get('description', '')
                    if article:
                        st.markdown(f"- **{regulation}**: {article} - {description}")
                    else:
                        st.markdown(f"- **{regulation}**: {description}")
                elif isinstance(ref, str):
                    st.markdown(f"- {ref}")


def _generate_context_specific_recommendations(
    decision: str,
    task_type: str,
    task_description: str,
    risk_level: str,
    jurisdictions: List[str],
    industry: str
) -> List[Dict[str, Any]]:
    """Generate context-specific recommendations based on analysis data."""
    recommendations = []
    
    # Decision-specific recommendations
    if decision == "AUTONOMOUS":
        recommendations.append({
            "title": "Review Applicable Regulations",
            "description": f"Review {task_type.replace('_', ' ').title() if task_type else 'compliance'} requirements for {', '.join(jurisdictions[:2]) if jurisdictions else 'your jurisdictions'}. Ensure you understand all obligations before proceeding.",
            "priority": "HIGH"
        })
        recommendations.append({
            "title": "Document Your Approach",
            "description": "Create a brief document outlining your compliance approach, rationale, and any controls you'll implement. This helps with future audits and demonstrates due diligence.",
            "priority": "MEDIUM"
        })
        recommendations.append({
            "title": "Implement and Monitor",
            "description": "Proceed with implementation and schedule a follow-up review in 30 days to ensure ongoing compliance and address any issues early.",
            "priority": "MEDIUM"
        })
    elif decision == "REVIEW_REQUIRED":
        recommendations.append({
            "title": "Schedule Review Meeting",
            "description": "Contact your manager or compliance team within the next 2-3 business days to schedule a review meeting. Don't delay - approval is required before proceeding.",
            "priority": "HIGH"
        })
        recommendations.append({
            "title": "Prepare Review Materials",
            "description": f"Prepare a brief summary of the {task_type.replace('_', ' ').title() if task_type else 'compliance'} requirements, your proposed approach, and any potential risks or concerns. Include relevant regulatory references.",
            "priority": "HIGH"
        })
        recommendations.append({
            "title": "Wait for Approval",
            "description": "Do not proceed with any actions until you receive explicit approval. Document the approved approach and any conditions or modifications requested.",
            "priority": "HIGH"
        })
    else:  # ESCALATE
        recommendations.append({
            "title": "Contact Compliance Officer Immediately",
            "description": "Reach out to your compliance officer or legal counsel within 24 hours. This task requires expert review due to its complexity and potential legal/regulatory implications.",
            "priority": "HIGH"
        })
        recommendations.append({
            "title": "Provide Task Details",
            "description": f"Share the task details: {task_description[:150] + '...' if len(task_description) > 150 else task_description}. Include all relevant context about jurisdictions, data types, and deadlines.",
            "priority": "HIGH"
        })
        recommendations.append({
            "title": "Do Not Proceed",
            "description": "Do not take any action until you receive expert guidance. Proceeding without proper review could result in compliance violations and penalties.",
            "priority": "HIGH"
        })
    
    # Add jurisdiction-specific recommendations
    if jurisdictions:
        if "EU" in str(jurisdictions) or "European Union" in str(jurisdictions):
            recommendations.append({
                "title": "GDPR Compliance Check",
                "description": "If this task involves personal data, ensure GDPR requirements are met, including data subject rights, lawful basis, and privacy notices.",
                "priority": "MEDIUM"
            })
        if "US_CA" in str(jurisdictions) or "California" in str(jurisdictions):
            recommendations.append({
                "title": "CCPA Compliance Check",
                "description": "If this task involves California residents' personal information, ensure CCPA requirements are met, including consumer rights and privacy disclosures.",
                "priority": "MEDIUM"
            })
    
    return recommendations


def render_action_plan(analysis: Dict[str, Any]) -> None:
    """
    Render step-by-step action plan with specific tasks.
    
    Status: ✅ IMPLEMENTED
    Priority: P0 - Critical
    
    Provides clear, actionable steps based on decision outcome.
    """
    decision = analysis.get('decision', '')
    task_type = analysis.get('task', {}).get('category', '') if isinstance(analysis.get('task'), dict) else ''
    risk_level = analysis.get('risk_level', 'MEDIUM')
    task_description = analysis.get('task', {}).get('description', 'N/A') if isinstance(analysis.get('task'), dict) else 'N/A'
    
    st.markdown("---")
    st.markdown("## ✅ Your Action Plan")
    
    if decision == "AUTONOMOUS":
        st.success("**You can proceed independently.** Follow these steps:")
        steps = [
            f"1. Review the {task_type.replace('_', ' ').title() if task_type else 'compliance'} requirements for your jurisdiction",
            "2. Document your compliance approach and rationale",
            "3. Implement the required controls or processes",
            "4. Schedule a follow-up review in 30 days to ensure ongoing compliance"
        ]
    elif decision == "REVIEW_REQUIRED":
        st.warning("**Get approval before proceeding.** Here's your plan:")
        steps = [
            "1. Schedule a meeting with your manager or compliance team within the next 2-3 business days",
            f"2. Prepare a brief summary of the {task_type.replace('_', ' ').title() if task_type else 'compliance'} requirements and your proposed approach",
            "3. Present your plan for review and address any concerns",
            "4. Document the approved approach and any conditions",
            "5. Implement only after receiving explicit approval"
        ]
    else:  # ESCALATE
        st.error("**Expert review required.** Take these steps immediately:")
        task_summary = task_description[:100] + "..." if len(task_description) > 100 else task_description
        steps = [
            "1. Contact your compliance officer or legal counsel immediately (within 24 hours)",
            f"2. Provide them with the task details: {task_summary}",
            "3. Request a compliance review meeting as soon as possible",
            "4. Do not proceed with any actions until expert guidance is received",
            "5. Document the expert's recommendations and follow them precisely"
        ]
    
    for step in steps:
        st.markdown(f"- {step}")
    
    # Add regulatory references if available
    regulatory_refs = analysis.get('regulatory_references', [])
    if regulatory_refs:
        st.markdown("---")
        st.markdown("### 📜 Regulatory References")
        for ref in regulatory_refs:
            if isinstance(ref, dict):
                regulation = ref.get('regulation', 'N/A')
                article = ref.get('article', '')
                description = ref.get('description', '')
                if article:
                    st.markdown(f"- **{regulation}**: {article} - {description}")
                else:
                    st.markdown(f"- **{regulation}**: {description}")


def render_stakeholders(analysis: Dict[str, Any]) -> None:
    """
    Render stakeholder involvement guidance.
    
    Status: ✅ IMPLEMENTED
    Priority: P0 - Critical
    
    Provides clear guidance on who to involve based on decision and risk level.
    """
    decision = analysis.get('decision', '')
    risk_level = analysis.get('risk_level', 'MEDIUM')
    
    if decision == "AUTONOMOUS":
        return  # No stakeholders needed for autonomous decisions
    
    st.markdown("---")
    st.markdown("## 👥 Who To Talk To")
    
    stakeholders = []
    
    if decision == "REVIEW_REQUIRED":
        stakeholders.append({
            "role": "Your Manager",
            "reason": "Required for approval before proceeding with this task",
            "when": "Before starting the task (within 2-3 business days)"
        })
        if risk_level == "HIGH":
            stakeholders.append({
                "role": "Compliance Team",
                "reason": "High-risk tasks require compliance review to ensure proper handling",
                "when": "As soon as possible, ideally before manager approval"
            })
    else:  # ESCALATE
        stakeholders.append({
            "role": "Compliance Officer",
            "reason": "Expert review required for complex compliance scenarios with significant legal or regulatory implications",
            "when": "Immediately (within 24 hours)"
        })
        stakeholders.append({
            "role": "Legal Counsel",
            "reason": "Legal implications require professional guidance to avoid violations and penalties",
            "when": "Before any action is taken"
        })
    
    for stakeholder in stakeholders:
        st.markdown(f"""
        <div style='background-color: #f0f9ff; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #3b82f6; color: #0f172a;'>
            <strong>👤 {stakeholder['role']}</strong><br>
            <small style='color: #0f172a;'><strong>Why:</strong> {stakeholder['reason']}</small><br>
            <small style='color: #0f172a;'><strong>When:</strong> {stakeholder['when']}</small>
        </div>
        """, unsafe_allow_html=True)


def render_escalation_reason(analysis: Dict[str, Any]) -> None:
    """
    Render escalation reason if applicable.
    
    Status: ✅ IMPLEMENTED
    Priority: P1 - Important
    
    Displays the specific reason why a task requires escalation.
    Only shown when decision is ESCALATE and reason is provided.
    
    Args:
        analysis: Dictionary containing analysis results
                  Expected keys: decision, escalation_reason
    
    Graceful degradation:
        - Not ESCALATE decision: shows nothing
        - Missing escalation_reason: shows nothing
        - Empty escalation_reason: shows nothing
    """
    decision = analysis.get('decision', '')
    escalation_reason = analysis.get('escalation_reason')
    
    # Only show for ESCALATE decisions
    if decision != 'ESCALATE':
        return
    
    # Graceful exit if no escalation reason
    if not escalation_reason:
        return
    
    # Check if string is empty or whitespace only
    if not escalation_reason.strip():
        return
    
    st.markdown("---")
    st.error(f"🚨 **Escalation Reason**: {escalation_reason}")


def render_confidence_warnings(analysis: Dict[str, Any]) -> None:
    """
    Render dynamic confidence warnings.
    
    Status: ✅ IMPLEMENTED - Basic version with graceful degradation
    Priority: P0 - Critical (AI self-awareness)
    """
    # Use unified schema field "confidence" (0-1 range)
    confidence_raw = analysis.get("confidence")
    if not isinstance(confidence_raw, (int, float)):
        return  # Graceful exit if confidence not available
    
    # Normalize to 0-1 range
    if confidence_raw > 1.0:
        confidence = confidence_raw / 100.0
    else:
        confidence = confidence_raw
    
    # Only show warnings if confidence is below threshold
    if confidence < 0.70:
        st.error("""
        ⚠️ **LOW CONFIDENCE WARNING**
        
        The AI's confidence in this decision is below 70%. Even though the recommendation 
        may suggest autonomous action, please exercise extra caution:
        
        - Review all risk factors carefully
        - Consult with your team before proceeding
        - Document your decision-making process
        - Consider getting a second opinion
        """)
    elif confidence < 0.85:
        st.warning("""
        ⚠️ **Moderate Confidence Alert**
        
        The AI's confidence is between 70-85%. While the recommendation is reasonable, 
        consider:
        
        - Double-checking key assumptions
        - Verifying regulatory requirements
        - Documenting your approach
        """)
    # High confidence (>= 0.85) - no warning needed, already shown in confidence meter


def render_agent_explainability(analysis: Dict[str, Any]) -> None:
    """
    Render agent explainability section.
    
    Status: ✅ IMPLEMENTED - Basic version with expandable section
    Priority: P2 - Nice-to-have
    """
    with st.expander("🤖 How Did the AI Agent Reach This Decision?", expanded=False):
        st.markdown("""
        **Decision Process:**
        
        The AI agent uses a 6-factor risk assessment model to evaluate compliance tasks:
        
        1. **Jurisdiction Complexity** (15%) - Regulatory framework analysis
        2. **Entity Risk Profile** (15%) - Organization history and maturity
        3. **Task Complexity** (20%) - Task category and requirements
        4. **Data Sensitivity** (20%) - Personal data and special categories
        5. **Regulatory Oversight** (20%) - Direct regulation status
        6. **Impact Severity** (10%) - Stakeholder and financial consequences
        
        **Decision Logic:**
        - Risk Score < 0.4 → **AUTONOMOUS** (You can proceed independently)
        - Risk Score 0.4-0.7 → **REVIEW_REQUIRED** (Human approval needed)
        - Risk Score > 0.7 → **ESCALATE** (Expert involvement required)
        
        **Pattern Matching:**
        The agent also considers similar past cases for your organization to provide 
        context-aware recommendations.
        
        **Model Limitations:**
        This is an AI-generated recommendation. Always verify critical compliance 
        requirements with your legal or compliance team, especially for high-risk scenarios.
        """)
        
        # Show reasoning chain if available (unified schema format)
        why = analysis.get('why', {})
        if isinstance(why, dict):
            reasoning = why.get('reasoning_steps', [])
        else:
            reasoning = []
        display_reasoning = []
        for step in reasoning[:5]:
            safe_step = _clean_reasoning_text(step)
            if safe_step:
                display_reasoning.append(safe_step)

        if display_reasoning:
            st.markdown("**Reasoning Steps:**")
            for i, step in enumerate(display_reasoning, 1):
                st.markdown(f"{i}. {step}")
            if len(reasoning) > 5 and len(display_reasoning) < len(reasoning):
                st.caption(f"... and {len(reasoning) - len(display_reasoning)} more steps")


def render_counterfactual_explanations(analysis: Dict[str, Any]) -> None:
    """
    Render counterfactual "what if" scenarios.
    
    Status: ✅ IMPLEMENTED - Basic version with risk factor analysis
    Priority: P2 - Nice-to-have
    """
    risk_analysis = analysis.get("risk_analysis", [])
    if not risk_analysis or not isinstance(risk_analysis, list):
        return  # Graceful exit if no risk factors

    risk_factors = {}
    for item in risk_analysis:
        if isinstance(item, dict):
            factor_name = item.get('factor', '')
            score = item.get('score', 0.0)
            if factor_name:
                risk_factors[factor_name] = score
        elif hasattr(item, 'factor') and hasattr(item, 'score'):
            risk_factors[item.factor] = item.score
    
    if not risk_factors:
        return  # No high-risk factors to show
    
    # Find high risk factors (> 0.60)
    high_risk_factors = {
        k: v for k, v in risk_factors.items() 
        if isinstance(v, (int, float)) and v > 0.60
    }
    
    if not high_risk_factors:
        return  # No high-risk factors to show
    
    with st.expander("🔍 What Would Change This Decision?", expanded=False):
        st.markdown("""
        **High-Risk Factors:**
        
        The following factors significantly contributed to this decision. Changing these 
        could alter the recommendation:
        """)
        
        for factor, score in sorted(high_risk_factors.items(), key=lambda x: x[1], reverse=True):
            factor_display = factor.replace("_", " ").title()
            st.markdown(f"- **{factor_display}**: {score:.1%}")
            
            # Provide suggestions based on factor type
            if "jurisdiction" in factor.lower():
                st.caption("   💡 Consider consulting with jurisdiction-specific compliance experts")
            elif "data" in factor.lower() or "sensitivity" in factor.lower():
                st.caption("   💡 Review data handling procedures and privacy controls")
            elif "regulatory" in factor.lower():
                st.caption("   💡 Ensure compliance with all applicable regulations")
        
        st.info("""
        💡 **Tip**: Use the "What-If Analysis" feature on the Analyze Task page to 
        explore how changing these factors would affect the decision.
        """)


def render_feedback_form(analysis: Dict[str, Any]) -> None:
    """
    Render human feedback form for learning loop.
    
    Status: ✅ IMPLEMENTED - Basic version with API integration
    Priority: P0 - Critical (Learning loop)
    """
    from components.api_client import APIClient
    from components.session_manager import SessionManager
    
    st.markdown("---")
    st.markdown("## 💬 Human Feedback (Optional)")
    st.markdown("Help improve the AI by providing feedback on this decision.")
    
    # Check if feedback already submitted for this analysis
    existing_feedback = SessionManager.get_feedback()
    if existing_feedback and existing_feedback.get("submitted"):
        st.info("✅ **Feedback Submitted**: Thank you! Your feedback has been recorded and will help improve future recommendations.")
        if st.button("🔄 Submit Different Feedback"):
            SessionManager.save_feedback({"submitted": False})
            st.rerun()
        return
    
    with st.form("feedback_form", clear_on_submit=False):
        ai_decision = analysis.get("decision", "UNKNOWN")
        
        st.markdown(f"**AI's Decision:** {ai_decision.replace('_', ' ').title()}")
        
        human_decision = st.selectbox(
            "Your Decision:",
            options=["AUTONOMOUS", "REVIEW_REQUIRED", "ESCALATE"],
            index=0 if ai_decision == "AUTONOMOUS" else 1 if ai_decision == "REVIEW_REQUIRED" else 2,
            help="Select what you think the correct decision should be"
        )
        
        notes = st.text_area(
            "Additional Notes (Optional):",
            placeholder="Any additional context or feedback...",
            height=100
        )
        
        submitted = st.form_submit_button("📤 Submit Feedback", type="primary")
        
        if submitted:
            api = APIClient()
            entity_name = analysis.get("entity_context", {}).get("name", "") if isinstance(analysis.get("entity_context"), dict) else ""
            task_description = analysis.get("task", {}).get("description", "") if isinstance(analysis.get("task"), dict) else ""
            audit_id = analysis.get("audit_id")
            
            feedback_payload = {
                "entity_name": entity_name,
                "task_description": task_description,
                "ai_decision": ai_decision,
                "human_decision": human_decision,
                "notes": notes.strip() if notes else None,
                "audit_trail_id": audit_id
            }
            
            response = api.submit_feedback(feedback_payload)
            
            if response.success:
                st.success("✅ **Thank you!** Your feedback has been submitted and will help improve future recommendations.")
                SessionManager.save_feedback({"submitted": True, "human_decision": human_decision})
                st.rerun()
            else:
                st.error(f"❌ Failed to submit feedback: {response.error}")


def render_export_section(analysis: Dict[str, Any]) -> None:
    """
    Render export options.
    
    Status: ✅ IMPLEMENTED - Uses export_utils module
    Priority: P1 - Important
    """
    from components.export_utils import render_export_section as render_export
    import pandas as pd
    
    st.markdown("---")
    st.markdown("## 📤 Share or Save This Guidance")
    
    entity_name = analysis.get("entity_context", {}).get("name", "") if isinstance(analysis.get("entity_context"), dict) else ""
    task_category = analysis.get("task", {}).get("category", "") if isinstance(analysis.get("task"), dict) else ""
    risk_level = analysis.get("risk_level", "")
    
    # Prepare data for export
    text_report = _format_analysis_as_text(analysis)
    json_data = analysis
    dataframe = _format_analysis_as_dataframe(analysis)
    
    # Use the export_utils render function
    render_export(
        data=analysis,
        dataframe=dataframe,
        text_report=text_report,
        json_data=json_data,
        prefix="guidance",
        entity_name=entity_name,
        task_category=task_category,
        risk_level=risk_level,
        show_email=False,  # Email not implemented yet
        email_api_endpoint=None
    )
    
    st.caption("💡 Note: Email export is not yet available. Please use download options above.")


def _format_analysis_as_text(analysis: Dict[str, Any]) -> str:
    """Format analysis as text report"""
    lines = []
    lines.append("=" * 70)
    lines.append("COMPLIANCE ANALYSIS REPORT")
    lines.append("=" * 70)
    lines.append("")
    
    decision = analysis.get("decision", "UNKNOWN")
    confidence = analysis.get("confidence", 0)
    risk_level = analysis.get("risk_level", "UNKNOWN")
    
    lines.append(f"Decision: {decision.replace('_', ' ').title()}")
    lines.append(f"Confidence: {confidence:.1%}" if isinstance(confidence, (int, float)) else f"Confidence: {confidence}")
    lines.append(f"Risk Level: {risk_level}")
    lines.append("")
    
    why = analysis.get("why", {})
    if isinstance(why, dict):
        reasoning = why.get("reasoning_steps", [])
    else:
        reasoning = []
    if reasoning:
        lines.append("Reasoning:")
        for i, step in enumerate(reasoning, 1):
            lines.append(f"  {i}. {step}")
        lines.append("")
    
    recommendations = analysis.get("recommendations", [])
    if recommendations:
        lines.append("Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            if isinstance(rec, dict):
                lines.append(f"  {i}. {rec.get('title', 'N/A')}: {rec.get('description', '')}")
            else:
                lines.append(f"  {i}. {rec}")
        lines.append("")
    
    lines.append("=" * 70)
    return "\n".join(lines)


def _format_analysis_as_dataframe(analysis: Dict[str, Any]) -> "pd.DataFrame":
    """Format analysis as DataFrame for Excel export"""
    import pandas as pd
    
    data = {
        "Field": [],
        "Value": []
    }
    
    data["Field"].append("Decision")
    data["Value"].append(analysis.get("decision", "UNKNOWN"))
    
    confidence = analysis.get("confidence", 0)
    data["Field"].append("Confidence")
    data["Value"].append(f"{confidence:.1%}" if isinstance(confidence, (int, float)) else str(confidence))
    
    data["Field"].append("Risk Level")
    data["Value"].append(analysis.get("risk_level", "UNKNOWN"))
    
    risk_analysis = analysis.get("risk_analysis", [])
    risk_factors = {}
    if isinstance(risk_analysis, list):
        for item in risk_analysis:
            if isinstance(item, dict):
                factor_name = item.get('factor', '')
                score = item.get('score', 0.0)
                if factor_name:
                    risk_factors[factor_name] = score
            elif hasattr(item, 'factor') and hasattr(item, 'score'):
                risk_factors[item.factor] = item.score
    
    if risk_factors and isinstance(risk_factors, dict):
        for factor, value in risk_factors.items():
            if isinstance(value, (int, float)):
                data["Field"].append(factor.replace("_", " ").title())
                data["Value"].append(f"{value:.1%}")
    
    return pd.DataFrame(data)


def render_chat_integration(analysis: Dict[str, Any]) -> None:
    """
    Render chat assistant integration.
    
    Status: ✅ IMPLEMENTED - Context preparation note
    Priority: P2 - Nice-to-have
    
    Note: Chat assistant is available in the sidebar. Context from this analysis
    is automatically available for questions.
    """
    # Chat integration is handled by sidebar component
    # This function exists for architecture completeness but doesn't need to render anything
    # The sidebar chat component can access analysis results from session state
    pass  # Sidebar feature - no UI needed here


# =============================================================================
# NOTE: Utility functions have been moved to their respective component modules
# - Confidence utilities → confidence_display.py
# - Risk utilities → risk_display.py
# - Similar cases utilities → similar_cases_display.py
# - Suggestions utilities → suggestions_display.py
# =============================================================================


# =============================================================================
# NOTES FOR FUTURE DEVELOPMENT
# =============================================================================
"""
ARCHITECTURE PRINCIPLES:
1. This file is the single source of truth for results rendering
2. Each sub-component is independently testable
3. Missing components fail gracefully with TODO notices
4. No business logic - only display orchestration
5. Components can be implemented in any order

IMPLEMENTATION STATUS:

✅ COMPLETED:
- render_confidence_meter() - Imported from confidence_display.py
- render_risk_breakdown() - Imported from risk_display.py
- render_similar_cases() - Imported from similar_cases_display.py
- render_proactive_suggestions() - Imported from suggestions_display.py
- render_pattern_analysis() - Implemented inline
- render_escalation_reason() - Implemented inline

All core renderers are implemented. Future enhancements (export, richer explainability, chat context) can be added as new helper functions without changing existing call sites. Update this note when new components are shipped.
"""
