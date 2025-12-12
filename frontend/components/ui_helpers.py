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
    # PERFORMANCE FIX: Use a single session-wide flag to prevent redundant CSS injection
    # CSS is idempotent, but injecting 1488 lines on every page load is expensive
    # Use a persistent key that survives page switches but resets on app restart
    theme_applied_key = "_light_theme_css_applied_v1"

    # Only inject CSS once per session - Streamlit will maintain it across page switches
    if st.session_state.get(theme_applied_key, False):
        return  # CSS already injected, skip expensive operation

    # #region agent log
    import json
    import os
    import time
    try:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".cursor")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "debug.log")
        with open(log_path, "a") as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "theme-apply",
                "hypothesisId": "T1",
                "location": "ui_helpers.py:apply_light_theme_css",
                "message": "Applying light theme CSS",
                "data": {
                    "page": st.session_state.get("_current_page", "unknown"),
                    "theme_applied": False
                },
                "timestamp": int(time.time() * 1000)
            }) + "\n")
    except Exception:
        pass
    # #endregion
    
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

        /* Force sidebar light theme regardless of user theme */
        [data-testid="stSidebar"] {
            background: #f8fafc !important;
            color: #0f172a !important;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            background: #f8fafc !important;
            color: #0f172a !important;
        }
        [data-testid="stSidebar"] a, [data-testid="stSidebar"] span, [data-testid="stSidebar"] button {
            color: #0f172a !important;
        }
        [data-testid="stSidebar"] button {
            background: #e2e8f0 !important;
        }
        
        .stApp {
            background-color: #ffffff !important;
        }
        
        [data-testid="stAppViewContainer"] {
            background-color: #ffffff !important;
        }
        
        /* Header / top bar */
        header[data-testid="stHeader"] {
            background: #f8fafc !important;
            color: #0f172a !important;
            border-bottom: 1px solid #e2e8f0 !important;
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
        .stText, .stMarkdown, .stWrite, p, span, div {
            color: #1e293b !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #0f172a !important;
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

        /* Force all form inputs to light backgrounds */
        input, textarea, select, option {
            background-color: #ffffff !important;
            color: #1e293b !important;
        }
        [data-baseweb="input"] input,
        [data-testid="stNumberInput"] input {
            background-color: #ffffff !important;
            color: #1e293b !important;
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
        [data-testid="stExpander"] summary {
            background: #f8fafc !important;
            border: 1px solid #e2e8f0 !important;
            color: #0f172a !important;
            border-radius: 10px !important;
        }
        [data-testid="stExpander"] svg {
            color: #0f172a !important;
        }
        
        /* ====================================================================
           CHECKBOXES
           ==================================================================== */
        /* Checkbox container - horizontal layout */
        .stCheckbox {
            display: flex !important;
            align-items: center !important;
            gap: 0.5rem !important;
            margin-bottom: 0.75rem !important;
            min-height: 2.5rem !important;
        }
        
        /* Checkbox label text */
        .stCheckbox label {
            color: #1e293b !important;
            font-size: 0.95rem !important;
            line-height: 1.4 !important;
            margin: 0 !important;
        }
        
        /* Checkbox box - unchecked state */
        .stCheckbox [data-baseweb="checkbox"] > div:first-child {
            background-color: #ffffff !important;
            border: 2px solid #cbd5e1 !important;
            border-radius: 4px !important;
            width: 18px !important;
            height: 18px !important;
            min-width: 18px !important;
        }
        
        /* Checkbox box - checked state */
        .stCheckbox [data-baseweb="checkbox"][aria-checked="true"] > div:first-child {
            background-color: #3b82f6 !important;
            border-color: #3b82f6 !important;
        }
        
        /* Remove any black backgrounds */
        .stCheckbox [data-baseweb="checkbox"] * {
            background-color: transparent !important;
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
        
        /* Fix rotated/vertical text in Select All chips */
        [data-baseweb="select"] span {
            writing-mode: horizontal-tb !important;
            transform: none !important;
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
        
        /* Ensure multiselect dropdown text orientation stays normal */
        .stMultiSelect [data-baseweb="select"] span {
            writing-mode: horizontal-tb !important;
            transform: none !important;
        }
        
        /* ====================================================================
           PROGRESS BARS
           ==================================================================== */
        [data-testid="stProgress"] > div {
            background-color: #e2e8f0 !important;
            border-radius: 999px !important;
        }
        
        [data-testid="stProgress"] > div > div {
            background: linear-gradient(90deg, #3b82f6, #2563eb) !important;
            border-radius: 999px !important;
        }
        
        /* ====================================================================
           TOOLTIPS / POPOVERS
           ==================================================================== */
        [data-baseweb="tooltip"] {
            background-color: #0f172a !important;
            color: #e2e8f0 !important;
        }
        
        [data-baseweb="tooltip"] > div {
            color: #e2e8f0 !important;
        }
        
        /* Ensure overlays don't go black */
        [data-baseweb="popover"], [data-baseweb="tooltip"] {
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.15) !important;
        }
        
        /* ====================================================================
           EXPANDERS - stronger light background
           ==================================================================== */
        [data-testid="stExpander"],
        [data-testid="stExpander"] > div,
        [data-testid="stExpander"] [data-testid="element-container"],
        [data-testid="stExpander"] [data-testid="stVerticalBlock"],
        [data-testid="stExpander"] [data-testid="block-container"],
        [data-testid="stExpander"] [data-testid="stMarkdownContainer"] {
            background-color: #ffffff !important;
            color: #1e293b !important;
        }
        .streamlit-expanderHeader,
        .streamlit-expander,
        .streamlit-expanderContent {
            background-color: #ffffff !important;
            color: #1e293b !important;
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
            padding: 0.75rem 1.5rem !important;
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
           CALENDAR - Complete Styling for Light Theme
           ==================================================================== */
        /* Calendar container and all nested elements */
        [data-baseweb="calendar"],
        [data-baseweb="calendar"] *,
        [data-baseweb="calendar"] > div,
        [data-baseweb="calendar"] > div > div {
            background-color: #ffffff !important;
            color: #1e293b !important;
        }
        
        /* Calendar header (month/year) */
        [data-baseweb="calendar"] header,
        [data-baseweb="calendar"] [role="heading"] {
            background-color: #ffffff !important;
            color: #1e293b !important;
        }
        
        /* Calendar day cells - all days */
        [data-baseweb="calendar"] [role="gridcell"],
        [data-baseweb="calendar"] button[role="gridcell"],
        [data-baseweb="calendar"] [data-baseweb="button"][role="gridcell"] {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #e2e8f0 !important;
        }
        
        /* Calendar day cells - hover state */
        [data-baseweb="calendar"] [role="gridcell"]:hover,
        [data-baseweb="calendar"] button[role="gridcell"]:hover {
            background-color: #f1f5f9 !important;
            border-color: #3b82f6 !important;
        }
        
        /* Selected date - should be blue, not black */
        [data-baseweb="calendar"] [role="gridcell"][aria-selected="true"],
        [data-baseweb="calendar"] button[role="gridcell"][aria-selected="true"],
        [data-baseweb="calendar"] [data-baseweb="button"][aria-selected="true"],
        [data-baseweb="calendar"] [aria-selected="true"] {
            background-color: #2563eb !important;
            color: #ffffff !important;
            border-color: #1d4ed8 !important;
            box-shadow: none !important;
        }
        [data-baseweb="calendar"] [role="gridcell"]::after,
        [data-baseweb="calendar"] [role="gridcell"]::before {
            background: none !important;
        }
        
        /* Today's date */
        [data-baseweb="calendar"] [data-today="true"],
        [data-baseweb="calendar"] button[data-today="true"] {
            background-color: #f0f9ff !important;
            border: 2px solid #3b82f6 !important;
            color: #1e293b !important;
        }
        
        /* Calendar navigation buttons */
        [data-baseweb="calendar"] button[aria-label*="Previous"],
        [data-baseweb="calendar"] button[aria-label*="Next"],
        [data-baseweb="calendar"] [data-baseweb="button"] {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
        }
        
        /* Calendar navigation buttons hover */
        [data-baseweb="calendar"] button:hover {
            background-color: #f1f5f9 !important;
            border-color: #3b82f6 !important;
        }
        
        /* Calendar popover/overlay container */
        [data-baseweb="popover"] [data-baseweb="calendar"],
        [role="dialog"] [data-baseweb="calendar"] {
            background-color: #ffffff !important;
        }
        
        /* Remove any black backgrounds from calendar */
        [data-baseweb="calendar"] * {
            background-color: inherit !important;
        }
        
        /* Force white background on calendar root */
        [data-baseweb="calendar"] {
            background: #ffffff !important;
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
           MOBILE RESPONSIVENESS
           ==================================================================== */
        /* Ensure columns don't collapse on desktop (non-form columns) */
        [data-testid="column"]:not(.stForm [data-testid="column"]) {
            min-width: 300px !important;
            flex: 1 1 300px !important;
            align-items: flex-start !important;
        }
        
        /* Prevent horizontal overflow from squeezing columns (non-form) */
        [data-testid="stHorizontalBlock"]:not(.stForm [data-testid="stHorizontalBlock"]) {
            flex-wrap: wrap !important;
            gap: 1rem !important;
        }

        @media (max-width: 768px) {
            /* Reduce padding on mobile */
            .stMarkdown h1 {
                font-size: 2rem !important;
            }
            
            .stMarkdown h2 {
                font-size: 1.5rem !important;
            }
            
            /* Stack columns on mobile (non-form columns) */
            [data-testid="column"]:not(.stForm [data-testid="column"]) {
                min-width: 100% !important;
                width: 100% !important;
            }
            
            /* Reduce margins on mobile */
            .stMarkdown {
                margin-bottom: 1rem !important;
            }
            
            /* Reduce button padding on mobile */
            .stButton > button {
                padding: 0.5rem 1rem !important;
                font-size: 0.9rem !important;
            }
        }
        
        /* ====================================================================
           FORMS - Layout and Alignment
           ==================================================================== */
        /* Form container max-width to prevent over-expansion */
        .stForm, [data-testid="stForm"] {
            max-width: 1200px !important;
            margin: 0 auto !important;
            background-color: #ffffff !important;
            padding: 1.5rem !important;
            border-radius: 8px !important;
            gap: 0.5rem !important;
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
        
        /* Filter alignment */
        [data-testid="column"] .stSelectbox,
        [data-testid="column"] .stMultiSelect {
            width: 100% !important;
        }
        
        /* ====================================================================
           FORM COLUMNS - CRITICAL: Prevent column collapse in forms
           ==================================================================== */
        /* Form columns must maintain minimum width to prevent collapse */
        .stForm [data-testid="column"],
        .stForm [data-testid="stHorizontalBlock"] > [data-testid="column"],
        [data-testid="stForm"] [data-testid="column"] {
            min-width: 350px !important;
            width: 50% !important;
            max-width: 50% !important;
            flex: 0 0 50% !important;
            flex-basis: 50% !important;
            flex-shrink: 0 !important;
            flex-grow: 0 !important;
            box-sizing: border-box !important;
            padding: 0 0.5rem !important;
            writing-mode: horizontal-tb !important;
            text-orientation: mixed !important;
        }
        
        /* Prevent ANY text rotation in form columns */
        .stForm [data-testid="column"] *,
        [data-testid="stForm"] [data-testid="column"] * {
            writing-mode: horizontal-tb !important;
            text-orientation: mixed !important;
            transform: none !important;
            text-align: left !important;
        }
        
        /* Form horizontal block - ensure columns don't wrap unexpectedly */
        .stForm [data-testid="stHorizontalBlock"],
        [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-wrap: nowrap !important;
            gap: 1rem !important;
            width: 100% !important;
            box-sizing: border-box !important;
        }
        
        /* Checkboxes inside form columns - ensure full width */
        .stForm [data-testid="column"] .stCheckbox,
        [data-testid="stForm"] [data-testid="column"] .stCheckbox {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
        }
        
        /* Multiselect inside form columns - ensure full width */
        .stForm [data-testid="column"] .stMultiSelect,
        [data-testid="stForm"] [data-testid="column"] .stMultiSelect {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
        }
        
        /* Media query: Stack columns on smaller screens only */
        @media (max-width: 900px) {
            .stForm [data-testid="column"],
            .stForm [data-testid="stHorizontalBlock"] > [data-testid="column"] {
                min-width: 100% !important;
                width: 100% !important;
                max-width: 100% !important;
                flex: 0 0 100% !important;
                flex-basis: 100% !important;
            }
        }
        
        /* ====================================================================
           TABLES/DATAFRAMES - Comprehensive Light Theme Override
           ==================================================================== */
        /* Main DataFrame container */
        .stDataFrame,
        div[data-testid="stDataFrame"],
        [data-testid="stDataFrame"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 8px !important;
        }
        
        /* All nested DataFrame divs */
        .stDataFrame div,
        div[data-testid="stDataFrame"] > div,
        div[data-testid="stDataFrame"] div,
        [data-testid="stDataFrame"] > div,
        [data-testid="stDataFrame"] div {
            background-color: #ffffff !important;
            color: #1e293b !important;
        }
        
        /* DataFrame tables */
        .stDataFrame table,
        div[data-testid="stDataFrame"] table,
        [data-testid="stDataFrame"] table,
        table {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border-collapse: collapse !important;
        }
        
        /* Table headers */
        .stDataFrame th,
        div[data-testid="stDataFrame"] th,
        [data-testid="stDataFrame"] th,
        table th,
        thead th {
            background-color: #f1f5f9 !important;
            color: #0f172a !important;
            border: 1px solid #e2e8f0 !important;
            font-weight: 600 !important;
            padding: 0.75rem !important;
        }
        
        /* Table cells */
        .stDataFrame td,
        div[data-testid="stDataFrame"] td,
        [data-testid="stDataFrame"] td,
        table td,
        tbody td {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #e2e8f0 !important;
            padding: 0.75rem !important;
        }
        
        /* Table rows */
        .stDataFrame tr,
        div[data-testid="stDataFrame"] tr,
        [data-testid="stDataFrame"] tr,
        table tr,
        tbody tr {
            background-color: #ffffff !important;
        }
        
        /* Alternating row colors for better readability */
        .stDataFrame tbody tr:nth-child(even),
        div[data-testid="stDataFrame"] tbody tr:nth-child(even),
        [data-testid="stDataFrame"] tbody tr:nth-child(even),
        tbody tr:nth-child(even) {
            background-color: #f8fafc !important;
        }
        
        /* Hover state for rows */
        .stDataFrame tbody tr:hover,
        div[data-testid="stDataFrame"] tbody tr:hover,
        [data-testid="stDataFrame"] tbody tr:hover,
        tbody tr:hover {
            background-color: #f1f5f9 !important;
        }
        
        /* Streamlit table wrapper */
        .stTable,
        [data-testid="stTable"] {
            background-color: #ffffff !important;
        }
        
        .stTable table,
        [data-testid="stTable"] table {
            background-color: #ffffff !important;
            color: #1e293b !important;
        }
        
        /* Force all table-related text to be dark */
        .stDataFrame *,
        div[data-testid="stDataFrame"] *,
        [data-testid="stDataFrame"] *,
        .stTable *,
        [data-testid="stTable"] * {
            color: inherit !important;
        }
        
        /* Override any dark background classes Streamlit might add */
        [class*="dark"],
        [class*="black"],
        [style*="background-color: black"],
        [style*="background-color: #000"],
        [style*="background: black"],
        [style*="background: #000"] {
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
        
        /* ====================================================================
           CHART STYLING - Comprehensive Light Theme for Plotly Charts
           ==================================================================== */
        /* Plotly graph containers */
        .plotly-graph-div,
        [data-testid="stPlotlyChart"],
        div[data-testid="stPlotlyChart"] {
            background-color: #ffffff !important;
        }
        
        /* Plotly SVG containers */
        .plotly-graph-div .js-plotly-plot,
        .plotly-graph-div .js-plotly-plot .plot-container,
        .plotly-graph-div .js-plotly-plot .plot-container .svg-container,
        .plotly-graph-div .js-plotly-plot .plot-container .svg-container svg,
        svg.main-svg,
        svg.main-svg > g {
            background-color: #ffffff !important;
        }
        
        /* Plotly background elements */
        .plotly .bg,
        .plotly .plotbg,
        .js-plotly-plot .bg {
            fill: #ffffff !important;
        }
        
        /* Ensure plot background is white */
        .js-plotly-plot .plotly {
            background-color: #ffffff !important;
        }
        
        /* Fix for dark theme patches */
        .element-container div[data-testid="element-container"],
        [data-testid="stPlotlyChart"] div {
            background-color: transparent !important;
        }
        
        /* Navigation and page indicators - Light Theme */
        /* Streamlit sidebar navigation */
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            background-color: #f8fafc !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] span {
            color: #1e293b !important;
        }
        
        /* Active page indicator */
        [data-testid="stSidebarNav"] [aria-current="page"],
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background-color: #e0e7ff !important;
            color: #1e40af !important;
            border-left: 3px solid #3b82f6 !important;
        }
        
        /* Navigation links hover */
        [data-testid="stSidebarNav"] a:hover {
            background-color: #f1f5f9 !important;
            color: #1e40af !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Mark as applied - this persists across page switches in Streamlit
    st.session_state[theme_applied_key] = True


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
    
    # Avoid nested columns when inside_form=True to prevent layout collapse
    if inside_form:
        # Stack vertically for forms to avoid nested column issues
        all_selected = len(current_selection) == len(options) and len(options) > 0
        
        # Add container with width constraint for form mode
        st.markdown('<div style="width: 100%; max-width: 100%; box-sizing: border-box;">', unsafe_allow_html=True)
        
        toggle = st.checkbox(
            "📋 Select All" if not all_selected else "✂️ Clear All",
            value=all_selected,
            key=f"{state_key}_select_all_toggle",
            help="Select all options" if not all_selected else "Clear all selections"
        )
        
        # If user toggles, update state
        if toggle != all_selected:
            if toggle:
                st.session_state[state_key] = options.copy()
            else:
                st.session_state[state_key] = []
        
        # Multiselect below toggle (no nested columns) - full width
        current_default = st.session_state[state_key]
        valid_default = [opt for opt in current_default if opt in options] if current_default else []
        
        # If no valid default and default parameter was provided, use it if valid
        if not valid_default and default:
            valid_default = [opt for opt in default if opt in options]
        
        # Wrap multiselect in container to ensure full width
        st.markdown('<div style="width: 100%; max-width: 100%;">', unsafe_allow_html=True)
        selected = st.multiselect(
            label,
            options=options,
            default=valid_default,
            key=key or f"ms_{label.replace(' ', '_')}",
            help=help,
            placeholder=placeholder if placeholder else "Choose options..."
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Update state
        st.session_state[state_key] = selected
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Use columns only when NOT in form (outside forms, nested columns are fine)
        select_all_col, multiselect_col = st.columns([1, 4])
        
        with select_all_col:
            all_selected = len(current_selection) == len(options) and len(options) > 0
            
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
            # Ensure default values are valid (subset of options)
            current_default = st.session_state[state_key]
            valid_default = [opt for opt in current_default if opt in options] if current_default else []
            
            # If no valid default and default parameter was provided, use it if valid
            if not valid_default and default:
                valid_default = [opt for opt in default if opt in options]
            
            selected = st.multiselect(
                label,
                options=options,
                default=valid_default,
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


# Override theme helper with dark-compatible CSS to ensure text visibility
def apply_light_theme_css():
    """Apply consistent theme CSS that works in both light and dark modes."""
    st.markdown("""
    <style>
    /* ============================================
       GLOBAL TEXT VISIBILITY FIXES
       ============================================ */
    
    .main .block-container,
    .main .block-container * { color: inherit; }
    
    .main h1, .main h2, .main h3, 
    .main .stMarkdown h1, .main .stMarkdown h2, .main .stMarkdown h3 {
        color: #ffffff !important;
    }
    .main p, .main li, .main span, .main label {
        color: #e0e0e0 !important;
    }
    
    /* What To Do Next / alerts */
    .stAlert, [data-testid="stAlert"],
    .element-container div[data-testid="stAlert"] {
        background-color: #2d2d3d !important;
        border: 1px solid #404050 !important;
    }
    .stAlert p, .stAlert li, .stAlert span,
    [data-testid="stAlert"] p, [data-testid="stAlert"] li, [data-testid="stAlert"] span {
        color: #e0e0e0 !important;
    }
    .stAlert[data-baseweb="notification"] { background-color: #1e3a5f !important; }
    div[data-baseweb="notification"][kind="positive"] { background-color: #1e4d3d !important; }
    div[data-baseweb="notification"][kind="warning"] { background-color: #4d3d1e !important; }
    
    /* Expanders */
    .streamlit-expanderHeader,
    [data-testid="stExpander"] summary,
    button[kind="secondary"] {
        color: #ffffff !important;
        background-color: #2d2d3d !important;
    }
    .streamlit-expanderContent,
    [data-testid="stExpander"] > div {
        background-color: #1e1e2e !important;
        color: #e0e0e0 !important;
    }
    
    /* Chat */
    .stChatMessage,
    [data-testid="stChatMessage"],
    [data-testid="stChatMessageContent"] {
        background-color: #2d2d3d !important;
        border: 1px solid #404050 !important;
    }
    .stChatMessage p, .stChatMessage span, .stChatMessage li,
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] span, [data-testid="stChatMessage"] li {
        color: #e0e0e0 !important;
    }
    .stChatInput, [data-testid="stChatInput"] { background-color: #2d2d3d !important; }
    .stChatInput input, .stChatInput textarea {
        color: #ffffff !important; background-color: #1e1e2e !important;
    }
    
    /* Tabs/results */
    .stTabs [data-baseweb="tab-panel"],
    [data-testid="stTabs"] > div { background-color: transparent !important; }
    .stTabs [data-baseweb="tab-panel"] > div,
    .stTabs [data-baseweb="tab-panel"] p,
    .stTabs [data-baseweb="tab-panel"] li,
    .stTabs [data-baseweb="tab-panel"] span { color: #e0e0e0 !important; }
    div[style*="background-color: white"],
    div[style*="background-color: #fff"],
    div[style*="background: white"],
    div[style*="background: #fff"] { background-color: #2d2d3d !important; background: #2d2d3d !important; }
    
    /* Form elements */
    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {
        background-color: #1e1e2e !important;
        color: #ffffff !important;
        border: 1px solid #404050 !important;
    }
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    [data-testid="stSelectbox"] > div > div {
        background-color: #1e1e2e !important;
        color: #ffffff !important;
    }
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [data-baseweb="select"] [role="listbox"] { background-color: #2d2d3d !important; }
    [data-baseweb="menu"] li, [role="option"] { color: #e0e0e0 !important; }
    
    /* Sidebar */
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div { background-color: #1a1a2e !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] li, [data-testid="stSidebar"] .stMarkdown { color: #e0e0e0 !important; }
    
    /* Metrics */
    .stMetric, [data-testid="stMetric"], [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: #ffffff !important;
    }
    .stMetric label { color: #b0b0b0 !important; }
    
    /* Tables */
    .stDataFrame, [data-testid="stDataFrame"], .stTable { background-color: #1e1e2e !important; }
    .stDataFrame th, .stDataFrame td, .stTable th, .stTable td {
        color: #e0e0e0 !important; border-color: #404050 !important;
    }
    
    /* Buttons */
    .stButton button { color: #ffffff !important; }
    .stButton button[kind="primary"] { background-color: #ff4b4b !important; }
    .stButton button[kind="secondary"] { background-color: #2d2d3d !important; border: 1px solid #404050 !important; }
    
    /* Code blocks */
    .stCodeBlock, code, pre { background-color: #1e1e2e !important; color: #e0e0e0 !important; }
    
    /* Markdown containers */
    .stMarkdown div[data-testid="stMarkdownContainer"] { color: #e0e0e0 !important; }
    blockquote {
        border-left: 4px solid #ff4b4b !important;
        background-color: #2d2d3d !important;
        color: #e0e0e0 !important;
        padding: 10px 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)


def force_dark_theme():
    """Nuclear option - force dark theme on everything"""
    st.markdown("""
    <style>
    /* Override EVERYTHING */
    * {
        color: #e0e0e0 !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    
    /* Except buttons which need specific colors */
    button, .stButton button {
        color: #ffffff !important;
    }
    
    /* And inputs which need dark text on light bg sometimes */
    input, textarea, select {
        color: #ffffff !important;
        background-color: #1e1e2e !important;
    }
    
    /* Remove all white backgrounds */
    div, section, article, aside, header, footer, main {
        background-color: transparent !important;
    }
    
    /* Set main container background */
    .main .block-container {
        background-color: #0e1117 !important;
    }
    </style>
    """, unsafe_allow_html=True)
# ============================================================================
# STANDARDIZED UI COMPONENTS
# ============================================================================

def render_page_header(title: str, icon: str = "", description: str = "", margin_bottom: str = "2rem") -> None:
    """
    Render standardized page header with consistent styling.
    
    Args:
        title: Page title
        icon: Optional icon emoji
        description: Optional description text
        margin_bottom: Bottom margin (default: 2rem)
    """
    icon_text = f"{icon} " if icon else ""
    st.markdown(f"""
    <div style='margin-bottom: {margin_bottom};'>
        <h1 style='font-size: 2.5rem; font-weight: 700; color: #0f172a !important; margin-bottom: 0.5rem;'>
            {icon_text}{title}
        </h1>
        {f"<p style='font-size: 1.1rem; color: #64748b; margin: 0;'>{description}</p>" if description else ""}
    </div>
    """, unsafe_allow_html=True)


def render_section_header(title: str, icon: str = "", level: int = 2, margin_top: str = "2.5rem", margin_bottom: str = "1.5rem") -> None:
    """
    Render standardized section header with consistent spacing and icon size.
    
    Args:
        title: Section title (will be title-cased)
        icon: Optional icon emoji (will be sized to 24px)
        level: Header level (2 for h2, 3 for h3, etc.)
        margin_top: Top margin (default: 2.5rem)
        margin_bottom: Bottom margin (default: 1.5rem)
    """
    # Ensure title case
    title = title.title() if title else ""
    
    # Icon styling with 24px size
    if icon:
        icon_text = f"<span style='font-size: 24px; display: inline-block; vertical-align: middle; margin-right: 0.5rem;'>{icon}</span>"
    else:
        icon_text = ""
    
    tag = f"h{level}"
    st.markdown(f"""
    <{tag} style='font-size: {"2rem" if level == 2 else "1.5rem"}; font-weight: 700; color: #1e40af; margin-top: {margin_top}; margin-bottom: {margin_bottom}; border-left: 4px solid #3b82f6; padding-left: 1rem;'>
        {icon_text}{title}
    </{tag}>
    """, unsafe_allow_html=True)


def render_card(header: str = "", body: Any = None, icon: str = "", collapsible: bool = False, default_expanded: bool = True) -> None:
    """
    Render standardized card component.
    
    Args:
        header: Card header text
        icon: Optional icon emoji
        body: Card body content (function or content)
        collapsible: Whether card is collapsible
        default_expanded: Default expanded state (if collapsible)
    """
    icon_text = f"{icon} " if icon else ""
    
    if collapsible:
        with st.expander(f"{icon_text}{header}", expanded=default_expanded):
            if callable(body):
                body()
            else:
                st.markdown(body if body else "")
    else:
        st.markdown(f"""
        <div style='background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
            {f"<h3 style='font-size: 1.25rem; font-weight: 600; color: #0f172a; margin-top: 0; margin-bottom: 1rem;'>{icon_text}{header}</h3>" if header else ""}
            <div style='color: #1e293b;'>
        """, unsafe_allow_html=True)
        
        if callable(body):
            body()
        else:
            st.markdown(body if body else "")
        
        st.markdown("</div></div>", unsafe_allow_html=True)


def render_empty_state(message: str, icon: str = "📭", submessage: str = "") -> None:
    """
    Render standardized empty state with consistent styling.
    
    Args:
        message: Main message
        icon: Icon emoji (will be sized to 24px)
        submessage: Optional submessage
    """
    st.markdown(f"""
    <div style='text-align: center; padding: 3rem 2rem; background-color: #f8fafc; border-radius: 8px; border: 1px dashed #cbd5e1; margin: 2.5rem 0 1.5rem 0;'>
        <div style='font-size: 24px; margin-bottom: 1rem;'>{icon}</div>
        <p style='font-size: 1.25rem; color: #64748b; margin: 0; font-weight: 600;'>{message}</p>
        {f"<p style='font-size: 1rem; color: #94a3b8; margin-top: 0.5rem;'>{submessage}</p>" if submessage else ""}
    </div>
    """, unsafe_allow_html=True)


def render_plotly_chart(fig, title: str = "", height: int = 400, width: str = "stretch", show_title: bool = True, key: str = None) -> None:
    """
    Render Plotly chart with consistent styling (400px height, title case, standard margins).
    
    Args:
        fig: Plotly figure
        title: Chart title (will be title-cased, shown above chart if show_title=True)
        height: Chart height in pixels (default: 400px)
        width: Chart width ('stretch' or 'content')
        show_title: Show title above chart (removes title from chart itself)
    """
    # Ensure title case
    title_cased = title.title() if title else ""
    
    # Remove title from chart if showing above
    if show_title and title_cased:
        st.markdown(f"<h4 style='font-size: 1.1rem; font-weight: 600; color: #475569; margin: 1rem 0 0.5rem 0;'>{title_cased}</h4>", unsafe_allow_html=True)
        # Remove title from chart itself
        if hasattr(fig, 'layout') and hasattr(fig.layout, 'title'):
            fig.update_layout(title=None)
    
    # Standard layout with consistent margins and legend placement
    # Force light theme with comprehensive color overrides
    fig.update_layout(
        height=height,
        template="plotly_white",  # Use plotly_white template
        font=dict(family="Arial, sans-serif", size=12, color="#1e293b"),
        plot_bgcolor="white",  # Chart background
        paper_bgcolor="white",  # Paper/container background
        margin=dict(l=60, r=60, t=40, b=60),  # Consistent margins
        # Ensure light theme colors
        xaxis=dict(
            gridcolor="#e2e8f0",
            linecolor="#cbd5e1",
            zerolinecolor="#cbd5e1",
            title_font=dict(color="#1e293b")
        ),
        yaxis=dict(
            gridcolor="#e2e8f0",
            linecolor="#cbd5e1",
            zerolinecolor="#cbd5e1",
            title_font=dict(color="#1e293b")
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="#e2e8f0",
            borderwidth=1,
            font=dict(color="#1e293b")
        ) if len(fig.data) > 1 else None  # Horizontal legend if multiple series
    )
    
    # Update traces to ensure light theme colors
    for trace in fig.data:
        if hasattr(trace, 'marker'):
            if hasattr(trace.marker, 'line') and trace.marker.line.color == 'black':
                trace.marker.line.color = "#1e293b"
        if hasattr(trace, 'line') and trace.line.color == 'black':
            trace.line.color = "#1e293b"
    
    st.plotly_chart(fig, width=width, key=key)


def render_error_message(error_type: str, message: str, details: str = "", show_details: bool = False) -> None:
    """
    Render standardized error message.
    
    Args:
        error_type: Error type (e.g., "ValidationError", "APIError")
        message: User-friendly message
        details: Technical details (optional)
        show_details: Whether to show details in expander
    """
    st.error(f"**{error_type}**: {message}")
    
    if details and show_details:
        with st.expander("Technical Details"):
            st.code(details, language="text")


def render_info_box(message: str, icon: str = "ℹ️", color: str = "#3b82f6") -> None:
    """
    Render standardized info box.
    
    Args:
        message: Info message
        icon: Icon emoji
        color: Border color (hex)
    """
    st.markdown(f"""
    <div style='background-color: #f0f9ff; padding: 1rem; border-radius: 8px; margin: 1rem 0; border-left: 4px solid {color};'>
        <p style='font-size: 1rem; color: #1e40af; margin: 0;'>
            <strong>{icon}</strong> {message}
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_divider(margin_top: str = "1rem", margin_bottom: str = "1rem") -> None:
    """
    Render standardized divider with consistent spacing.
    
    Args:
        margin_top: Top margin (default: 1rem)
        margin_bottom: Bottom margin (default: 1rem)
    """
    st.markdown(f"<div style='margin-top: {margin_top}; margin-bottom: {margin_bottom}; border-top: 1px solid #e2e8f0;'></div>", unsafe_allow_html=True)


def should_hide_section(data: Any, empty_message: str = "No data available") -> bool:
    """
    Check if section should be hidden (empty/None).
    
    Args:
        data: Data to check
        empty_message: Message to show if empty
        
    Returns:
        True if should hide, False otherwise
    """
    if data is None:
        return True
    if isinstance(data, (list, dict, str)):
        if not data or (isinstance(data, str) and not data.strip()):
            return True
    return False


def render_section_if_not_empty(title: str, data: Any, render_func: callable, icon: str = "", empty_message: str = "No data available") -> None:
    """
    Render section only if data is not empty.
    
    Args:
        title: Section title
        data: Data to check
        render_func: Function to render content
        icon: Optional icon
        empty_message: Message if empty
    """
    if should_hide_section(data):
        st.markdown(f"""
        <div style='opacity: 0.5; padding: 1rem; background-color: #f8fafc; border-radius: 8px; margin: 1rem 0;'>
            <p style='color: #94a3b8; margin: 0; font-style: italic;'>{icon} {title}: {empty_message}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        render_section_header(title, icon=icon)
        render_func(data)
