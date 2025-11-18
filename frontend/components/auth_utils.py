"""
Authentication Utilities
========================
Centralized authentication for all dashboard pages using backend JWT.
Secure global session state system that persists across navigation.
"""

import streamlit as st
from typing import Optional, Dict
import os
from . import auth_client

# Load environment variables with python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not required, use os.getenv only

# Get API base URL with fallback to localhost:8000
API_BASE_URL = os.getenv("BACKEND_URL") or os.getenv("API_BASE_URL") or "http://localhost:8000"

# Initialize session state flags if missing
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Prevent infinite redirect loops
if "auth_redirect_in_progress" not in st.session_state:
    st.session_state["auth_redirect_in_progress"] = False


def _set_tokens(access_token: str, refresh_token: str, username: Optional[str] = None):
    """Set authentication tokens and update session state."""
    st.session_state["token"] = access_token
    st.session_state["refresh"] = refresh_token
    st.session_state["username"] = username or st.session_state.get("username")
    st.session_state["auth"] = True
    st.session_state["authenticated"] = True
    # Clear redirect flag on successful auth
    st.session_state["auth_redirect_in_progress"] = False


def _clear_tokens():
    """Clear all authentication tokens and reset session state."""
    for k in ["token", "refresh", "username", "auth"]:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state["authenticated"] = False
    st.session_state["auth_redirect_in_progress"] = False


def is_authenticated() -> bool:
    """
    Check if user is authenticated by verifying token exists.
    
    Returns:
        True if authenticated (token exists), False otherwise
    """
    # Verify both flag and token exist
    has_flag = bool(st.session_state.get("authenticated", False))
    has_token = bool(st.session_state.get("token"))
    return has_flag and has_token


def check_auth():
    """
    Unified auth guard for all pages.
    - If authenticated: return immediately (no-op)
    - If not: show login message and stop execution (don't redirect)
    - Prevents infinite loops with redirect flag
    """
    # If already authenticated, allow access
    if is_authenticated():
        return
    
    # Prevent infinite redirect loops
    if st.session_state.get("auth_redirect_in_progress", False):
        st.warning("⚠️ Please sign in to continue.")
        st.stop()
        return
    
    # Set redirect flag to prevent loops
    st.session_state["auth_redirect_in_progress"] = True
    
    # Show login message and stop (don't redirect)
    st.warning("⚠️ Please sign in to continue.")
    st.info("💡 Use the login form above to access this page.")
    st.stop()

def show_login_page():
    """
    Display the login form and handle authentication against backend /auth/login.
    
    Returns True if user is authenticated, False otherwise.
    """
    # Clear redirect flag when showing login page
    st.session_state["auth_redirect_in_progress"] = False
    
    if is_authenticated():
        return True
    
    st.title("🔐 Agentic Compliance Assistant – Demo Login")
    st.markdown("""
    <p style='font-size: 1.1rem; text-align: center; color: #475569; margin-bottom: 1.25rem;'>
    This is a demo environment. No real data is stored.
    </p>
    """, unsafe_allow_html=True)
    
    # Backend health check BEFORE login form
    from .api_client import APIClient
    api = APIClient()
    health = api.health_check()
    if not health.success:
        st.error("⚠️ **Backend is not available**")
        st.info(f"""
        **Connection Error:** {health.error or "Backend offline"}
        
        **Troubleshooting:**
        1. Ensure the backend is running: `make backend` or `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
        2. Check backend URL: {API_BASE_URL}
        3. Verify backend health: http://localhost:8000/health
        4. Check firewall settings
        
        **Quick Start:**
        ```bash
        make start  # Starts both backend and dashboard
        ```
        """)
        return False
    
    # Session expiry notice (one-time)
    if st.session_state.get("session_expired"):
        st.warning("Your session expired. Please log in again.")
        del st.session_state["session_expired"]
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="demo")
            password = st.text_input("Password", type="password", placeholder="demo123")
            submit = st.form_submit_button("🔓 Sign In", use_container_width=True, type="primary")
            
            if submit:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    with st.spinner("Signing in..."):
                        try:
                            ok, access, refresh, err = auth_client.login(username, password, timeout=10)
                            if ok and access and refresh:
                                _set_tokens(access, refresh, username=username)
                                st.session_state["authenticated"] = True
                                st.success("✅ Login successful! Redirecting...")
                                # Clear redirect flag on successful login
                                st.session_state["auth_redirect_in_progress"] = False
                                # Ensure a hard rerun to refresh sidebar/pages
                                try:
                                    st.experimental_rerun()
                                except Exception:
                                    st.rerun()
                            else:
                                # Surface backend status or error to aid diagnosis (minimal, targeted)
                                detail = err or "Login failed"
                                st.error(f"Sign-in failed: {detail}. If this persists, verify BACKEND_URL/API_BASE_URL and that the backend is running.")
                        except Exception as e:
                            st.error(f"Cannot connect to backend. {e}")
    
    return False


def require_auth():
    """
    Require authentication to access a page.
    Delegates to check_auth() so all pages use the same guard.
    
    This function should be called at the top of every page (except Home.py)
    to ensure the user is authenticated before accessing the page.
    
    Example:
        from components.auth_utils import require_auth
        
        require_auth()  # Must be called before any other page content
    """
    check_auth()


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
    Ensures clean logout and redirects to Home page.
    """
    _clear_tokens()
    # Clear redirect flag
    st.session_state["auth_redirect_in_progress"] = False
    try:
        st.switch_page("Home.py")
    except Exception:
        st.rerun()


def show_logout_button(container=None):
    """
    Display a logout button in the specified container or sidebar.
    
    Args:
        container: Optional Streamlit container (e.g., st.sidebar, st.columns()[0]).
                   If None, displays in the main area.
    
    Example:
        # In sidebar
        with st.sidebar:
            show_logout_button()
        
        # In header
        col1, col2 = st.columns([5, 1])
        with col2:
            show_logout_button()
    """
    target = container if container is not None else st
    
    if is_authenticated():
        username = st.session_state.get("username", "User")
        target.markdown("---")
        target.markdown(f"**Logged in as:** {username}")
        if target.button("🚪 Logout", use_container_width=True, key="logout_btn"):
            logout()
