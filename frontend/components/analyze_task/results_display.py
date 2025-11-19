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
  proactive_suggestions, pattern_analysis, escalation_reason
- ⚠️ Partial: decision_banner, risk_level_display, reasoning_chain, recommendations
- ❌ TODO: action_plan, stakeholders, confidence_warnings, feedback_form,
  export_section, agent_explainability, counterfactuals, chat_integration
"""

import streamlit as st
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.agent.risk_models import DecisionAnalysis

# Import sub-components
from .confidence_display import render_confidence_meter
from .risk_display import render_risk_breakdown
from .similar_cases_display import render_similar_cases
from .suggestions_display import render_proactive_suggestions


def render_results(analysis: dict) -> None:
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
    
    # Render results header with clearer structure
    st.markdown("---")
    st.markdown("## 🎯 Your Results")
    
    # Add a clear summary section FIRST
    st.markdown("""
    <div style='background-color: #f0f9ff; padding: 1rem; border-radius: 10px; margin-bottom: 2rem; border-left: 4px solid #3b82f6;'>
        <p style='font-size: 1.1rem; color: #1e40af; margin: 0;'>
            <strong>📋 Summary:</strong> Below is your compliance analysis with decision, confidence level, risk assessment, and actionable recommendations.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick summary metrics at the top
    col1, col2, col3 = st.columns(3)
    with col1:
        decision = analysis.get("decision", "UNKNOWN")
        decision_display = decision.replace("_", " ").title() if isinstance(decision, str) else str(decision)
        st.metric("Decision", decision_display, help="The AI's recommended action")
    with col2:
        # Extract confidence - try confidence_score first (0-1), then confidence
        confidence_raw = analysis.get("confidence_score") or analysis.get("confidence", 0)
        if isinstance(confidence_raw, (int, float)):
            # Normalize to 0-100% for display
            if confidence_raw <= 1.0:
                confidence_percent = confidence_raw * 100
            else:
                confidence_percent = confidence_raw
            st.metric("Confidence", f"{confidence_percent:.0f}%", help="How certain the AI is about this decision (0-100%)")
        else:
            st.metric("Confidence", "N/A", help="How certain the AI is about this decision")
    with col3:
        risk = analysis.get("risk_level", "UNKNOWN")
        risk_display = risk.replace("_", " ").title() if isinstance(risk, str) else str(risk)
        st.metric("Risk Level", risk_display, help="Overall risk assessment")
    
    st.markdown("---")
    
    # =========================================================================
    # CORE DECISION OUTPUT
    # =========================================================================
    # P0 - Critical: User's primary answer
    render_decision_banner(analysis)
    
    # P0 - Critical: Confidence in the decision
    render_confidence_meter(analysis)
    
    # P0 - Critical: Risk level assessment
    render_risk_level_display(analysis)
    
    # =========================================================================
    # AGENTIC AI FEATURES (Entity Memory & Proactive Intelligence)
    # =========================================================================
    # P0 - Critical: Proactive AI insights shown BEFORE main results
    # Note: Should appear early to catch user's attention
    render_proactive_suggestions(analysis)
    
    # P0 - Critical: Entity memory - similar past cases
    # Core agentic feature showing organizational learning
    render_similar_cases(analysis)
    
    # P1 - Important: Pattern analysis across historical data
    render_pattern_analysis(analysis)
    
    # =========================================================================
    # DETAILED ANALYSIS
    # =========================================================================
    # P1 - Important: Breakdown of all 6 risk factors
    render_risk_breakdown(analysis)
    
    # P0 - Partial: Step-by-step reasoning from AI
    render_reasoning_chain(analysis)
    
    # P0 - Partial: Action recommendations with sources
    render_recommendations(analysis)
    
    # P1 - Important: Action plan specific to decision type
    render_action_plan(analysis)
    
    # P1 - Important: Stakeholder involvement guidance
    render_stakeholders(analysis)
    
    # P1 - Important: Why escalation is needed (if applicable)
    render_escalation_reason(analysis)
    
    # =========================================================================
    # AI TRANSPARENCY & SELF-AWARENESS
    # =========================================================================
    # P0 - Missing: Dynamic warnings based on confidence level
    render_confidence_warnings(analysis)
    
    # P2 - Nice-to-have: How AI reached this decision
    render_agent_explainability(analysis)
    
    # P2 - Nice-to-have: What would change this decision
    render_counterfactual_explanations(analysis)
    
    # =========================================================================
    # USER INTERACTION
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


def render_decision_banner(analysis: dict) -> None:
    """
    Render the main decision outcome banner.
    
    Status: ⚠️ PARTIAL - Simplified in new UI
    Priority: P0 - Critical
    
    TODO: Restore features from old UI:
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


def render_risk_level_display(analysis: dict) -> None:
    """
    Render risk level assessment.
    
    Status: ⚠️ PARTIAL - Basic display
    Priority: P0 - Critical
    
    TODO: Enhance with:
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


def render_pattern_analysis(analysis: dict) -> None:
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


def render_reasoning_chain(analysis: dict) -> None:
    """
    Render AI reasoning chain.
    
    Status: ⚠️ PARTIAL - Simple list in new UI
    Priority: P0 - Critical
    
    TODO: Restore features from old UI:
    - Parse reasoning into structured sections (Risk Analysis, Decision Logic)
    - Visual formatting with headers
    - Overall risk score display
    - Expandable full details section
    - Debug viewer for reasoning structure
    """
    reasoning = analysis.get('reasoning_chain', [])
    if reasoning:
        with st.expander("💭 Why This Decision?", expanded=True):
            for i, step in enumerate(reasoning, 1):
                st.markdown(f"{i}. {step}")


def render_recommendations(analysis: dict) -> None:
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
                <div style='background-color: #f8fafc; padding: 1rem; border-radius: 8px; margin: 0.75rem 0; border-left: 4px solid #3b82f6;'>
                    <strong>{priority_emoji} {i}. {title}</strong><br>
                    <span style='color: #475569;'>{description}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Handle string recommendation
                st.markdown(f"""
                <div style='background-color: #f8fafc; padding: 1rem; border-radius: 8px; margin: 0.75rem 0; border-left: 4px solid #3b82f6;'>
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
    jurisdictions: list,
    industry: str
) -> list:
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


def render_action_plan(analysis: dict) -> None:
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


def render_stakeholders(analysis: dict) -> None:
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
        <div style='background-color: #f0f9ff; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #3b82f6;'>
            <strong>👤 {stakeholder['role']}</strong><br>
            <small><strong>Why:</strong> {stakeholder['reason']}</small><br>
            <small><strong>When:</strong> {stakeholder['when']}</small>
        </div>
        """, unsafe_allow_html=True)


def render_escalation_reason(analysis: dict) -> None:
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


def render_confidence_warnings(analysis: dict) -> None:
    """
    Render dynamic confidence warnings.
    
    Status: ❌ MISSING - Not implemented in new UI
    Priority: P0 - Critical (AI self-awareness)
    
    TODO: Implement confidence warnings:
    - < 0.70: Error box with "LOW CONFIDENCE WARNING"
    - < 0.85: Warning box with "Moderate Confidence Alert"
    - >= 0.85: Success box with "High Confidence"
    - Specific guidance for each level
    - Required actions even if decision says autonomous
    """
    return


def render_agent_explainability(analysis: dict) -> None:
    """
    Render agent explainability section.
    
    Status: ❌ MISSING - Not implemented in new UI
    Priority: P2 - Nice-to-have
    
    TODO: Implement explainability:
    - "How did the AI Agent reach this decision?" expander
    - Decision process explanation
    - Pattern matching description
    - Decision logic framework
    - Agentic behavior highlights
    - Model limitations disclosure
    """
    # TODO: Implement when component is created
    pass  # Low priority - not displayed by default


def render_counterfactual_explanations(analysis: dict) -> None:
    """
    Render counterfactual "what if" scenarios.
    
    Status: ❌ MISSING - Not implemented in new UI
    Priority: P2 - Nice-to-have
    
    TODO: Implement counterfactuals:
    - "What Would Change This Decision?" section
    - High risk factors (> 0.60) with suggestions
    - Jurisdiction, data sensitivity, regulatory factors
    - Expandable section
    """
    # TODO: Implement when component is created
    pass  # Low priority


def render_feedback_form(analysis: dict) -> None:
    """
    Render human feedback form for learning loop.
    
    Status: ❌ MISSING - Not implemented in new UI
    Priority: P0 - Critical (Learning loop)
    
    TODO: Implement feedback form:
    - "Human Feedback (Optional)" section
    - Decision selection dropdown
    - Agreement/override indicators
    - Notes text area
    - Submission confirmation
    - Feedback history display
    - State management to prevent duplicates
    - API integration
    """
    return


def render_export_section(analysis: dict) -> None:
    """
    Render export options.
    
    Status: ❌ MISSING - Not implemented in new UI
    Priority: P1 - Important
    
    TODO: Implement export section:
    - "Share or Save This Guidance" section
    - Export to TXT (formatted report)
    - Export to Excel (DataFrame)
    - Export to JSON (structured data)
    - Email export option
    - Auto-generated filenames
    - Export history tracking
    """
    return


def render_chat_integration(analysis: dict) -> None:
    """
    Render chat assistant integration.
    
    Status: ❌ MISSING - Not implemented in new UI
    Priority: P2 - Nice-to-have
    
    TODO: Implement chat integration:
    - Prepare context from analysis
    - Pass to sidebar chat component
    - Allow questions about decision
    """
    # TODO: Implement when component is created
    pass  # Sidebar feature


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

⚠️ PARTIAL (Basic implementation, needs enhancement):
- render_decision_banner() - Simplified version
- render_risk_level_display() - Basic version
- render_reasoning_chain() - Simple list
- render_recommendations() - Simple list

❌ REMAINING TODO:
Phase 1 (P0 - Critical):
- render_confidence_warnings() - Dynamic warnings based on confidence
- render_feedback_form() - Learning loop component

Phase 2 (P1 - Important):
- render_action_plan() - Step-by-step action plan
- render_stakeholders() - Who to talk to section
- render_export_section() - Export to TXT/Excel/JSON

Phase 3 (P2 - Nice-to-have):
- render_agent_explainability() - How AI decided
- render_counterfactual_explanations() - What would change decision
- render_chat_integration() - Sidebar chat context

REFACTORING SAFETY:
- DO NOT remove function calls from render_results()
- Always check FEATURE_INVENTORY.md before modifying
- Add new features as new functions, don't modify existing
- Keep TODO comments until fully implemented
"""

