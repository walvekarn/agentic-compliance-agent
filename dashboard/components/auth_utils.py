"""
Authentication Utilities
========================
Centralized authentication for all dashboard pages.
"""

import streamlit as st


def show_login_page():
    """
    Display the login form and handle authentication.
    
    This should be called from Home.py only.
    Returns True if user is authenticated, False otherwise.
    """
    # Initialize auth state
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
    
    # If already authenticated, return True
    if st.session_state["auth"]:
        return True
    
    # Show login screen
    st.title("🔐 Compliance Assistant Login")
    st.markdown("""
    <p style='font-size: 1.3rem; text-align: center; color: #475569; margin-bottom: 2rem;'>
    Please enter the password to access the dashboard
    </p>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("🔓 Login", use_container_width=True, type="primary")
            
            if submit:
                # Check password against secrets
                try:
                    if password == st.secrets["login_password"]:
                        st.session_state["auth"] = True
                        st.success("✅ Login successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error("❌ Incorrect password. Please try again.")
                except KeyError:
                    # If secrets not configured, use default demo password
                    if password == "demo123":
                        st.session_state["auth"] = True
                        st.success("✅ Login successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error("❌ Incorrect password. Please try again.")
        
        st.markdown("---")
        st.info("💡 **Demo Password**: demo123")
        st.caption("⚠️ This is a demo authentication system. Not suitable for production use.")
    
    return False


def require_auth():
    """
    Require authentication to access a page.
    
    Checks if the user is authenticated via st.session_state["auth"].
    If not authenticated, displays a warning and stops execution.
    
    Usage:
        At the top of each page (AFTER query param navigation), call:
        require_auth()
    """
    # Initialize auth state if not present
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
    
    if not st.session_state["auth"]:
        st.warning("⚠️ Please login first.")
        st.info("👉 Return to the Home page to login.")
        
        # Provide a button to go back to home using proper Streamlit navigation
        if st.button("🏠 Go to Login Page", type="primary"):
            st.switch_page("Home.py")
        
        st.stop()


def logout():
    """
    Log out the current user.
    
    Clears ALL session state to prevent data leaks between users.
    """
    # Clear ALL session state keys to prevent data leakage
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Reinitialize auth to False
    st.session_state["auth"] = False
    st.switch_page("Home.py")
