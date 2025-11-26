"""Centralized theme helpers for Streamlit pages."""

import streamlit as st


def apply_home_theme_css() -> None:
    """Apply the Home page styling (moved out of inline blocks)."""
    st.markdown(
        """
        <style>
            .main {padding: 1rem 2rem 2rem 2rem; max-width: 1400px; margin: 0 auto;}
            h1 {font-size: 4rem !important; font-weight: 800 !important; color: #0f172a !important; text-align: center; margin-bottom: 0.75rem !important; line-height: 1.1 !important;}
            h2 {font-size: 2.5rem !important; font-weight: 700 !important; color: #1e40af !important; margin-top: 2.5rem !important; margin-bottom: 1.5rem !important; text-align: center;}
            h3 {font-size: 2rem !important; font-weight: 700 !important; color: #2563eb !important; margin-top: 1.5rem !important; margin-bottom: 1rem !important;}
            p, li, div {font-size: 1.25rem !important; line-height: 1.7 !important; color: #1e293b !important;}
            .feature-card {background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 2.5rem; border-radius: 20px; margin: 1.5rem 0; box-shadow: 0 8px 16px rgba(0,0,0,0.1); border: 3px solid #7dd3fc; transition: all 0.3s; min-height: 280px;}
            .feature-card:hover {transform: translateY(-5px); box-shadow: 0 12px 24px rgba(0,0,0,0.15); border-color: #3b82f6;}
            .feature-card h3 {font-size: 2.25rem !important; font-weight: 800 !important; margin-bottom: 1.25rem !important; color: #0f172a !important; text-align: center;}
            .feature-card p {font-size: 1.35rem !important; color: #1e40af !important; margin-bottom: 1.25rem !important; font-weight: 500; text-align: center;}
            .feature-card ul {font-size: 1.2rem !important; color: #1e293b !important; list-style-position: inside;}
            .feature-card ul li {font-size: 1.2rem !important; padding: 0.5rem 0; color: #1e293b !important;}
            .stButton button {font-size: 1.4rem !important; font-weight: 700 !important; padding: 1.25rem 2.5rem !important; border-radius: 15px !important; transition: all 0.3s !important; text-transform: none !important; box-shadow: 0 6px 12px rgba(59, 130, 246, 0.3) !important;}
            .stButton button:hover {transform: translateY(-3px) !important; box-shadow: 0 10px 20px rgba(59, 130, 246, 0.4) !important;}
            .stAlert {font-size: 1.3rem !important; padding: 1.5rem !important; border-radius: 15px !important; margin: 1.5rem 0 !important;}
            .stMetric {background-color: #f8fafc !important; padding: 2rem !important; border-radius: 15px !important; border: 3px solid #cbd5e1 !important;}
            .stMetric label {font-size: 1.3rem !important; font-weight: 600 !important; color: #0f172a !important;}
            .stMetric [data-testid="stMetricValue"] {font-size: 2.5rem !important; font-weight: 800 !important; color: #0f172a !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_agentic_page_css() -> None:
    """Lightweight styling used on Agentic Analysis page badges/cards."""
    st.markdown(
        """
        <style>
            .agentic-badge {background: linear-gradient(135deg, #dbeafe, #bfdbfe); color: #0f172a; padding: 0.5rem 0.75rem; border-radius: 10px; display: inline-block; font-weight: 700; border: 1px solid #93c5fd;}
            .agentic-card {background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem; box-shadow: 0 2px 6px rgba(0,0,0,0.05);}
        </style>
        """,
        unsafe_allow_html=True,
    )
