"""
Form Utilities
==============
Helper functions for form input parsing and validation.
"""

from typing import Optional, List


def parse_positive_int(value: str, field_label: str, errors: List[str], minimum: int = 1) -> Optional[int]:
    """
    Convert text input to a positive integer.
    
    Args:
        value: String value to parse
        field_label: Human-readable field name for error messages
        errors: List to append error messages to
        minimum: Minimum allowed value
        
    Returns:
        Parsed integer or None if invalid
    """
    if not value or not value.strip():
        errors.append(f"Please enter {field_label}")
        return None
    try:
        number = int(value.strip())
        if number < minimum:
            errors.append(f"Please enter {field_label} (at least {minimum})")
            return None
        return number
    except ValueError:
        errors.append(f"Please enter a whole number for {field_label}")
        return None


def parse_optional_int(value: str, field_label: str, errors: List[str], minimum: int = 0) -> Optional[int]:
    """
    Convert optional text input to integer or None.
    
    Args:
        value: String value to parse  
        field_label: Human-readable field name for error messages
        errors: List to append error messages to
        minimum: Minimum allowed value
        
    Returns:
        Parsed integer, None if empty, or None if invalid (with error added)
    """
    if not value or not value.strip():
        return None
    try:
        number = int(value.strip())
        if number < minimum:
            errors.append(f"Please enter {field_label} (cannot be less than {minimum})")
            return None
        return number
    except ValueError:
        errors.append(f"Please enter a whole number for {field_label}")
        return None


def describe_confidence(value: float) -> tuple:
    """
    Return a plain-language description for the confidence score.
    
    Args:
        value: Confidence score (0.0 to 1.0)
        
    Returns:
        Tuple of (confidence_label, advice)
    """
    if value >= 0.85:
        return "Very confident", "You can rely on this recommendation."
    if value >= 0.65:
        return "Moderately confident", "Consider a quick double-check with your reviewer."
    return "Cautious", "Treat this as a starting point and involve a reviewer immediately."


def describe_risk_level(level: str) -> tuple:
    """
    Get user-friendly description of risk level.
    
    Args:
        level: Risk level (LOW, MEDIUM, HIGH)
        
    Returns:
        Tuple of (label, description)
    """
    mapping = {
        "LOW": ("🟢 Low Priority", "Routine work with minimal compliance risk."),
        "MEDIUM": ("🟡 Medium Priority", "Worth a second look before proceeding."),
        "HIGH": ("🔴 High Priority", "Needs expert attention before you continue.")
    }
    return mapping.get(level, ("⚪ Priority not set", "No priority information was returned."))

