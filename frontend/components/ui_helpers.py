"""
UI Helper Functions
==================
Utility functions for common UI patterns with accessibility support.
"""

import streamlit as st
from typing import List, Any, Optional


def apply_light_theme_css():
    """
    Apply light theme CSS to override Streamlit's default dark theme.
    Call this at the top of each page to ensure consistent light theme.
    """
    st.markdown("""
    <style>
        /* FORCE LIGHT THEME - Override Streamlit's default dark theme */
        html, body, [class*="css"] {
            background-color: #ffffff !important;
            color: #1e293b !important;
        }
        
        /* Override Streamlit's sidebar dark theme */
        section[data-testid="stSidebar"] {
            background-color: #f8fafc !important;
        }
        
        section[data-testid="stSidebar"] * {
            color: #1e293b !important;
        }
        
        /* Override main app background */
        .stApp {
            background-color: #ffffff !important;
        }
        
        /* Force all Streamlit text elements to be dark */
        .stText, .stMarkdown, .stWrite, p, span, div, label {
            color: #1e293b !important;
        }
        
        /* Override Streamlit's default text colors */
        h1, h2, h3, h4, h5, h6 {
            color: #0f172a !important;
        }
        
        /* Ensure buttons are visible */
        .stButton > button {
            background-color: #3b82f6 !important;
            color: #ffffff !important;
            border: none !important;
        }
        
        /* Override any dark backgrounds in Streamlit components */
        [data-testid="stAppViewContainer"] {
            background-color: #ffffff !important;
        }
        
        /* Force sidebar to be light */
        [data-testid="stSidebar"] {
            background-color: #f8fafc !important;
        }
        
        [data-testid="stSidebar"] .css-1d391kg {
            background-color: #f8fafc !important;
        }
        
        /* Main container */
        .main {
            background-color: #ffffff !important;
        }
        
        /* FORM ELEMENTS - Force light theme */
        /* Text inputs */
        .stTextInput > div > div > input {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
        }
        
        .stTextInput label {
            color: #1e293b !important;
        }
        
        /* Text areas */
        .stTextArea > div > div > textarea {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
        }
        
        .stTextArea label {
            color: #1e293b !important;
        }
        
        /* Selectboxes */
        .stSelectbox > div > div > select {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
        }
        
        .stSelectbox label {
            color: #1e293b !important;
        }
        
        /* Multiselect */
        .stMultiSelect > div > div {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
        }
        
        .stMultiSelect label {
            color: #1e293b !important;
        }
        
        /* Checkboxes */
        .stCheckbox label {
            color: #1e293b !important;
        }
        
        /* Date inputs */
        .stDateInput > div > div > input {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
        }
        
        .stDateInput label {
            color: #1e293b !important;
        }
        
        /* Number inputs */
        .stNumberInput > div > div > input {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
        }
        
        .stNumberInput label {
            color: #1e293b !important;
        }
        
        /* Override Streamlit's dark input backgrounds */
        input[type="text"],
        input[type="number"],
        input[type="date"],
        textarea,
        select {
            background-color: #ffffff !important;
            color: #1e293b !important;
        }
        
        /* Form containers */
        .stForm {
            background-color: #ffffff !important;
        }
        
        /* Help text */
        .stTooltip,
        .stHelp {
            color: #64748b !important;
        }
    </style>
    """, unsafe_allow_html=True)


def multiselect_with_select_all(
    label: str,
    options: List[str],
    default: Optional[List[str]] = None,
    key: Optional[str] = None,
    help: Optional[str] = None,
    placeholder: str = "Choose options...",
    inside_form: bool = True
) -> List[str]:
    """
    Multiselect dropdown with "Select All" option and fixed "No results" bug.
    
    Features:
    - "Select All" / "Deselect All" toggle button
    - Always shows options (fixes "No results" bug)
    - Resets search after selection
    - Keyboard accessible
    - Form-safe mode (uses checkbox instead of button when inside_form=True)
    
    Args:
        label: Label for the multiselect
        options: List of options to choose from
        default: Default selected options
        key: Unique key for session state
        help: Help text/tooltip
        placeholder: Placeholder text
        inside_form: If True, uses checkbox for "Select All" (form-safe). If False, uses button.
        
    Returns:
        List of selected options
    """
    if not options:
        return []
    
    default = default or []
    
    # Initialize selection state
    state_key = f"multiselect_state_{key or label.replace(' ', '_')}"
    
    # If default is provided and state is empty or different, update it
    if default and (state_key not in st.session_state or st.session_state[state_key] != default):
        st.session_state[state_key] = default.copy()
    
    # Initialize if still not set
    if state_key not in st.session_state:
        st.session_state[state_key] = []
    
    current_selection = st.session_state[state_key]
    
    # Add "Select All" / "Deselect All" toggle
    select_all_col, multiselect_col = st.columns([1, 4])
    
    with select_all_col:
        all_selected = len(current_selection) == len(options) and len(options) > 0

        if inside_form:
        # SAFE toggle for forms (checkbox instead of button)
        toggle = st.checkbox(
            "📋 Select All" if not all_selected else "✂️ Clear All",
            value=all_selected,
            key=f"{state_key}_select_all_toggle",
            help="Select all options" if not all_selected else "Clear all selections"
        )
        else:
            # Use button when not in form (better UX outside forms)
            if st.button(
                "📋 Select All" if not all_selected else "✂️ Clear All",
                key=f"{state_key}_select_all_toggle",
                help="Select all options" if not all_selected else "Clear all selections",
                width="stretch"
            ):
                toggle = not all_selected
            else:
                toggle = all_selected

        # If user toggles, update state
        if toggle != all_selected:
            if toggle:
                st.session_state[state_key] = options.copy()
            else:
                st.session_state[state_key] = []
    
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
