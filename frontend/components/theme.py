"""Centralized theme helpers for Streamlit pages."""

import streamlit as st


def apply_home_theme_css() -> None:
    """Apply Home page styling - extends base light theme"""
    from .ui_helpers import apply_light_theme_css
    
    # Apply base light theme first
    apply_light_theme_css()
    
    # Add Home-page-specific CSS overrides
    st.markdown(
        """
        <style>
            /* Home page layout - extends base .main */
            .main {
                padding: 1rem 2rem 2rem 2rem !important;
                max-width: 1400px !important;
                margin: 0 auto !important;
            }
            
            /* Home page typography - larger, centered headings */
            h1 {
                font-size: 4rem !important;
                font-weight: 800 !important;
                text-align: center !important;
                margin-bottom: 0.75rem !important;
                line-height: 1.1 !important;
            }
            
            h2 {
                font-size: 2.5rem !important;
                font-weight: 700 !important;
                color: #1e40af !important;
                margin-top: 2.5rem !important;
                margin-bottom: 1.5rem !important;
                text-align: center !important;
            }
            
            h3 {
                font-size: 2rem !important;
                font-weight: 700 !important;
                color: #2563eb !important;
                margin-top: 1.5rem !important;
                margin-bottom: 1rem !important;
            }
            
            /* Home page text - larger font sizes */
            p, li, div {
                font-size: 1.25rem !important;
                line-height: 1.7 !important;
            }
            
            /* Home page feature cards - unique to Home */
            .feature-card {
                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                padding: 2.5rem;
                border-radius: 20px;
                margin: 1.5rem 0;
                box-shadow: 0 8px 16px rgba(0,0,0,0.1);
                border: 3px solid #7dd3fc;
                transition: all 0.3s;
                min-height: 280px;
            }
            
            .feature-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 12px 24px rgba(0,0,0,0.15);
                border-color: #3b82f6;
            }
            
            .feature-card h3 {
                font-size: 2.25rem !important;
                font-weight: 800 !important;
                margin-bottom: 1.25rem !important;
                color: #0f172a !important;
                text-align: center !important;
            }
            
            .feature-card p {
                font-size: 1.35rem !important;
                color: #1e40af !important;
                margin-bottom: 1.25rem !important;
                font-weight: 500;
                text-align: center !important;
            }
            
            .feature-card ul {
                font-size: 1.2rem !important;
                color: #1e293b !important;
                list-style-position: inside;
            }
            
            .feature-card ul li {
                font-size: 1.2rem !important;
                padding: 0.5rem 0;
                color: #1e293b !important;
            }
            
            /* Home page button overrides - larger, more prominent */
            .stButton button {
                font-size: 1.4rem !important;
                font-weight: 700 !important;
                padding: 1.25rem 2.5rem !important;
                border-radius: 15px !important;
                transition: all 0.3s !important;
                text-transform: none !important;
                box-shadow: 0 6px 12px rgba(59, 130, 246, 0.3) !important;
            }
            
            .stButton button:hover {
                transform: translateY(-3px) !important;
                box-shadow: 0 10px 20px rgba(59, 130, 246, 0.4) !important;
            }
            
            /* Home page alert overrides - larger */
            .stAlert {
                font-size: 1.3rem !important;
                padding: 1.5rem !important;
                border-radius: 15px !important;
                margin: 1.5rem 0 !important;
            }
            
            /* Home page metric overrides - larger */
            .stMetric {
                background-color: #f8fafc !important;
                padding: 2rem !important;
                border-radius: 15px !important;
                border: 3px solid #cbd5e1 !important;
            }
            
            .stMetric label {
                font-size: 1.3rem !important;
                font-weight: 600 !important;
                color: #0f172a !important;
            }
            
            .stMetric [data-testid="stMetricValue"] {
                font-size: 2.5rem !important;
                font-weight: 800 !important;
                color: #0f172a !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# REMOVED: apply_agentic_page_css() - Dead code, never used
# If needed in future, add these styles to apply_light_theme_css() instead
