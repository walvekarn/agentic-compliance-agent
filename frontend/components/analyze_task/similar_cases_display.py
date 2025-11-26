"""
Similar Cases Display Component
================================
Entity memory display showing similar past decisions.

Status: ✅ IMPLEMENTED
Priority: P0 - Critical (Core agentic feature)
"""

import streamlit as st
from datetime import datetime, timezone
from typing import Optional, Union


def render_similar_cases(analysis: dict) -> None:
    """
    Render similar past cases from entity memory.
    
    This is a core agentic AI feature that demonstrates organizational learning
    by showing how the system has handled similar situations in the past.
    
    Features:
    - Expandable section with case cards
    - Color-coded by decision type
    - Time ago calculation
    - Decision outcome indicators
    - Risk level and confidence display
    - Task description preview
    - Graceful handling of missing/malformed data
    
    Args:
        analysis: Dictionary containing analysis results
                  Expected keys: similar_cases (List[dict])
    
    Graceful degradation:
        - Missing similar_cases: shows nothing
        - Empty similar_cases: shows nothing
        - Malformed dates: displays without time ago
        - Missing fields: displays available information only
    """
    
    # =========================================================================
    # EXTRACT SIMILAR CASES
    # =========================================================================
    similar_cases = analysis.get('similar_cases')
    
    # Graceful exit if no similar cases
    if not similar_cases:
        return
    
    # Check if list is empty
    if not isinstance(similar_cases, list) or len(similar_cases) == 0:
        return
    
    # =========================================================================
    # RENDER SIMILAR CASES SECTION
    # =========================================================================
    st.markdown("---")
    st.markdown("## 🧠 Agent Memory: Similar Past Cases")
    st.markdown("""
    <p style='font-size: 1.1rem; color: #64748b; margin-bottom: 1.5rem;'>
    I remember analyzing similar tasks for your organization. Here's what I learned:
    </p>
    """, unsafe_allow_html=True)
    
    # Pattern analysis summary (if available)
    pattern_analysis = analysis.get('pattern_analysis')
    if pattern_analysis:
        st.info(f"📊 **Pattern Analysis**: {pattern_analysis}")
    
    # Display cases in expandable section
    with st.expander(
        f"📁 View {len(similar_cases)} Similar Past {'Case' if len(similar_cases) == 1 else 'Cases'}",
        expanded=True
    ):
        for i, case in enumerate(similar_cases, 1):
            _render_case_card(case, i)
        
        # Helper note
        st.caption("💡 **Note**: All similar cases are shown above. Your form data is preserved - you can scroll up to review or modify your inputs anytime.")


def _render_case_card(case: dict, case_number: int) -> None:
    """
    Render a single case card with color coding.
    
    Args:
        case: Case dictionary with decision details
        case_number: Sequential case number for display
    """
    
    # Extract case details
    decision = case.get('decision', 'UNKNOWN')
    risk_level = case.get('risk_level', 'UNKNOWN')
    confidence = case.get('confidence') or case.get('confidence_score')
    task_description = case.get('task_description', '')
    timestamp = case.get('timestamp', case.get('created_at'))
    entity_name = case.get('entity_name', '')
    task_category = case.get('task_category', '')
    
    # Calculate time ago
    time_ago = _calculate_time_ago(timestamp)
    
    # Get decision styling
    decision_emoji = _get_decision_emoji(decision)
    decision_color = _get_decision_color(decision)
    
    # Render card with color-coded background
    st.markdown(f"""
    <div style="background: {decision_color}; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
        <strong>Case #{case_number}</strong> {f"({time_ago})" if time_ago else ""}
        <br/>
        <strong>{decision_emoji} Decision:</strong> {decision}
        <br/>
        <strong>Risk Level:</strong> {risk_level}
        {f"<br/><strong>Category:</strong> {task_category}" if task_category else ""}
        {f"<br/><strong>Organization:</strong> {entity_name}" if entity_name else ""}
        {f"<br/><strong>Task:</strong> {task_description[:100]}..." if task_description else ""}
    </div>
    """, unsafe_allow_html=True)
    
    # Display confidence if available
    if confidence is not None:
        try:
            confidence_normalized = _normalize_confidence(confidence)
            emoji, label = _get_confidence_display(confidence_normalized)
            st.caption(f"   {emoji} **Confidence:** {label} ({confidence_normalized*100:.0f}%)")
        except (ValueError, TypeError):
            pass  # Skip confidence display if malformed


def _calculate_time_ago(timestamp: Optional[Union[str, datetime]]) -> Optional[str]:
    """
    Calculate human-readable time ago from timestamp.
    
    Handles:
    - ISO format strings
    - datetime objects (timezone-aware or naive)
    - Invalid formats (returns None)
    
    Args:
        timestamp: Timestamp as string or datetime
    
    Returns:
        Human-readable time ago string or None
    """
    if not timestamp:
        return None
    
    try:
        # Parse timestamp if string
        if isinstance(timestamp, str):
            # Remove 'Z' and replace with '+00:00' for proper parsing
            timestamp_str = timestamp.replace('Z', '+00:00')
            case_date = datetime.fromisoformat(timestamp_str)
        elif isinstance(timestamp, datetime):
            case_date = timestamp
        else:
            return None
        
        # Get current time in UTC
        now_utc = datetime.now(timezone.utc)
        
        # Ensure case_date is timezone-aware
        if case_date.tzinfo is None:
            case_date = case_date.replace(tzinfo=timezone.utc)
        
        # Calculate delta
        delta = now_utc - case_date
        
        # Format time ago
        if delta.days == 0:
            hours = delta.seconds // 3600
            if hours == 0:
                minutes = delta.seconds // 60
                if minutes == 0:
                    return "just now"
                elif minutes == 1:
                    return "1 minute ago"
                else:
                    return f"{minutes} minutes ago"
            elif hours == 1:
                return "1 hour ago"
            else:
                return f"{hours} hours ago"
        elif delta.days == 1:
            return "yesterday"
        elif delta.days < 7:
            return f"{delta.days} days ago"
        elif delta.days < 30:
            weeks = delta.days // 7
            return f"{weeks} week ago" if weeks == 1 else f"{weeks} weeks ago"
        elif delta.days < 365:
            months = delta.days // 30
            return f"{months} month ago" if months == 1 else f"{months} months ago"
        else:
            years = delta.days // 365
            return f"{years} year ago" if years == 1 else f"{years} years ago"
    
    except (ValueError, AttributeError, TypeError):
        # Silently fail on bad timestamps
        return None


def _get_decision_emoji(decision: str) -> str:
    """
    Get emoji for decision type.
    
    Args:
        decision: Decision string (AUTONOMOUS, REVIEW_REQUIRED, ESCALATE)
    
    Returns:
        Emoji string
    """
    emoji_map = {
        "AUTONOMOUS": "✅",
        "REVIEW_REQUIRED": "⚠️",
        "ESCALATE": "🚨",
        "UNKNOWN": "📋"
    }
    return emoji_map.get(decision, "📋")


def _get_decision_color(decision: str) -> str:
    """
    Get background color for decision card.
    
    Args:
        decision: Decision string
    
    Returns:
        Hex color code
    """
    color_map = {
        "AUTONOMOUS": "#d1fae5",      # Light green
        "REVIEW_REQUIRED": "#fef3c7",  # Light yellow
        "ESCALATE": "#fee2e2",         # Light red
        "UNKNOWN": "#f3f4f6"           # Light gray
    }
    return color_map.get(decision, "#f3f4f6")


def _normalize_confidence(confidence: Union[int, float, str]) -> float:
    """
    Normalize confidence to 0-1 range.
    
    Args:
        confidence: Confidence value (0-1, 0-100, or string)
    
    Returns:
        Normalized confidence (0-1)
    """
    if isinstance(confidence, str):
        confidence = float(confidence)
    
    confidence = float(confidence)
    
    # Handle 0-100 format
    if confidence > 1.0:
        confidence = confidence / 100.0
    
    # Clamp to valid range
    return max(0.0, min(1.0, confidence))


def _get_confidence_display(confidence: float) -> tuple[str, str]:
    """
    Get emoji and label for confidence level.
    
    Args:
        confidence: Normalized confidence (0-1)
    
    Returns:
        Tuple of (emoji, label)
    """
    if confidence >= 0.75:
        return "🟢", "High Confidence"
    elif confidence >= 0.40:
        return "🟡", "Medium Confidence"
    else:
        return "🔴", "Low Confidence"


# =============================================================================
# ALTERNATIVE COMPACT RENDERING
# =============================================================================

def render_similar_cases_summary(analysis: dict) -> None:
    """
    Render compact summary of similar cases (count and pattern).
    
    Use this for dashboard views or quick reference.
    
    Args:
        analysis: Analysis dictionary
    """
    similar_cases = analysis.get('similar_cases', [])
    
    if not similar_cases or len(similar_cases) == 0:
        return
    
    pattern_analysis = analysis.get('pattern_analysis', '')
    
    st.info(
        f"🧠 **{len(similar_cases)} similar past case{'s' if len(similar_cases) != 1 else ''}** "
        f"{f'- {pattern_analysis}' if pattern_analysis else 'found in organization history'}"
    )


def render_similar_cases_inline(analysis: dict, max_cases: int = 3) -> None:
    """
    Render inline similar cases list (no expander).
    
    Args:
        analysis: Analysis dictionary
        max_cases: Maximum number of cases to display
    """
    similar_cases = analysis.get('similar_cases', [])
    
    if not similar_cases or len(similar_cases) == 0:
        return
    
    st.markdown("#### 🧠 Similar Past Cases")
    
    for i, case in enumerate(similar_cases[:max_cases], 1):
        decision = case.get('decision', 'UNKNOWN')
        risk_level = case.get('risk_level', 'UNKNOWN')
        timestamp = case.get('timestamp')
        time_ago = _calculate_time_ago(timestamp)
        
        decision_emoji = _get_decision_emoji(decision)
        
        st.markdown(
            f"**{i}.** {decision_emoji} {decision} "
            f"(Risk: {risk_level}) "
            f"{f'- {time_ago}' if time_ago else ''}"
        )
    
    if len(similar_cases) > max_cases:
        st.caption(f"   ... and {len(similar_cases) - max_cases} more case(s)")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_similar_cases_count(analysis: dict) -> int:
    """
    Get count of similar cases.
    
    Args:
        analysis: Analysis dictionary
    
    Returns:
        Number of similar cases (0 if none)
    """
    similar_cases = analysis.get('similar_cases', [])
    return len(similar_cases) if similar_cases else 0


def has_similar_cases(analysis: dict) -> bool:
    """
    Check if analysis has similar cases.
    
    Args:
        analysis: Analysis dictionary
    
    Returns:
        True if similar cases exist
    """
    return get_similar_cases_count(analysis) > 0


def get_most_recent_case(analysis: dict) -> Optional[dict]:
    """
    Get the most recent similar case.
    
    Args:
        analysis: Analysis dictionary
    
    Returns:
        Most recent case dict or None
    """
    similar_cases = analysis.get('similar_cases', [])
    
    if not similar_cases or len(similar_cases) == 0:
        return None
    
    # Try to find most recent by timestamp
    cases_with_time = []
    for case in similar_cases:
        timestamp = case.get('timestamp', case.get('created_at'))
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    timestamp_str = timestamp.replace('Z', '+00:00')
                    parsed_time = datetime.fromisoformat(timestamp_str)
                elif isinstance(timestamp, datetime):
                    parsed_time = timestamp
                else:
                    continue
                
                cases_with_time.append((parsed_time, case))
            except (ValueError, AttributeError, TypeError):
                continue
    
    if cases_with_time:
        # Sort by timestamp descending (most recent first)
        cases_with_time.sort(key=lambda x: x[0], reverse=True)
        return cases_with_time[0][1]
    
    # Fallback: return first case
    return similar_cases[0]


def get_decision_distribution(analysis: dict) -> dict[str, int]:
    """
    Get distribution of decisions across similar cases.
    
    Args:
        analysis: Analysis dictionary
    
    Returns:
        Dict with decision counts
    """
    similar_cases = analysis.get('similar_cases', [])
    
    distribution = {
        'AUTONOMOUS': 0,
        'REVIEW_REQUIRED': 0,
        'ESCALATE': 0,
        'UNKNOWN': 0
    }
    
    for case in similar_cases:
        decision = case.get('decision', 'UNKNOWN')
        if decision in distribution:
            distribution[decision] += 1
        else:
            distribution['UNKNOWN'] += 1
    
    return distribution
