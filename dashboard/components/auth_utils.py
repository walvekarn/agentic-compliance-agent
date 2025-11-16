"""
Authentication Utilities
========================
Centralized authentication for all dashboard pages using backend JWT.
"""

import streamlit as st
from typing import Optional, Dict
import os
from . import auth_client


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Initialize a simple, stable session auth flag if missing
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False


def _set_tokens(access_token: str, refresh_token: str, username: Optional[str] = None):
    st.session_state["token"] = access_token
    st.session_state["refresh"] = refresh_token
    st.session_state["username"] = username or st.session_state.get("username")
    st.session_state["auth"] = True
    st.session_state["authenticated"] = True


def _clear_tokens():
    for k in ["token", "refresh", "username", "auth"]:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state["authenticated"] = False


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated"))


def show_login_page():
    """
    Display the login form and handle authentication against backend /auth/login.
    
    Returns True if user is authenticated, False otherwise.
    """
    if is_authenticated():
        return True
    
    st.title("🔐 Sign in to Compliance Assistant")
    st.markdown("""
    <p style='font-size: 1.1rem; text-align: center; color: #475569; margin-bottom: 1.25rem;'>
    Enter your credentials to continue
    </p>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="acme.user")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("🔓 Sign In", use_container_width=True, type="primary")
            
            if submit:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    try:
                        ok, access, refresh, err = auth_client.login(username, password, timeout=10)
                        if ok and access and refresh:
                            _set_tokens(access, refresh, username=username)
                            st.session_state["authenticated"] = True
                            st.success("✅ Login successful! Redirecting...")
                            st.rerun()
                        else:
                            st.error(err or "Login failed. Please try again.")
                    except Exception as e:
                        st.error(f"Cannot connect to backend. {e}")
    
    return False


def require_auth():
    """
    Require authentication to access a page.
    If not authenticated, render login page once and stop.
    """
    if is_authenticated():
        return
    if not show_login_page():
        st.stop()


def get_auth_headers() -> Dict[str, str]:
    """
    Return Authorization header using current access token, if available.
    """
    access = st.session_state.get("token")
    return {"Authorization": f"Bearer {access}"} if access else {}


def refresh_tokens_if_needed() -> bool:
    """
    Refresh access token using stored refresh token.
    Returns True on success, False otherwise.
    """
    refresh = st.session_state.get("refresh")
    if not refresh:
        return False
    try:
        ok, new_access, new_refresh, err = auth_client.refresh(refresh, timeout=10)
        if ok and new_access and new_refresh:
            _set_tokens(new_access, new_refresh)
            return True
        _clear_tokens()
        return False
    except Exception:
        _clear_tokens()
        return False


def logout():
    """
    Log out the current user by clearing session tokens and state.
    """
    _clear_tokens()
    st.switch_page("Home.py")
