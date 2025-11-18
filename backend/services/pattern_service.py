"""
Pattern Analysis Service

Analyzes patterns in entity decision history.
"""

from typing import Dict, Any, List
from backend.repositories.entity_history_repository import EntityHistoryRepository


class PatternService:
    """Service for analyzing patterns in entity decision history"""
    
    def __init__(self, entity_repository: EntityHistoryRepository):
        """
        Initialize pattern service.
        
        Args:
            entity_repository: Repository for entity history
        """
        self.entity_repository = entity_repository
    
    def analyze_decision_patterns(
        self,
        entity_name: str,
        task_category: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze decision patterns for entity/task combination.
        
        Args:
            entity_name: Entity name
            task_category: Task category
            limit: Maximum number of similar cases to analyze
            
        Returns:
            Dictionary with pattern analysis including:
            - similar_cases: List of similar cases
            - pattern_analysis: Text description of patterns
            - statistics: Decision distribution percentages
        """
        # Fetch similar cases
        similar_cases = self.entity_repository.find_by_entity_and_category(
            entity_name, task_category, limit
        )
        
        if not similar_cases:
            return {
                "similar_cases": [],
                "pattern_analysis": None,
                "statistics": {}
            }
        
        # Convert to dicts
        similar_cases_dicts = [case.to_dict() for case in similar_cases]
        
        # Calculate statistics
        total_cases = len(similar_cases_dicts)
        autonomous_count = sum(1 for c in similar_cases_dicts if c['decision'] == 'AUTONOMOUS')
        review_count = sum(1 for c in similar_cases_dicts if c['decision'] == 'REVIEW_REQUIRED')
        escalate_count = sum(1 for c in similar_cases_dicts if c['decision'] == 'ESCALATE')
        
        # Build pattern analysis text
        pattern_parts = [
            f"Based on {total_cases} similar past {'case' if total_cases == 1 else 'cases'} for {entity_name}:"
        ]
        
        if escalate_count > 0:
            escalate_pct = (escalate_count / total_cases * 100)
            pattern_parts.append(f"escalated {escalate_pct:.0f}% of the time")
        
        if review_count > 0:
            review_pct = (review_count / total_cases * 100)
            pattern_parts.append(f"required review {review_pct:.0f}% of the time")
        
        if autonomous_count > 0:
            autonomous_pct = (autonomous_count / total_cases * 100)
            pattern_parts.append(f"handled autonomously {autonomous_pct:.0f}% of the time")
        
        # Average confidence
        avg_confidence = sum(c.get('confidence_score', 0) or 0 for c in similar_cases_dicts) / total_cases
        
        pattern_analysis = ". ".join(pattern_parts) + "."
        
        return {
            "similar_cases": similar_cases_dicts,
            "pattern_analysis": pattern_analysis,
            "statistics": {
                "total_cases": total_cases,
                "autonomous_pct": (autonomous_count / total_cases * 100) if total_cases > 0 else 0,
                "review_pct": (review_count / total_cases * 100) if total_cases > 0 else 0,
                "escalate_pct": (escalate_count / total_cases * 100) if total_cases > 0 else 0,
                "avg_confidence": avg_confidence
            }
        }

