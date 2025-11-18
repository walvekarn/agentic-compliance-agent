"""
Proactive Suggestions Display Component
========================================
AI-generated insights and recommendations shown before main results.

Status: ✅ IMPLEMENTED
Priority: P0 - Critical (Core agentic feature)
"""

import streamlit as st
from typing import Optional


def render_proactive_suggestions(analysis: dict) -> None:
    """
    Render proactive AI suggestions and insights.
    
    This is a core agentic feature that demonstrates the AI's ability to
    proactively identify issues, opportunities, and recommendations before
    the user even asks.
    
    Features:
    - Severity-based styling (HIGH → warning, MEDIUM → info, LOW → success)
    - Icon and title support
    - Message and suggestion text
    - Optional action buttons
    - Priority grouping (high priority shown first)
    - Graceful handling of minimal or full data formats
    
    Args:
        analysis: Dictionary containing analysis results
                  Expected keys: proactive_suggestions (List[dict])
    
    Data formats supported:
        Minimal: {"severity": "HIGH", "message": "Text"}
        Full: {"priority": "high", "icon": "💡", "title": "Title",
               "message": "Text", "suggestion": "Text", "action_label": "Text"}
    
    Graceful degradation:
        - Missing proactive_suggestions: shows nothing
        - Empty list: shows nothing
        - Missing fields: displays available information only
    """
    
    # =========================================================================
    # EXTRACT PROACTIVE SUGGESTIONS
    # =========================================================================
    proactive_suggestions = analysis.get('proactive_suggestions')
    
    # Graceful exit if no suggestions
    if not proactive_suggestions:
        return
    
    # Check if list is empty
    if not isinstance(proactive_suggestions, list) or len(proactive_suggestions) == 0:
        return
    
    # =========================================================================
    # RENDER PROACTIVE SUGGESTIONS SECTION
    # =========================================================================
    st.markdown("---")
    st.markdown("## 💡 Before You Continue...")
    st.markdown("""
    <p style='font-size: 1.1rem; color: #64748b; margin-bottom: 1.5rem;'>
    The AI agent noticed a few things you should know:
    </p>
    """, unsafe_allow_html=True)
    
    # Group suggestions by priority/severity
    high_priority, medium_priority, low_priority = _group_suggestions_by_priority(
        proactive_suggestions
    )
    
    # Display high priority suggestions first (most prominent)
    for suggestion in high_priority:
        _render_suggestion_card(suggestion, 'HIGH')
    
    # Display medium priority in expandable section if multiple
    if medium_priority:
        if len(medium_priority) == 1:
            _render_suggestion_card(medium_priority[0], 'MEDIUM')
        else:
            with st.expander(
                f"ℹ️ Additional Insights ({len(medium_priority)})",
                expanded=False
            ):
                for suggestion in medium_priority:
                    _render_suggestion_card(suggestion, 'MEDIUM')
    
    # Display low priority suggestions in collapsed expander
    if low_priority:
        with st.expander(
            f"✅ Optional Optimizations ({len(low_priority)})",
            expanded=False
        ):
            for suggestion in low_priority:
                _render_suggestion_card(suggestion, 'LOW')


def _group_suggestions_by_priority(
    suggestions: list[dict]
) -> tuple[list, list, list]:
    """
    Group suggestions by priority/severity level.
    
    Args:
        suggestions: List of suggestion dicts
    
    Returns:
        Tuple of (high_priority, medium_priority, low_priority) lists
    """
    high = []
    medium = []
    low = []
    
    for suggestion in suggestions:
        # Determine priority level (check both priority and severity fields)
        priority = _get_suggestion_priority(suggestion)
        
        if priority == 'HIGH':
            high.append(suggestion)
        elif priority == 'MEDIUM':
            medium.append(suggestion)
        else:  # LOW
            low.append(suggestion)
    
    return high, medium, low


def _get_suggestion_priority(suggestion: dict) -> str:
    """
    Extract priority level from suggestion.
    
    Checks multiple fields:
    - severity (HIGH/MEDIUM/LOW)
    - priority (high/medium/low)
    
    Args:
        suggestion: Suggestion dict
    
    Returns:
        Priority level: HIGH, MEDIUM, or LOW
    """
    # Check severity field (uppercase)
    severity = suggestion.get('severity', '').upper()
    if severity in ['HIGH', 'MEDIUM', 'LOW']:
        return severity
    
    # Check priority field (lowercase)
    priority = suggestion.get('priority', '').lower()
    if priority == 'high':
        return 'HIGH'
    elif priority == 'medium':
        return 'MEDIUM'
    elif priority == 'low':
        return 'LOW'
    
    # Default to MEDIUM if not specified
    return 'MEDIUM'


def _render_suggestion_card(suggestion: dict, priority: str) -> None:
    """
    Render a single suggestion card with appropriate styling.
    
    Args:
        suggestion: Suggestion dict with message, title, icon, etc.
        priority: Priority level (HIGH, MEDIUM, LOW)
    """
    # Extract suggestion details
    icon = suggestion.get('icon', _get_default_icon(priority))
    title = suggestion.get('title', 'Suggestion')
    message = suggestion.get('message', '')
    suggestion_text = suggestion.get('suggestion', '')
    action_label = suggestion.get('action_label')
    action_type = suggestion.get('action')
    
    # Build suggestion content
    content = _build_suggestion_content(
        icon, title, message, suggestion_text
    )
    
    # Display with appropriate styling based on priority
    if priority == 'HIGH':
        st.warning(content)
    elif priority == 'MEDIUM':
        st.info(content)
    else:  # LOW
        st.success(content)
    
    # Render action button if present
    if action_label and action_type:
        _render_suggestion_action(action_label, action_type)


def _build_suggestion_content(
    icon: str,
    title: str,
    message: str,
    suggestion: str
) -> str:
    """
    Build formatted suggestion content string.
    
    Args:
        icon: Emoji icon
        title: Suggestion title
        message: Main message text
        suggestion: Suggestion/recommendation text
    
    Returns:
        Formatted markdown string
    """
    parts = []
    
    # Title with icon
    if title:
        parts.append(f"**{icon} {title}**")
    
    # Message
    if message:
        parts.append(f"\n{message}")
    
    # Suggestion
    if suggestion:
        parts.append(f"\n💡 **Suggestion**: {suggestion}")
    
    return "\n".join(parts) if parts else "No details provided"


def _get_default_icon(priority: str) -> str:
    """
    Get default icon for priority level.
    
    Args:
        priority: Priority level
    
    Returns:
        Emoji icon
    """
    icon_map = {
        'HIGH': '⚠️',
        'MEDIUM': 'ℹ️',
        'LOW': '✅'
    }
    return icon_map.get(priority, '💡')


def _render_suggestion_action(action_label: str, action_type: str) -> None:
    """
    Render action button for suggestion.
    
    Args:
        action_label: Button label
        action_type: Action type (view_calendar, view_history, etc.)
    """
    if action_type == 'view_calendar':
        if st.button(
            f"📅 {action_label}",
            key=f"action_calendar_{hash(action_label)}"
        ):
            st.switch_page("pages/2_Compliance_Calendar.py")
    
    elif action_type == 'view_history':
        # Display inline note instead of navigation
        st.info(
            "📊 **Similar cases are displayed below** in the "
            "'Agent Memory: Similar Past Cases' section."
        )
    
    elif action_type == 'view_audit':
        if st.button(
            f"📋 {action_label}",
            key=f"action_audit_{hash(action_label)}"
        ):
            st.switch_page("pages/3_Audit_Trail.py")
    
    else:
        # Generic action button (no navigation)
        st.caption(f"💡 {action_label}")


# =============================================================================
# ALTERNATIVE COMPACT RENDERING
# =============================================================================

def render_suggestions_summary(analysis: dict) -> None:
    """
    Render compact summary of suggestions (count by severity).
    
    Use this for dashboard views or quick reference.
    
    Args:
        analysis: Analysis dictionary
    """
    suggestions = analysis.get('proactive_suggestions', [])
    
    if not suggestions or len(suggestions) == 0:
        return
    
    high, medium, low = _group_suggestions_by_priority(suggestions)
    
    summary_parts = []
    if high:
        summary_parts.append(f"⚠️ {len(high)} high priority")
    if medium:
        summary_parts.append(f"ℹ️ {len(medium)} medium priority")
    if low:
        summary_parts.append(f"✅ {len(low)} low priority")
    
    summary_text = " | ".join(summary_parts)
    st.info(f"💡 **Suggestions**: {summary_text}")


def render_suggestions_inline(analysis: dict, max_suggestions: int = 3) -> None:
    """
    Render inline suggestions list (no cards).
    
    Args:
        analysis: Analysis dictionary
        max_suggestions: Maximum number to display
    """
    suggestions = analysis.get('proactive_suggestions', [])
    
    if not suggestions or len(suggestions) == 0:
        return
    
    st.markdown("#### 💡 AI Suggestions")
    
    for i, suggestion in enumerate(suggestions[:max_suggestions], 1):
        priority = _get_suggestion_priority(suggestion)
        icon = suggestion.get('icon', _get_default_icon(priority))
        title = suggestion.get('title', 'Suggestion')
        message = suggestion.get('message', '')
        
        st.markdown(f"**{i}.** {icon} **{title}**: {message[:100]}{'...' if len(message) > 100 else ''}")
    
    if len(suggestions) > max_suggestions:
        st.caption(f"   ... and {len(suggestions) - max_suggestions} more suggestion(s)")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_suggestions_count(analysis: dict) -> int:
    """
    Get count of proactive suggestions.
    
    Args:
        analysis: Analysis dictionary
    
    Returns:
        Number of suggestions (0 if none)
    """
    suggestions = analysis.get('proactive_suggestions', [])
    return len(suggestions) if suggestions else 0


def has_suggestions(analysis: dict) -> bool:
    """
    Check if analysis has proactive suggestions.
    
    Args:
        analysis: Analysis dictionary
    
    Returns:
        True if suggestions exist
    """
    return get_suggestions_count(analysis) > 0


def get_high_priority_suggestions(analysis: dict) -> list[dict]:
    """
    Get only high priority suggestions.
    
    Args:
        analysis: Analysis dictionary
    
    Returns:
        List of high priority suggestion dicts
    """
    suggestions = analysis.get('proactive_suggestions', [])
    
    if not suggestions:
        return []
    
    high, _, _ = _group_suggestions_by_priority(suggestions)
    return high


def get_suggestions_by_priority(analysis: dict) -> dict[str, list]:
    """
    Get suggestions grouped by priority level.
    
    Args:
        analysis: Analysis dictionary
    
    Returns:
        Dict with HIGH, MEDIUM, LOW keys
    """
    suggestions = analysis.get('proactive_suggestions', [])
    
    if not suggestions:
        return {'HIGH': [], 'MEDIUM': [], 'LOW': []}
    
    high, medium, low = _group_suggestions_by_priority(suggestions)
    
    return {
        'HIGH': high,
        'MEDIUM': medium,
        'LOW': low
    }


def format_suggestion_summary(suggestion: dict) -> str:
    """
    Format a single suggestion as a summary string.
    
    Args:
        suggestion: Suggestion dict
    
    Returns:
        Formatted summary string
    """
    priority = _get_suggestion_priority(suggestion)
    icon = suggestion.get('icon', _get_default_icon(priority))
    title = suggestion.get('title', 'Suggestion')
    message = suggestion.get('message', '')
    
    summary = f"{icon} {title}"
    if message:
        # Truncate long messages
        message_preview = message[:80] + '...' if len(message) > 80 else message
        summary += f": {message_preview}"
    
    return summary

