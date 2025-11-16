"""
Shared Constants and Mappings
==============================
Centralized constants to prevent mapping mismatches between frontend and backend.
"""

# ============================================================================
# FRONTEND → BACKEND MAPPINGS
# ============================================================================

TYPE_MAP = {
    "New startup (less than 3 years old)": "STARTUP",
    "Private company (not traded publicly)": "PRIVATE_COMPANY",
    "Public company (traded on stock exchange)": "PUBLIC_COMPANY",
    "Bank or financial institution": "FINANCIAL_INSTITUTION",
    "Hospital, clinic, or healthcare provider": "HEALTHCARE",
    "Non-profit or charity": "NONPROFIT",
    "Government agency or department": "GOVERNMENT"
}

INDUSTRY_MAP = {
    "Technology and software": "TECHNOLOGY",
    "Banking and financial services": "FINANCIAL_SERVICES",
    "Healthcare and medical": "HEALTHCARE",
    "Retail and e-commerce": "RETAIL",
    "Manufacturing": "MANUFACTURING",
    "Education": "EDUCATION",
    "Government": "GOVERNMENT",
    "Other": "OTHER"  # FIXED: was "UNKNOWN" - backend expects "OTHER"
}

TASK_MAP = {
    "General question or inquiry": "GENERAL_INQUIRY",
    "Reviewing or updating a policy": "POLICY_REVIEW",
    "Working with customer data": "DATA_PRIVACY",
    "Assessing potential risks": "RISK_ASSESSMENT",
    "Reviewing a contract or agreement": "CONTRACT_REVIEW",
    "Security or IT system check": "SECURITY_AUDIT",
    "Financial report or disclosure": "FINANCIAL_REPORTING",
    "Filing something with a government agency": "REGULATORY_FILING",
    "Responding to an incident or problem": "INCIDENT_RESPONSE"
}

IMPACT_MAP = {
    "Not much": "Low",
    "Minor problems": "Moderate",
    "Serious issues": "Significant",
    "Major crisis": "Critical"
}

JURISDICTION_DISPLAY_TO_CODE = {
    "United States": "US_FEDERAL",
    "California (additional state rules)": "US_CA",
    "New York (additional state rules)": "US_NY",
    "European Union countries": "EU",
    "United Kingdom": "UK",
    "Canada": "CANADA",
    "Australia": "AUSTRALIA",
    "Multiple countries worldwide": "MULTI_JURISDICTIONAL"
}

CODE_TO_JURISDICTION_DISPLAY = {
    code: display for display, code in JURISDICTION_DISPLAY_TO_CODE.items()
}

# ============================================================================
# DROPDOWN OPTIONS
# ============================================================================

COMPANY_TYPE_OPTIONS = [
    "-- Please select --",
    "New startup (less than 3 years old)",
    "Private company (not traded publicly)",
    "Public company (traded on stock exchange)",
    "Bank or financial institution)",
    "Hospital, clinic, or healthcare provider",
    "Non-profit or charity",
    "Government agency or department"
]

INDUSTRY_OPTIONS = [
    "-- Please select --",
    "Technology and software",
    "Banking and financial services",
    "Healthcare and medical",
    "Retail and e-commerce",
    "Manufacturing",
    "Education",
    "Government",
    "Other"
]

TASK_TYPE_OPTIONS = [
    "-- Please select --",
    "General question or inquiry",
    "Reviewing or updating a policy",
    "Working with customer data",
    "Assessing potential risks",
    "Reviewing a contract or agreement",
    "Security or IT system check",
    "Financial report or disclosure",
    "Filing something with a government agency",
    "Responding to an incident or problem"
]

IMPACT_OPTIONS = [
    "-- Select impact --",
    "Not much",
    "Minor problems",
    "Serious issues",
    "Major crisis"
]

LOCATION_OPTIONS = [
    "United States",
    "California (additional state rules)",
    "New York (additional state rules)",
    "European Union countries",
    "United Kingdom",
    "Canada",
    "Australia",
    "Multiple countries worldwide"
]

# ============================================================================
# EXAMPLE FORM DATA
# ============================================================================

EXAMPLE_FORM_VALUES = {
    "company_name": "Acme Robotics",
    "company_type": "Private company (not traded publicly)",
    "industry": "Technology and software",
    "employee_count": "250",
    "locations": ["United States", "European Union countries"],
    "handles_data": True,
    "is_regulated": False,
    "task_description": "We need to update our privacy policy to include new features we're launching next month. The features involve collecting user preferences and behavior data to personalize the experience.",
    "task_type": "Reviewing or updating a policy",
    "involves_personal": True,
    "involves_financial": False,
    "crosses_borders": True,
    "has_deadline": True,
    "impact_level": "Serious issues",
    "people_affected": "50000"
}

# ============================================================================
# API CONFIGURATION
# ============================================================================

import os
import socket

def _detect_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# Prefer BACKEND_URL if provided, then API_BASE_URL; else fallback to LAN IP
_env_backend = os.getenv("BACKEND_URL") or os.getenv("API_BASE_URL")
if _env_backend and _env_backend.strip():
    API_BASE_URL = _env_backend.rstrip("/")
else:
    API_BASE_URL = f"http://{_detect_lan_ip()}:8000"
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# ============================================================================
# APP STATES
# ============================================================================

class AppState:
    """Application state constants"""
    FORM = "FORM"
    LOADING = "LOADING"
    RESULTS = "RESULTS"
    ERROR = "ERROR"

