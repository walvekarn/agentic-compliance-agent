"""
Schema Loader
=============
Helper functions to load and access unified schemas.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Get the directory containing this file
SCHEMAS_DIR = Path(__file__).parent


def load_jurisdictions() -> List[Dict[str, Any]]:
    """
    Load jurisdictions from unified schema.
    
    Returns:
        List of jurisdiction dictionaries with code, name, regulations, description
    """
    jurisdictions_file = SCHEMAS_DIR / "jurisdictions.json"
    with open(jurisdictions_file, 'r') as f:
        data = json.load(f)
    return data.get("jurisdictions", [])


def load_task_categories() -> List[Dict[str, Any]]:
    """
    Load task categories from unified schema.
    
    Returns:
        List of task category dictionaries with code, name, description, complexity, typical_risk
    """
    categories_file = SCHEMAS_DIR / "task_categories.json"
    with open(categories_file, 'r') as f:
        data = json.load(f)
    return data.get("task_categories", [])


def get_jurisdiction_by_code(code: str) -> Optional[Dict[str, Any]]:
    """
    Get jurisdiction by code.
    
    Args:
        code: Jurisdiction code (e.g., "EU", "US_FEDERAL")
        
    Returns:
        Jurisdiction dictionary or None if not found
    """
    jurisdictions = load_jurisdictions()
    for j in jurisdictions:
        if j.get("code") == code:
            return j
    return None


def get_jurisdiction_name(code: str) -> str:
    """
    Get jurisdiction name by code.
    
    Args:
        code: Jurisdiction code
        
    Returns:
        Jurisdiction name or code if not found
    """
    jurisdiction = get_jurisdiction_by_code(code)
    if jurisdiction:
        return jurisdiction.get("name", code)
    return code


def get_task_category_by_code(code: str) -> Optional[Dict[str, Any]]:
    """
    Get task category by code.
    
    Args:
        code: Task category code (e.g., "DATA_PRIVACY")
        
    Returns:
        Task category dictionary or None if not found
    """
    categories = load_task_categories()
    for cat in categories:
        if cat.get("code") == code:
            return cat
    return None


def get_task_category_name(code: str) -> str:
    """
    Get task category name by code.
    
    Args:
        code: Task category code
        
    Returns:
        Task category name or code if not found
    """
    category = get_task_category_by_code(code)
    if category:
        return category.get("name", code)
    return code


def get_all_jurisdiction_codes() -> List[str]:
    """Get list of all jurisdiction codes"""
    jurisdictions = load_jurisdictions()
    return [j.get("code") for j in jurisdictions if j.get("code")]


def get_all_task_category_codes() -> List[str]:
    """Get list of all task category codes"""
    categories = load_task_categories()
    return [cat.get("code") for cat in categories if cat.get("code")]


def normalize_jurisdiction_name(name: str) -> str:
    """
    Normalize jurisdiction name to match schema.
    
    Args:
        name: Jurisdiction name (e.g., "European Union", "EU")
        
    Returns:
        Normalized name from schema
    """
    # Try exact match first
    jurisdictions = load_jurisdictions()
    for j in jurisdictions:
        if j.get("name") == name or j.get("code") == name:
            return j.get("name", name)
    
    # Try case-insensitive match
    name_lower = name.lower()
    for j in jurisdictions:
        if j.get("name", "").lower() == name_lower or j.get("code", "").lower() == name_lower:
            return j.get("name", name)
    
    return name

