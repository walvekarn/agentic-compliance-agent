"""
UI Helper Functions
==================
Utility functions for common UI patterns with accessibility support.
"""

import streamlit as st
from typing import List, Any, Optional


def apply_light_theme_css():
    """
    Apply comprehensive light theme CSS to override Streamlit's default dark theme.
    Includes complete styling for all components: checkboxes, dropdowns, buttons, inputs, filters, etc.
    Call this at the top of each page to ensure consistent light theme.
    """
    st.markdown("""
    <style>
        /* ====================================================================
           BASE THEME - Force Light Theme
           ==================================================================== */
        html, body, [class*="css"] {
            background-color: #ffffff !important;
            color: #1e293b !important;
        }
        
        section[data-testid="stSidebar"] {
            background-color: #f8fafc !important;
        }
        
        section[data-testid="stSidebar"] * {
            color: #1e293b !important;
        }
        
        .stApp {
            background-color: #ffffff !important;
        }
        
        [data-testid="stAppViewContainer"] {
            background-color: #ffffff !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: #f8fafc !important;
        }
        
        [data-testid="stSidebar"] .css-1d391kg {
            background-color: #f8fafc !important;
        }
        
        .main {
            background-color: #ffffff !important;
        }
        
        /* ====================================================================
           TEXT ELEMENTS
           ==================================================================== */
        .stText, .stMarkdown, .stWrite, p, span, div, label {
            color: #1e293b !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #0f172a !important;
        }
        
        /* ====================================================================
           CHAT MESSAGE COMPONENTS - Light Theme
           ==================================================================== */
        [data-testid="stChatMessage"] {
            background-color: #ffffff !important;
        }
        
        [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] span {
            color: #1e293b !important;
        }
        
        [data-testid="stChatMessageUser"] {
            background-color: #f1f5f9 !important;
        }
        
        [data-testid="stChatMessageAssistant"] {
            background-color: #ffffff !important;
        }
        
        /* Chat input styling */
        [data-testid="stTextInput"] input {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
        }
        
        [data-testid="stTextInput"] input:focus {
            border-color: #3b82f6 !important;
            outline: 2px solid #3b82f6 !important;
        }
        
        /* Chat input container */
        [data-testid="stTextInput"] > div > div {
            background-color: #ffffff !important;
        }
        
        /* Chat input label */
        [data-testid="stTextInput"] label {
            color: #1e293b !important;
        }
        
        /* Info boxes and alerts */
        .stAlert {
            background-color: #f0f9ff !important;
            border-left: 4px solid #3b82f6 !important;
        }
        
        .stAlert p, .stAlert div {
            color: #1e293b !important;
        }
        
        /* Caption text */
        .stCaption {
            color: #64748b !important;
        }
        
        /* Expander styling */
        [data-testid="stExpander"] {
            background-color: #ffffff !important;
        }
        
        [data-testid="stExpander"] summary {
            color: #1e293b !important;
        }
        
        [data-testid="stExpander"] summary:hover {
            color: #3b82f6 !important;
        }
        
        /* Expander content - prevent black background when expanded */
        [data-testid="stExpander"] > div,
        [data-testid="stExpander"] [data-testid="element-container"],
        [data-testid="stExpander"] [data-testid="stVerticalBlock"] {
            background-color: #ffffff !important;
            color: #1e293b !important;
        }
        
        [data-testid="stExpander"] [data-testid="stMarkdownContainer"],
        [data-testid="stExpander"] [data-testid="stMarkdownContainer"] > div {
            background-color: #ffffff !important;
            color: #1e293b !important;
        }
        
        [data-testid="stExpander"] p,
        [data-testid="stExpander"] div,
        [data-testid="stExpander"] h1,
        [data-testid="stExpander"] h2,
        [data-testid="stExpander"] h3,
        [data-testid="stExpander"] h4,
        [data-testid="stExpander"] h5,
        [data-testid="stExpander"] h6,
        [data-testid="stExpander"] span,
        [data-testid="stExpander"] li,
        [data-testid="stExpander"] ul {
            color: #1e293b !important;
            background-color: #ffffff !important;
        }
        
        /* ====================================================================
           CHECKBOXES - Complete Styling (Enhanced for Light Theme)
           ==================================================================== */
        .stCheckbox {
            margin-bottom: 0.5rem;
        }
        
        .stCheckbox label {
            color: #1e293b !important;
            font-size: 1rem !important;
        }
        
        /* Checkbox box styling - Multiple selectors to override Streamlit defaults */
        .stCheckbox [data-baseweb="checkbox"],
        .stCheckbox input[type="checkbox"],
        input[type="checkbox"][data-baseweb="checkbox"],
        [data-baseweb="checkbox"] {
            background-color: #ffffff !important;
            border: 2px solid #cbd5e1 !important;
            border-radius: 4px !important;
        }
        
        .stCheckbox [data-baseweb="checkbox"]:checked,
        .stCheckbox input[type="checkbox"]:checked,
        input[type="checkbox"][data-baseweb="checkbox"]:checked,
        [data-baseweb="checkbox"]:checked {
            background-color: #3b82f6 !important;
            border-color: #3b82f6 !important;
        }
        
        /* Fix checkbox checkmark color - ensure it's white on blue */
        .stCheckbox [data-baseweb="checkbox"]:checked::after,
        .stCheckbox input[type="checkbox"]:checked::after,
        [data-baseweb="checkbox"]:checked::after {
            color: #ffffff !important;
            border-color: #ffffff !important;
        }
        
        /* Override any dark theme checkbox styling */
        .stCheckbox [data-baseweb="checkbox"] svg,
        [data-baseweb="checkbox"] svg {
            color: #3b82f6 !important;
        }
        
        .stCheckbox [data-baseweb="checkbox"]:checked svg,
        [data-baseweb="checkbox"]:checked svg {
            color: #ffffff !important;
        }
        
        .stCheckbox [data-baseweb="checkbox"]:hover {
            border-color: #3b82f6 !important;
        }
        
        .stCheckbox [data-baseweb="checkbox"]:focus {
            outline: 2px solid #3b82f6 !important;
            outline-offset: 2px !important;
        }
        
        /* Force checkbox background - stronger override for dark theme */
        .stCheckbox [data-baseweb="checkbox"] > div,
        .stCheckbox [data-baseweb="checkbox"] > div > div {
            background-color: #ffffff !important;
        }
        
        .stCheckbox [data-baseweb="checkbox"]:checked > div,
        .stCheckbox [data-baseweb="checkbox"]:checked > div > div {
            background-color: #3b82f6 !important;
        }
        
        /* Checkbox SVG checkmark - ensure white on blue */
        .stCheckbox [data-baseweb="checkbox"]:checked svg path,
        .stCheckbox [data-baseweb="checkbox"]:checked svg {
            stroke: #ffffff !important;
            fill: #ffffff !important;
            color: #ffffff !important;
        }
        
        /* Override any dark checkbox backgrounds */
        .stCheckbox [data-baseweb="checkbox"] {
            background: #ffffff !important;
        }
        
        .stCheckbox [data-baseweb="checkbox"]:checked {
            background: #3b82f6 !important;
        }
        
        /* ====================================================================
           DROPDOWNS/SELECTBOXES - Complete Styling
           ==================================================================== */
        .stSelectbox [data-baseweb="select"] > div {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
        }
        
        .stSelectbox [data-baseweb="select"] span {
            color: #1e293b !important;
        }
        
        .stSelectbox [data-baseweb="select"]:hover {
            border-color: #3b82f6 !important;
        }
        
        .stSelectbox [data-baseweb="select"]:focus {
            border-color: #3b82f6 !important;
            outline: 2px solid #3b82f6 !important;
            outline-offset: 2px !important;
        }
        
        .stSelectbox label {
            color: #1e293b !important;
        }
        
        /* Dropdown options list */
        [data-baseweb="popover"] {
            background-color: #ffffff !important;
        }
        
        [data-baseweb="popover"] [role="option"] {
            color: #1e293b !important;
            background-color: #ffffff !important;
        }
        
        [data-baseweb="popover"] [role="option"]:hover {
            background-color: #f1f5f9 !important;
        }
        
        /* ====================================================================
           MULTISELECT - Complete Styling
           ==================================================================== */
        .stMultiSelect [data-baseweb="select"] > div {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
        }
        
        .stMultiSelect [data-baseweb="select"] span {
            color: #1e293b !important;
        }
        
        .stMultiSelect [data-baseweb="select"]:hover {
            border-color: #3b82f6 !important;
        }
        
        .stMultiSelect [data-baseweb="select"]:focus {
            border-color: #3b82f6 !important;
            outline: 2px solid #3b82f6 !important;
            outline-offset: 2px !important;
        }
        
        .stMultiSelect [data-baseweb="tag"] {
            background-color: #3b82f6 !important;
            color: #ffffff !important;
            border-radius: 4px !important;
        }
        
        .stMultiSelect label {
            color: #1e293b !important;
        }
        
        /* ====================================================================
           TEXT INPUTS - Complete Styling
           ==================================================================== */
        .stTextInput > div > div > input {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
            padding: 0.5rem 0.75rem !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #3b82f6 !important;
            outline: 2px solid #3b82f6 !important;
            outline-offset: 2px !important;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: #94a3b8 !important;
        }
        
        .stTextInput label {
            color: #1e293b !important;
        }
        
        /* Password input styling - fix black background */
        .stTextInput input[type="password"],
        input[type="password"],
        [data-baseweb="input"] input[type="password"] {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
        }
        
        /* Password visibility toggle button container */
        .stTextInput > div > div > div:last-child,
        [data-baseweb="input"] > div:last-child {
            background-color: #ffffff !important;
        }
        
        /* Password visibility toggle button */
        .stTextInput button[data-testid="baseButton-secondary"],
        [data-baseweb="input"] button {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            color: #1e293b !important;
        }
        
        /* Eye icon in password field */
        .stTextInput button svg,
        [data-baseweb="input"] button svg {
            color: #1e293b !important;
        }
        
        /* ====================================================================
           TEXT AREAS - Complete Styling
           ==================================================================== */
        .stTextArea > div > div > textarea {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
            padding: 0.5rem 0.75rem !important;
        }
        
        .stTextArea > div > div > textarea:focus {
            border-color: #3b82f6 !important;
            outline: 2px solid #3b82f6 !important;
            outline-offset: 2px !important;
        }
        
        .stTextArea label {
            color: #1e293b !important;
        }
        
        /* ====================================================================
           BUTTONS - Complete Styling with States
           ==================================================================== */
        .stButton > button {
            background-color: #3b82f6 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.5rem 1.5rem !important;
            font-weight: 600 !important;
            transition: all 0.2s !important;
        }
        
        .stButton > button:hover {
            background-color: #2563eb !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3) !important;
        }
        
        .stButton > button:active {
            background-color: #1d4ed8 !important;
            transform: translateY(0) !important;
        }
        
        .stButton > button:focus {
            outline: 2px solid #3b82f6 !important;
            outline-offset: 2px !important;
        }
        
        .stButton > button:disabled {
            background-color: #cbd5e1 !important;
            color: #94a3b8 !important;
            cursor: not-allowed !important;
        }
        
        /* Secondary button style - Enhanced */
        .stButton > button[kind="secondary"],
        button[kind="secondary"],
        .stButton > button[data-kind="secondary"] {
            background-color: #f1f5f9 !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
            font-weight: 600 !important;
        }
        
        .stButton > button[kind="secondary"]:hover,
        button[kind="secondary"]:hover,
        .stButton > button[data-kind="secondary"]:hover {
            background-color: #e2e8f0 !important;
            border-color: #94a3b8 !important;
            color: #0f172a !important;
        }
        
        /* Download button styling */
        .stDownloadButton > button,
        button[data-testid="baseButton-secondary"],
        .stDownloadButton button {
            background-color: #3b82f6 !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 600 !important;
        }
        
        .stDownloadButton > button:hover,
        button[data-testid="baseButton-secondary"]:hover,
        .stDownloadButton button:hover {
            background-color: #2563eb !important;
            color: #ffffff !important;
        }
        
        /* Export section buttons - ensure they're visible */
        button:has-text("Download"),
        button:contains("Download"),
        .stButton button:contains("Download") {
            background-color: #3b82f6 !important;
            color: #ffffff !important;
        }
        
        /* Override any dark button backgrounds */
        button {
            background-color: #3b82f6 !important;
            color: #ffffff !important;
        }
        
        button[kind="secondary"] {
            background-color: #f1f5f9 !important;
            color: #1e293b !important;
        }
        
        /* ====================================================================
           DATE INPUTS - Complete Styling
           ==================================================================== */
        .stDateInput > div > div > input,
        input[type="date"],
        [data-baseweb="input"] input {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
        }
        
        /* Date input container - fix black borders */
        .stDateInput > div,
        .stDateInput > div > div,
        [data-baseweb="input"] {
            background-color: #ffffff !important;
            border: none !important;
        }
        
        /* Date picker calendar icon button */
        .stDateInput button,
        [data-baseweb="input"] button,
        .stDateInput [data-baseweb="button"] {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
        }
        
        /* Remove any black lines/borders */
        .stDateInput > div > div > div:last-child {
            background-color: #ffffff !important;
            border: none !important;
        }
        
        .stDateInput label {
            color: #1e293b !important;
        }
        
        /* Calendar popup */
        [data-baseweb="calendar"] {
            background-color: #ffffff !important;
        }
        
        /* ====================================================================
           NUMBER INPUTS - Complete Styling
           ==================================================================== */
        .stNumberInput > div > div > input {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 6px !important;
        }
        
        .stNumberInput label {
            color: #1e293b !important;
        }
        
        /* ====================================================================
           ALERTS - Theme Override
           ==================================================================== */
        .stAlert {
            background-color: #f8fafc !important;
            border-left: 4px solid #3b82f6 !important;
        }
        
        .stAlert [data-baseweb="notification"] {
            background-color: #f8fafc !important;
        }
        
        /* ====================================================================
           FORMS - Layout and Alignment
           ==================================================================== */
        .stForm {
            background-color: #ffffff !important;
            padding: 1.5rem !important;
            border-radius: 8px !important;
        }
        
        /* Form elements alignment */
        .stForm .stTextInput,
        .stForm .stSelectbox,
        .stForm .stMultiSelect,
        .stForm .stCheckbox,
        .stForm .stDateInput,
        .stForm .stNumberInput {
            margin-bottom: 1rem !important;
        }
        
        /* Form column alignment */
        .stForm [data-testid="column"] {
            display: flex !important;
            flex-direction: column !important;
        }
        
        /* Filter alignment */
        [data-testid="column"] .stSelectbox,
        [data-testid="column"] .stMultiSelect {
            width: 100% !important;
        }
        
        /* ====================================================================
           TABLES/DATAFRAMES - Theme Override
           ==================================================================== */
        .stDataFrame {
            background-color: #ffffff !important;
        }
        
        .stDataFrame table {
            background-color: #ffffff !important;
        }
        
        .stDataFrame th {
            background-color: #f8fafc !important;
            color: #1e293b !important;
        }
        
        .stDataFrame td {
            background-color: #ffffff !important;
            color: #1e293b !important;
        }
        
        /* ====================================================================
           METRICS - Consistent Styling
           ==================================================================== */
        .stMetric {
            background-color: #ffffff !important;
            padding: 1.5rem !important;
            border-radius: 12px !important;
            border: 2px solid #e2e8f0 !important;
        }
        
        .stMetric label {
            color: #475569 !important;
            font-size: 1rem !important;
            font-weight: 600 !important;
        }
        
        .stMetric [data-testid="stMetricValue"] {
            color: #0f172a !important;
            font-size: 2rem !important;
            font-weight: 800 !important;
        }
        
        /* ====================================================================
           HELP TEXT/TOOLTIPS
           ==================================================================== */
        .stTooltip,
        .stHelp {
            color: #64748b !important;
        }
        
        /* ====================================================================
           OVERRIDE STREAMLIT'S DARK INPUT BACKGROUNDS
           ==================================================================== */
        input[type="text"],
        input[type="number"],
        input[type="date"],
        textarea,
        select {
            background-color: #ffffff !important;
            color: #1e293b !important;
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
