"""
Demo Data Helper
================
Provides sample demo data when the database is empty to help users understand
the system and see what metrics look like.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import random


def get_demo_audit_statistics() -> Dict[str, Any]:
    """Generate demo audit statistics for empty database"""
    return {
        "total_decisions": 42,
        "autonomous_count": 28,
        "review_required_count": 10,
        "escalate_count": 4,
        "avg_confidence": 0.82,
        "high_risk_count": 6,
        "medium_risk_count": 18,
        "low_risk_count": 18,
        "last_updated": datetime.now().isoformat()
    }


def get_demo_feedback_stats() -> Dict[str, Any]:
    """Generate demo feedback statistics for empty database"""
    return {
        "total_feedback_count": 15,
        "agreement_count": 12,
        "override_count": 3,
        "accuracy_percent": 80.0,
        "most_overridden_decision": "REVIEW_REQUIRED",
        "override_breakdown": {
            "AUTONOMOUS": 1,
            "REVIEW_REQUIRED": 2,
            "ESCALATE": 0
        }
    }


def get_demo_audit_entries(count: int = 10) -> List[Dict[str, Any]]:
    """Generate demo audit entries for empty database"""
    entries = []
    base_time = datetime.now() - timedelta(days=30)
    
    decision_types = ["AUTONOMOUS", "REVIEW_REQUIRED", "ESCALATE"]
    risk_levels = ["LOW", "MEDIUM", "HIGH"]
    task_categories = ["DATA_PROTECTION", "PRIVACY", "REGULATORY_COMPLIANCE", "SECURITY"]
    entities = ["Acme Corp", "TechStart Inc", "Global Services Ltd", "Digital Solutions"]
    jurisdictions = ["US_FEDERAL", "EU", "US_CA", "UK"]
    
    for i in range(count):
        decision = random.choice(decision_types)
        risk = random.choice(risk_levels)
        confidence = random.uniform(0.65, 0.95)
        
        entry = {
            "audit_id": i + 1,
            "timestamp": (base_time + timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))).isoformat(),
            "agent_type": "decision_engine",
            "task": {
                "description": f"Review {random.choice(['privacy policy', 'data processing agreement', 'compliance checklist', 'security audit'])}",
                "category": random.choice(task_categories)
            },
            "entity": {
                "name": random.choice(entities),
                "type": "PRIVATE_COMPANY"
            },
            "decision": {
                "outcome": decision,
                "confidence_score": confidence,
                "risk_level": risk,
                "risk_score": random.uniform(0.3, 0.9)
            },
            "entity_context": {
                "jurisdictions": random.sample(jurisdictions, random.randint(1, 2)),
                "industry": "TECHNOLOGY"
            },
            "risk_factors": {
                "jurisdiction_risk": random.uniform(0.2, 0.8),
                "entity_risk": random.uniform(0.2, 0.7),
                "task_risk": random.uniform(0.3, 0.9),
                "data_sensitivity_risk": random.uniform(0.2, 0.8),
                "regulatory_risk": random.uniform(0.2, 0.7),
                "impact_risk": random.uniform(0.1, 0.6)
            },
            "reasoning_chain": [
                "Analyzed entity risk profile",
                f"Evaluated {risk.lower()} risk factors",
                f"Determined {decision.lower()} decision"
            ],
            "escalation_reason": "High complexity" if decision == "ESCALATE" else None
        }
        entries.append(entry)
    
    return entries


def should_use_demo_data(api_response: Any, data_key: str = None) -> bool:
    """
    Determine if demo data should be used.
    
    Args:
        api_response: APIResponse object
        data_key: Optional key to check in response.data
        
    Returns:
        True if demo data should be used (empty/error response)
    """
    if not api_response or not api_response.success:
        return True
    
    if not api_response.data:
        return True
    
    if data_key:
        data = api_response.data.get(data_key) if isinstance(api_response.data, dict) else None
        if not data or (isinstance(data, list) and len(data) == 0) or (isinstance(data, dict) and not data):
            return True
    
    return False

