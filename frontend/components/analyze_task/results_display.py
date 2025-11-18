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
    
    # Render results header
    st.markdown("---")
    st.markdown("## 🎯 Your Results")
    
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
    Render action recommendations.
    
    Status: ⚠️ PARTIAL - Simple list in new UI
    Priority: P0 - Critical
    
    TODO: Restore features from old UI:
    - Numbered recommendations with full details
    - Expandable source citations for each recommendation
    - Regulatory basis (GDPR, CCPA, etc.)
    - Supporting evidence (confidence, risk factors, similar cases)
    - Related analysis points
    - Visual confidence meter per recommendation
    """
    recommendations = analysis.get('recommendations', [])
    if recommendations:
        with st.expander("💡 What To Do Next", expanded=True):
            for i, rec in enumerate(recommendations, 1):
                st.markdown(f"**{i}.** {rec}")


def render_action_plan(analysis: dict) -> None:
    """
    Render step-by-step action plan.
    
    Status: ❌ MISSING - Not implemented in new UI
    Priority: P1 - Important
    
    TODO: Implement action plan:
    - "Your Action Plan" section
    - Numbered steps specific to decision type
    - Derived from decision outcome
    - Clear, actionable guidance
    """
    return


def render_stakeholders(analysis: dict) -> None:
    """
    Render stakeholder involvement guidance.
    
    Status: ❌ MISSING - Not implemented in new UI
    Priority: P1 - Important
    
    TODO: Implement stakeholders section:
    - "Who To Talk To" section
    - Role-specific guidance
    - Derived from decision outcome
    - Info box styling
    """
    return


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

