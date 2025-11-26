"""
Risk Factor Breakdown Component
================================
Visual display of detailed risk factor analysis.

Status: ✅ IMPLEMENTED
Priority: P1 - Important
"""

import streamlit as st
from typing import Optional, Union


def render_risk_breakdown(analysis: dict) -> None:
    """
    Render detailed breakdown of all risk factors.
    
    Features:
    - 2-column layout for visual organization
    - Color-coded risk levels with emojis
    - Supports both numeric (0-1) and text-based risk levels
    - Progress bars for numeric values
    - Graceful handling of missing or empty data
    
    Args:
        analysis: Dictionary containing analysis results
                  Expected keys: risk_factors (dict)
    
    Graceful degradation:
        - Missing risk_factors: shows nothing
        - Empty risk_factors: shows nothing
        - Unknown risk levels: defaults to neutral display
    """
    
    # =========================================================================
    # EXTRACT RISK FACTORS
    # =========================================================================
    # Unified schema uses "risk_analysis" (list of RiskAnalysisItem)
    # Legacy format uses "risk_factors" (dict)
    risk_analysis = analysis.get('risk_analysis', [])
    risk_factors = analysis.get('risk_factors', {})
    
    # Convert unified schema format to legacy format for compatibility
    if risk_analysis and isinstance(risk_analysis, list) and len(risk_analysis) > 0:
        # Convert risk_analysis list to risk_factors dict
        risk_factors = {}
        for item in risk_analysis:
            if isinstance(item, dict):
                factor_name = item.get('factor', '')
                score = item.get('score', 0.0)
                if factor_name:
                    risk_factors[factor_name] = score
            elif hasattr(item, 'factor') and hasattr(item, 'score'):
                # Pydantic model
                risk_factors[item.factor] = item.score
    
    # Graceful exit if no risk factors
    if not risk_factors:
        return
    
    # Check if dict is empty
    if not isinstance(risk_factors, dict) or len(risk_factors) == 0:
        return
    
    # =========================================================================
    # RENDER RISK BREAKDOWN SECTION
    # =========================================================================
    st.markdown("---")
    st.markdown("### 📊 Risk Factor Breakdown")
    st.caption("Detailed analysis of compliance risk dimensions")
    
    # Convert risk factors to display format
    display_factors = _prepare_risk_factors_for_display(risk_factors)
    
    if not display_factors:
        return
    
    # Create 2-column layout
    col1, col2 = st.columns(2)
    
    # Distribute factors across columns
    factors_list = list(display_factors.items())
    mid_point = (len(factors_list) + 1) // 2
    
    with col1:
        for factor_name, factor_data in factors_list[:mid_point]:
            _render_risk_factor_card(factor_name, factor_data)
    
    with col2:
        for factor_name, factor_data in factors_list[mid_point:]:
            _render_risk_factor_card(factor_name, factor_data)
    
    # Overall risk score if available
    _render_overall_risk_score(analysis)
    
    # Expandable detailed view
    with st.expander("🔍 Understanding Risk Factors", expanded=False):
        st.markdown("""
        **Risk factors assess different dimensions of compliance risk:**
        
        - **Jurisdiction Risk**: Complexity from operating in multiple jurisdictions with varying regulations
        - **Entity Risk**: Risk based on organization type, size, and regulatory status
        - **Task Risk**: Risk from the specific task's complexity and requirements
        - **Data Sensitivity Risk**: Risk from handling personal, financial, or sensitive data
        - **Regulatory Risk**: Risk from specific regulatory requirements and obligations
        - **Impact Risk**: Potential impact if something goes wrong
        
        **Risk Levels:**
        - 🔴 **CRITICAL** (>80%): Immediate expert review required
        - 🟠 **HIGH** (60-80%): Escalation strongly recommended
        - 🟡 **MEDIUM** (40-60%): Review by supervisor recommended
        - 🟢 **LOW** (<40%): Routine handling appropriate
        """)


def _prepare_risk_factors_for_display(risk_factors: dict) -> dict:
    """
    Convert raw risk factors to display-ready format.
    
    Handles:
    - Numeric values (0-1) → convert to risk level
    - Text values (CRITICAL, HIGH, etc.) → use as-is
    - Unknown formats → neutral display
    
    Args:
        risk_factors: Raw risk factors dict
    
    Returns:
        Dict with factor names and display data
    """
    display_factors = {}
    
    # Map of technical names to display names
    name_map = {
        'jurisdiction_risk': 'Jurisdiction Complexity',
        'entity_risk': 'Entity Profile',
        'task_risk': 'Task Complexity',
        'data_sensitivity_risk': 'Data Sensitivity',
        'regulatory_risk': 'Regulatory Exposure',
        'impact_risk': 'Potential Impact',
        'jurisdiction': 'Jurisdiction',
        'timeline': 'Timeline',
        'complexity': 'Complexity',
        'data_sensitivity': 'Data Sensitivity',
        'regulatory_exposure': 'Regulatory Exposure',
        'impact': 'Impact'
    }
    
    for key, value in risk_factors.items():
        # Get display name
        display_name = name_map.get(key, _format_key_name(key))
        
        # Determine if numeric or text
        if isinstance(value, (int, float)):
            # Numeric value (0-1 or 0-100)
            normalized_value = _normalize_risk_value(value)
            risk_level, emoji, color = _get_risk_level_from_value(normalized_value)
            display_factors[display_name] = {
                'level': risk_level,
                'emoji': emoji,
                'color': color,
                'value': normalized_value,
                'is_numeric': True
            }
        elif isinstance(value, str):
            # Text value (CRITICAL, HIGH, MEDIUM, LOW)
            emoji, color = _get_risk_emoji_and_color(value.upper())
            display_factors[display_name] = {
                'level': value.upper(),
                'emoji': emoji,
                'color': color,
                'value': None,
                'is_numeric': False
            }
        else:
            # Unknown format - skip
            continue
    
    return display_factors


def _render_risk_factor_card(factor_name: str, factor_data: dict) -> None:
    """
    Render a single risk factor card.
    
    Args:
        factor_name: Display name of the factor
        factor_data: Dict with level, emoji, color, value, is_numeric
    """
    emoji = factor_data['emoji']
    level = factor_data['level']
    value = factor_data['value']
    is_numeric = factor_data['is_numeric']
    
    # Display header
    st.markdown(f"**{factor_name}**")
    
    # Display risk level with emoji
    st.markdown(f"{emoji} **{level}**")
    
    # If numeric, show progress bar
    if is_numeric and value is not None:
        _render_risk_progress_bar(value, level)
    
    # Add spacing
    st.markdown("")


def _render_risk_progress_bar(value: float, level: str) -> None:
    """
    Render a progress bar for numeric risk values.
    
    Args:
        value: Normalized risk value (0-1)
        level: Risk level string
    """
    # Determine color based on level
    if level == 'CRITICAL':
        progress_text = "🔴"
    elif level == 'HIGH':
        progress_text = "🟠"
    elif level == 'MEDIUM':
        progress_text = "🟡"
    else:  # LOW
        progress_text = "🟢"
    
    # Show percentage
    st.caption(f"{value * 100:.0f}%")


def _render_overall_risk_score(analysis: dict) -> None:
    """
    Render overall risk score if available.
    
    Args:
        analysis: Full analysis dict
    """
    risk_score = analysis.get('risk_score')
    
    if risk_score is not None:
        risk_score_normalized = _normalize_risk_value(risk_score)
        risk_level, emoji, color = _get_risk_level_from_value(risk_score_normalized)
        
        st.markdown("---")
        st.markdown(f"### {emoji} **Overall Risk Score: {risk_level}** ({risk_score_normalized * 100:.0f}%)")
        st.progress(risk_score_normalized)


def _normalize_risk_value(value: Union[int, float]) -> float:
    """
    Normalize risk value to 0-1 range.
    
    Handles:
    - 0-1 format: use as-is
    - 0-100 format: divide by 100
    
    Args:
        value: Raw risk value
    
    Returns:
        Normalized value (0-1)
    """
    if value > 1.0:
        # Assume 0-100 format
        normalized = value / 100.0
    else:
        # Already 0-1 format
        normalized = value
    
    # Clamp to valid range
    return max(0.0, min(1.0, normalized))


def _get_risk_level_from_value(value: float) -> tuple[str, str, str]:
    """
    Convert numeric risk value to risk level.
    
    Thresholds:
    - >= 0.80: CRITICAL
    - >= 0.60: HIGH
    - >= 0.40: MEDIUM
    - < 0.40: LOW
    
    Args:
        value: Normalized risk value (0-1)
    
    Returns:
        Tuple of (level, emoji, color)
    """
    if value >= 0.80:
        return "CRITICAL", "🔴", "#dc2626"
    elif value >= 0.60:
        return "HIGH", "🟠", "#ea580c"
    elif value >= 0.40:
        return "MEDIUM", "🟡", "#ca8a04"
    else:
        return "LOW", "🟢", "#16a34a"


def _get_risk_emoji_and_color(risk_level: str) -> tuple[str, str]:
    """
    Get emoji and color for text-based risk level.
    
    Args:
        risk_level: Risk level string (CRITICAL, HIGH, MEDIUM, LOW)
    
    Returns:
        Tuple of (emoji, color)
    """
    risk_map = {
        'CRITICAL': ("🔴", "#dc2626"),
        'HIGH': ("🟠", "#ea580c"),
        'MEDIUM': ("🟡", "#ca8a04"),
        'LOW': ("🟢", "#16a34a"),
        'SEVERE': ("🔴", "#dc2626"),
        'MODERATE': ("🟡", "#ca8a04"),
        'MINIMAL': ("🟢", "#16a34a")
    }
    
    return risk_map.get(risk_level, ("⚪", "#6b7280"))  # Default: neutral


def _format_key_name(key: str) -> str:
    """
    Format technical key name to display name.
    
    Examples:
    - 'jurisdiction_risk' → 'Jurisdiction Risk'
    - 'data_sensitivity' → 'Data Sensitivity'
    
    Args:
        key: Technical key name
    
    Returns:
        Formatted display name
    """
    # Remove '_risk' suffix if present
    if key.endswith('_risk'):
        key = key[:-5]
    
    # Replace underscores with spaces and title case
    return key.replace('_', ' ').title()


# =============================================================================
# ALTERNATIVE COMPACT RENDERING
# =============================================================================

def render_risk_summary(analysis: dict) -> None:
    """
    Render compact risk summary (single line with key factors).
    
    Use this for dashboard views or summary cards.
    
    Args:
        analysis: Analysis dictionary
    """
    risk_factors = analysis.get('risk_factors')
    
    if not risk_factors:
        return
    
    display_factors = _prepare_risk_factors_for_display(risk_factors)
    
    if not display_factors:
        return
    
    # Show top 3 highest risk factors
    sorted_factors = sorted(
        display_factors.items(),
        key=lambda x: x[1]['value'] if x[1]['value'] is not None else 0,
        reverse=True
    )[:3]
    
    risk_text = " | ".join([
        f"{data['emoji']} {name}: {data['level']}"
        for name, data in sorted_factors
    ])
    
    st.caption(f"**Key Risk Factors**: {risk_text}")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_highest_risk_factor(risk_factors: dict) -> Optional[tuple[str, str, float]]:
    """
    Get the highest risk factor.
    
    Args:
        risk_factors: Risk factors dict
    
    Returns:
        Tuple of (factor_name, risk_level, value) or None
    """
    if not risk_factors:
        return None
    
    display_factors = _prepare_risk_factors_for_display(risk_factors)
    
    if not display_factors:
        return None
    
    # Find highest risk
    highest = max(
        display_factors.items(),
        key=lambda x: x[1]['value'] if x[1]['value'] is not None else 0
    )
    
    return (highest[0], highest[1]['level'], highest[1]['value'])

