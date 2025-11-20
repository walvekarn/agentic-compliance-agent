"""
Session State Manager
====================
Centralized session state management with clear lifecycle.
"""

import streamlit as st
from typing import Optional, Dict, Any
from datetime import datetime
from .constants import AppState


class SessionManager:
    """Manage Streamlit session state with clear lifecycle"""
    
    @staticmethod
    def init():
        """Initialize ALL session state in ONE place"""
        defaults = {
            # App state
            'app_state': AppState.FORM,
            
            # Form data
            'form_data': {},
            
            # Analysis results
            'analysis_result': None,
            'analysis_timestamp': None,
            
            # Feedback
            'feedback_submitted': False,
            'feedback_data': None,
            
            # Error handling
            'error_message': None,
            'error_details': None,
            
            # Page flags
            'page_initialized': False,
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
        
        # Mark as initialized
        if not st.session_state.page_initialized:
            SessionManager.clear_analysis()
            st.session_state.page_initialized = True
    
    @staticmethod
    def reset_form():
        """Reset form to initial state"""
        st.session_state.app_state = AppState.FORM
        st.session_state.form_data = {}
        SessionManager.clear_analysis()
    
    @staticmethod
    def clear_analysis():
        """Clear analysis-specific data"""
        st.session_state.analysis_result = None
        st.session_state.analysis_timestamp = None
        st.session_state.feedback_submitted = False
        st.session_state.feedback_data = None
        st.session_state.error_message = None
        st.session_state.error_details = None
    
    @staticmethod
    def save_form_data(data: Dict[str, Any]):
        """Save form data to session"""
        st.session_state.form_data = data.copy()
    
    @staticmethod
    def get_form_data() -> Dict[str, Any]:
        """Get saved form data"""
        return st.session_state.form_data.copy()
    
    @staticmethod
    def save_analysis(result: Dict[str, Any]):
        """Save analysis result"""
        st.session_state.analysis_result = result
        st.session_state.analysis_timestamp = datetime.now()
        st.session_state.app_state = AppState.RESULTS
    
    @staticmethod
    def get_analysis() -> Optional[Dict[str, Any]]:
        """Get saved analysis result"""
        return st.session_state.analysis_result
    
    @staticmethod
    def set_loading():
        """Set app to loading state"""
        st.session_state.app_state = AppState.LOADING
    
    @staticmethod
    def set_error(message: str, details: Optional[str] = None):
        """Set error state"""
        st.session_state.app_state = AppState.ERROR
        st.session_state.error_message = message
        st.session_state.error_details = details
    
    @staticmethod
    def is_loading() -> bool:
        """Check if app is in loading state"""
        return st.session_state.app_state == AppState.LOADING
    
    @staticmethod
    def has_results() -> bool:
        """Check if we have analysis results"""
        return (st.session_state.app_state == AppState.RESULTS and 
                st.session_state.analysis_result is not None)
    
    @staticmethod
    def has_error() -> bool:
        """Check if we have an error"""
        return st.session_state.app_state == AppState.ERROR
    
    @staticmethod
    def save_feedback(feedback: Dict[str, Any]):
        """Save feedback data"""
        st.session_state.feedback_submitted = True
        st.session_state.feedback_data = feedback
    
    @staticmethod
    def get_feedback() -> Optional[Dict[str, Any]]:
        """Get saved feedback"""
        return st.session_state.feedback_data if st.session_state.feedback_submitted else None
    
    @staticmethod
    def get_analysis_age_minutes() -> Optional[int]:
        """Get age of analysis in minutes"""
        if st.session_state.analysis_timestamp:
            delta = datetime.now() - st.session_state.analysis_timestamp
            return delta.seconds // 60
        return None
    
    @staticmethod
    def save_draft(form_data: Dict[str, Any], page: str = "analyze_task"):
        """Save form data as draft."""
        draft_key = f"draft_{page}"
        st.session_state[draft_key] = {
            "data": form_data,
            "timestamp": datetime.now().isoformat(),
            "page": page
        }
    
    @staticmethod
    def get_draft(page: str = "analyze_task") -> Optional[Dict[str, Any]]:
        """Get saved draft for a page."""
        draft_key = f"draft_{page}"
        if draft_key in st.session_state:
            return st.session_state[draft_key].get("data")
        return None
    
    @staticmethod
    def has_draft(page: str = "analyze_task") -> bool:
        """Check if draft exists for a page."""
        draft_key = f"draft_{page}"
        return draft_key in st.session_state and st.session_state[draft_key] is not None
    
    @staticmethod
    def clear_draft(page: str = "analyze_task"):
        """Clear saved draft."""
        draft_key = f"draft_{page}"
        if draft_key in st.session_state:
            del st.session_state[draft_key]

