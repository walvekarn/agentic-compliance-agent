"""
Confidence Display Component
=============================
Visual confidence meter with interpretation and context.

Status: ✅ IMPLEMENTED
Priority: P0 - Critical
"""

import streamlit as st
from typing import Optional


def render_confidence_meter(analysis: dict) -> None:
    """
    Render visual confidence meter with interpretation.
    
    Features:
    - Auto-detects 0-1 or 0-100 format
    - Visual progress bar with color coding
    - Emoji indicators based on confidence level
    - Contextual explanation of what confidence means
    - Similar cases count integration
    - Confidence scale reference (expandable)
    
    Args:
        analysis: Dictionary containing analysis results
                  Expected keys: confidence_score, confidence, similar_cases
    
    Graceful degradation:
        - Missing confidence defaults to 0.5 (50%)
        - Missing similar_cases defaults to empty list
        - Handles both 0-1 and 0-100 formats automatically
    """
    
    # =========================================================================
    # EXTRACT AND NORMALIZE CONFIDENCE SCORE
    # =========================================================================
    confidence_raw = _extract_confidence(analysis)
    confidence_normalized = _normalize_confidence(confidence_raw)
    confidence_percent = confidence_normalized * 100
    
    # =========================================================================
    # EXTRACT SIMILAR CASES COUNT
    # =========================================================================
    similar_cases = analysis.get('similar_cases', [])
    similar_cases_count = len(similar_cases) if similar_cases else 0
    
    # =========================================================================
    # DETERMINE CONFIDENCE LEVEL AND STYLING
    # =========================================================================
    emoji, label, color, explanation = _get_confidence_visual(
        confidence_normalized, 
        similar_cases_count
    )
    
    # =========================================================================
    # RENDER CONFIDENCE SECTION
    # =========================================================================
    st.markdown(f"### {emoji} **Confidence Level: {label}** ({confidence_percent:.0f}%)")
    
    # Visual progress bar with color-coded text
    _render_progress_bar(confidence_normalized, label)
    
    # Contextual explanation
    with st.container():
        st.markdown("**What this means:**")
        for point in explanation:
            st.markdown(f"• {point}")
        
        # Similar cases context (if available)
        if similar_cases_count > 0:
            st.info(f"📊 **Based on {similar_cases_count} similar past case{'s' if similar_cases_count != 1 else ''}**")
        
        # Expandable confidence scale reference
        with st.expander("ℹ️ Understanding Confidence Scores", expanded=False):
            st.markdown("""
            **Confidence shows how certain the AI is about this recommendation:**
            
            - **🟢 75-100%**: High Confidence - Standard scenario, proceed with assurance
            - **🟡 40-74%**: Medium Confidence - Review recommended before proceeding
            - **🔴 Below 40%**: Low Confidence - Requires expert consultation
            
            **Higher confidence = More similar past cases + Clearer risk factors**
            
            The AI considers:
            - How similar your situation is to past analyzed cases
            - Clarity of applicable regulations
            - Completeness of the information provided
            - Complexity of jurisdictional requirements
            """)


def _extract_confidence(analysis: dict) -> float:
    """
    Extract confidence score from analysis dict.
    
    Tries multiple possible keys:
    - confidence_score (primary)
    - confidence (fallback)
    - defaults to 0.5 if missing
    
    Args:
        analysis: Analysis dictionary
    
    Returns:
        Raw confidence value (could be 0-1 or 0-100 format)
    """
    # Try primary key
    confidence = analysis.get('confidence_score')
    
    # Try fallback key
    if confidence is None:
        confidence = analysis.get('confidence')
    
    # Default to medium confidence if missing
    if confidence is None:
        return 0.5
    
    # Handle string values
    if isinstance(confidence, str):
        try:
            confidence = float(confidence)
        except (ValueError, TypeError):
            return 0.5
    
    return float(confidence)


def _normalize_confidence(confidence_raw: float) -> float:
    """
    Normalize confidence to 0-1 range.
    
    Auto-detects format:
    - If > 1.0: assumes 0-100 format, divides by 100
    - If 0-1: uses as-is
    
    Args:
        confidence_raw: Raw confidence value
    
    Returns:
        Normalized confidence in 0-1 range
    """
    # Handle 0-100 format
    if confidence_raw > 1.0:
        normalized = confidence_raw / 100.0
    else:
        normalized = confidence_raw
    
    # Clamp to valid range
    normalized = max(0.0, min(1.0, normalized))
    
    return normalized


def _get_confidence_visual(
    confidence: float, 
    similar_cases_count: int = 0
) -> tuple[str, str, str, list[str]]:
    """
    Get visual indicators and explanation for confidence level.
    
    Args:
        confidence: Normalized confidence (0-1)
        similar_cases_count: Number of similar past cases
    
    Returns:
        Tuple of (emoji, label, color, explanation_points)
    """
    # High confidence (>= 75%)
    if confidence >= 0.75:
        emoji = "🟢"
        label = "High Confidence"
        color = "success"
        explanation = [
            f"Based on {similar_cases_count} similar decision(s)" if similar_cases_count > 0 else "Standard compliance scenario",
            "All risk factors clearly defined",
            "High reliability - you can proceed with assurance"
        ]
    
    # Medium confidence (40-74%)
    elif confidence >= 0.40:
        emoji = "🟡"
        label = "Medium Confidence"
        color = "warning"
        explanation = [
            f"Based on {similar_cases_count} similar decision(s)" if similar_cases_count > 0 else "Moderately common scenario",
            "Most risk factors identified",
            "Reliable guidance - review recommended before proceeding"
        ]
    
    # Low confidence (< 40%)
    else:
        emoji = "🔴"
        label = "Low Confidence"
        color = "error"
        explanation = [
            f"Very limited precedent ({similar_cases_count} similar case(s))" if similar_cases_count > 0 else "Uncommon or complex scenario",
            "Risk factors unclear or incomplete",
            "Requires expert review before proceeding"
        ]
    
    return emoji, label, color, explanation


def _render_progress_bar(confidence: float, label: str) -> None:
    """
    Render visual progress bar with color-coded label.
    
    Args:
        confidence: Normalized confidence (0-1)
        label: Confidence level label
    """
    # Determine progress bar text based on confidence level
    if confidence >= 0.75:
        progress_text = f"🎯 {label}"
    elif confidence >= 0.40:
        progress_text = f"⚠️ {label}"
    else:
        progress_text = f"⚠️ {label} - Expert Review Needed"
    
    # Render progress bar
    st.progress(confidence, text=progress_text)


# =============================================================================
# ALTERNATIVE COMPACT RENDERING (for use in recommendations, etc.)
# =============================================================================

def render_confidence_compact(
    confidence: float, 
    similar_cases_count: int = 0,
    show_progress: bool = True
) -> None:
    """
    Render compact confidence display for use in recommendations or sidebars.
    
    Args:
        confidence: Confidence score (0-1 or 0-100, auto-normalized)
        similar_cases_count: Number of similar cases
        show_progress: Whether to show progress bar
    """
    # Normalize
    confidence_normalized = _normalize_confidence(confidence)
    confidence_percent = confidence_normalized * 100
    
    # Get visuals
    emoji, label, color, explanation = _get_confidence_visual(
        confidence_normalized, 
        similar_cases_count
    )
    
    # Compact display
    st.markdown(f"{emoji} **{label}**: {confidence_percent:.0f}%")
    
    if show_progress:
        st.progress(confidence_normalized)
    
    # Brief explanation
    if explanation:
        st.caption(f"└─ {explanation[0]}")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_confidence_emoji(confidence: float) -> str:
    """
    Get emoji for confidence level (utility function).
    
    Args:
        confidence: Confidence score (0-1 or 0-100)
    
    Returns:
        Emoji string
    """
    confidence_normalized = _normalize_confidence(confidence)
    emoji, _, _, _ = _get_confidence_visual(confidence_normalized)
    return emoji


def get_confidence_label(confidence: float) -> str:
    """
    Get label for confidence level (utility function).
    
    Args:
        confidence: Confidence score (0-1 or 0-100)
    
    Returns:
        Label string
    """
    confidence_normalized = _normalize_confidence(confidence)
    _, label, _, _ = _get_confidence_visual(confidence_normalized)
    return label


def get_confidence_interpretation(confidence: float) -> tuple[str, str, str]:
    """
    Get full interpretation of confidence level.
    
    Args:
        confidence: Confidence score (0-1 or 0-100)
    
    Returns:
        Tuple of (emoji, label, color)
    """
    confidence_normalized = _normalize_confidence(confidence)
    emoji, label, color, _ = _get_confidence_visual(confidence_normalized)
    return emoji, label, color

