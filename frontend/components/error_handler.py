"""
Error Handler Component
=======================
Provides error boundary functionality for Streamlit pages.
Since Streamlit doesn't have React-style error boundaries,
we use try/except blocks and this helper to display errors gracefully.
"""

import streamlit as st
import traceback
from typing import Callable, Any, Optional


def handle_errors(func: Callable) -> Callable:
    """
    Decorator to wrap Streamlit page functions with error handling.
    
    Usage:
        @handle_errors
        def main():
            # Your page code here
            pass
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error("⚠️ An unexpected error occurred")
            with st.expander("Error Details", expanded=False):
                st.code(traceback.format_exc())
            st.stop()
    return wrapper


def display_error(error: Exception, context: Optional[str] = None):
    """
    Display an error message in Streamlit with optional context.
    
    Args:
        error: The exception that occurred
        context: Optional context about where the error occurred
    """
    error_msg = str(error)
    if context:
        st.error(f"⚠️ Error in {context}: {error_msg}")
    else:
        st.error(f"⚠️ Error: {error_msg}")
    
    # Log to console
    print(f"❌ Error{' in ' + context if context else ''}: {error_msg}", flush=True)
    print(traceback.format_exc(), flush=True)


def safe_execute(func: Callable, context: Optional[str] = None, default: Any = None) -> Any:
    """
    Safely execute a function and return a default value on error.
    
    Args:
        func: Function to execute
        context: Optional context for error messages
        default: Value to return on error
        
    Returns:
        Function result or default value
    """
    try:
        return func()
    except Exception as e:
        display_error(e, context)
        return default

