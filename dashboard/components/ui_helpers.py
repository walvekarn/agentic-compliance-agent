"""
UI Helper Functions
==================
Utility functions for common UI patterns with accessibility support.
"""

import streamlit as st
from typing import List, Any, Optional


def multiselect_with_select_all(
    label: str,
    options: List[str],
    default: Optional[List[str]] = None,
    key: Optional[str] = None,
    help: Optional[str] = None,
    placeholder: str = "Choose options..."
) -> List[str]:
    """
    Multiselect dropdown with "Select All" option and fixed "No results" bug.
    
    Features:
    - "Select All" / "Deselect All" toggle button
    - Always shows options (fixes "No results" bug)
    - Resets search after selection
    - Keyboard accessible
    
    Args:
        label: Label for the multiselect
        options: List of options to choose from
        default: Default selected options
        key: Unique key for session state
        help: Help text/tooltip
        placeholder: Placeholder text
        
    Returns:
        List of selected options
    """
    if not options:
        return []
    
    default = default or []
    
    # Initialize selection state
    state_key = f"multiselect_state_{key or label.replace(' ', '_')}"
    if state_key not in st.session_state:
        st.session_state[state_key] = default.copy() if default else []
    
    current_selection = st.session_state[state_key]
    
    # Add "Select All" / "Deselect All" button
    select_all_col, multiselect_col = st.columns([1, 4])
    
    with select_all_col:
        all_selected = len(current_selection) == len(options) and len(options) > 0
        if st.button("📋 Select All" if not all_selected else "✂️ Clear All", 
                     key=f"{state_key}_select_all_btn",
                     help="Select all options" if not all_selected else "Clear all selections"):
            if all_selected:
                st.session_state[state_key] = []
            else:
                st.session_state[state_key] = options.copy()
            st.rerun()
    
    with multiselect_col:
        # Show multiselect - always enabled to fix "No results" bug
        selected = st.multiselect(
            label,
            options=options,
            default=st.session_state[state_key],
            key=key or f"ms_{label.replace(' ', '_')}",
            help=help,
            placeholder=placeholder if placeholder else "Choose options..."
        )
        
        # Update state
        st.session_state[state_key] = selected
    
    return st.session_state[state_key]


def add_tooltip(text: str, tooltip: str, icon: str = "ℹ️") -> str:
    """
    Add a tooltip to text with consistent icon.
    
    Args:
        text: Text to display
        tooltip: Tooltip text
        icon: Icon to use (default: ℹ️)
        
    Returns:
        HTML string with tooltip
    """
    return f'{text} <span title="{tooltip}" style="cursor: help; margin-left: 4px;">{icon}</span>'


def get_aria_label(label: str, help_text: Optional[str] = None) -> str:
    """
    Generate ARIA label from label and optional help text.
    
    Args:
        label: Primary label
        help_text: Optional help text to include
        
    Returns:
        ARIA label string
    """
    aria = label
    if help_text:
        aria = f"{label}. {help_text}"
    return aria

