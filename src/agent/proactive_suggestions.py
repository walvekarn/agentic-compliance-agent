"""
Proactive Suggestions Service

Generates contextual suggestions and insights based on:
- Upcoming calendar deadlines
- Similar high-risk past tasks
- Missing or incomplete information
- Pattern anomalies
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.db.models import EntityHistory, AuditTrail


class ProactiveSuggestionService:
    """Service for generating proactive suggestions based on context"""
    
    @staticmethod
    def generate_suggestions(
        db: Session,
        entity_name: str,
        task_category: str,
        current_decision: str,
        current_risk_level: str,
        jurisdictions: List[str],
        has_deadline: bool = False
    ) -> List[Dict]:
        """
        Generate proactive suggestions based on multiple factors
        
        Args:
            db: Database session
            entity_name: Organization name
            task_category: Category of current task
            current_decision: Decision made (AUTONOMOUS/REVIEW_REQUIRED/ESCALATE)
            current_risk_level: Risk level (LOW/MEDIUM/HIGH)
            jurisdictions: List of jurisdictions involved
            has_deadline: Whether task has a deadline
            
        Returns:
            List of suggestion dictionaries with type, message, priority, and action
        """
        suggestions = []
        
        # 1. Check for upcoming high-priority tasks (within 10 days)
        upcoming_suggestion = ProactiveSuggestionService._check_upcoming_tasks(
            db, entity_name
        )
        if upcoming_suggestion:
            suggestions.append(upcoming_suggestion)
        
        # 2. Check for similar high-risk past tasks
        similar_risk_suggestion = ProactiveSuggestionService._check_similar_high_risk(
            db, entity_name, task_category, jurisdictions
        )
        if similar_risk_suggestion:
            suggestions.append(similar_risk_suggestion)
        
        # 3. Check for missing required fields
        missing_fields_suggestion = ProactiveSuggestionService._check_missing_fields(
            jurisdictions, has_deadline
        )
        if missing_fields_suggestion:
            suggestions.append(missing_fields_suggestion)
        
        # 4. Check for decision anomaly (different from pattern)
        anomaly_suggestion = ProactiveSuggestionService._check_decision_anomaly(
            db, entity_name, task_category, current_decision
        )
        if anomaly_suggestion:
            suggestions.append(anomaly_suggestion)
        
        # 5. Check for escalation trend
        trend_suggestion = ProactiveSuggestionService._check_escalation_trend(
            db, entity_name
        )
        if trend_suggestion:
            suggestions.append(trend_suggestion)
        
        return suggestions
    
    @staticmethod
    def _check_upcoming_tasks(db: Session, entity_name: str) -> Optional[Dict]:
        """Check for upcoming high-priority tasks within 10 days"""
        try:
            cutoff_date = datetime.utcnow() + timedelta(days=10)
            
            # Query audit trail for recent high-risk decisions
            high_risk_upcoming = db.query(AuditTrail).filter(
                and_(
                    AuditTrail.entity_name == entity_name,
                    AuditTrail.risk_level == "HIGH",
                    AuditTrail.timestamp >= datetime.utcnow() - timedelta(days=30)
                )
            ).count()
            
            if high_risk_upcoming >= 3:
                return {
                    "type": "upcoming_tasks",
                    "priority": "high",
                    "icon": "📅",
                    "title": "High-Priority Tasks Detected",
                    "message": f"{high_risk_upcoming} high-priority tasks were identified in the last 30 days.",
                    "suggestion": "Consider reviewing your compliance calendar to ensure all deadlines are met.",
                    "action": "view_calendar",
                    "action_label": "View Compliance Calendar →"
                }
        except Exception as e:
            # Don't fail the entire request if this check fails
            print(f"Error checking upcoming tasks: {e}")
        
        return None
    
    @staticmethod
    def _check_similar_high_risk(
        db: Session,
        entity_name: str,
        task_category: str,
        jurisdictions: List[str]
    ) -> Optional[Dict]:
        """Check for similar high-risk past tasks"""
        try:
            # Find similar tasks that were high risk
            similar_high_risk = db.query(EntityHistory).filter(
                and_(
                    EntityHistory.entity_name == entity_name,
                    EntityHistory.task_category == task_category,
                    EntityHistory.risk_level == "HIGH"
                )
            ).order_by(EntityHistory.timestamp.desc()).first()
            
            if similar_high_risk:
                # Check if jurisdictions overlap
                past_jurisdictions = similar_high_risk.jurisdictions or []
                overlap = set(jurisdictions) & set(past_jurisdictions)
                
                if overlap:
                    jurisdiction_names = ", ".join(overlap)
                    days_ago = (datetime.utcnow() - similar_high_risk.timestamp).days
                    
                    return {
                        "type": "similar_high_risk",
                        "priority": "high",
                        "icon": "⚠️",
                        "title": "Similar High-Risk Task Found",
                        "message": f"This task appears similar to a previous high-risk item from {days_ago} days ago involving {jurisdiction_names}.",
                        "suggestion": "Review the previous case for lessons learned and required approvals.",
                        "action": "view_history",
                        "action_label": "View Similar Case →",
                        "metadata": {
                            "history_id": similar_high_risk.id,
                            "past_decision": similar_high_risk.decision,
                            "past_confidence": similar_high_risk.confidence_score
                        }
                    }
        except Exception as e:
            print(f"Error checking similar high-risk tasks: {e}")
        
        return None
    
    @staticmethod
    def _check_missing_fields(
        jurisdictions: List[str],
        has_deadline: bool
    ) -> Optional[Dict]:
        """Check for missing required fields"""
        missing = []
        
        if not jurisdictions or len(jurisdictions) == 0:
            missing.append("jurisdiction information")
        
        if not has_deadline:
            missing.append("regulatory deadline")
        
        if missing:
            fields_list = " and ".join(missing)
            return {
                "type": "missing_fields",
                "priority": "medium",
                "icon": "ℹ️",
                "title": "Optional Information Missing",
                "message": f"You didn't provide {fields_list}.",
                "suggestion": "Adding this information can improve decision accuracy. You can resubmit with complete details.",
                "action": "none",
                "action_label": None
            }
        
        return None
    
    @staticmethod
    def _check_decision_anomaly(
        db: Session,
        entity_name: str,
        task_category: str,
        current_decision: str
    ) -> Optional[Dict]:
        """Check if current decision differs from typical pattern"""
        try:
            # Get last 5 similar decisions
            past_decisions = db.query(EntityHistory).filter(
                and_(
                    EntityHistory.entity_name == entity_name,
                    EntityHistory.task_category == task_category
                )
            ).order_by(EntityHistory.timestamp.desc()).limit(5).all()
            
            if len(past_decisions) >= 3:
                # Check if current decision is different from majority
                decision_counts = {}
                for past in past_decisions:
                    decision_counts[past.decision] = decision_counts.get(past.decision, 0) + 1
                
                # Find most common past decision
                most_common = max(decision_counts, key=decision_counts.get)
                most_common_count = decision_counts[most_common]
                
                # If current is different and past pattern is strong (>60%)
                if (current_decision != most_common and 
                    most_common_count / len(past_decisions) >= 0.6):
                    
                    percentage = (most_common_count / len(past_decisions) * 100)
                    
                    return {
                        "type": "decision_anomaly",
                        "priority": "medium",
                        "icon": "🔍",
                        "title": "Decision Differs from Pattern",
                        "message": f"In the past, similar tasks were typically '{most_common}' ({percentage:.0f}% of the time).",
                        "suggestion": "This doesn't mean the current decision is wrong, but you may want to understand why this case differs.",
                        "action": "none",
                        "action_label": None
                    }
        except Exception as e:
            print(f"Error checking decision anomaly: {e}")
        
        return None
    
    @staticmethod
    def _check_escalation_trend(
        db: Session,
        entity_name: str
    ) -> Optional[Dict]:
        """Check if there's a concerning escalation trend"""
        try:
            # Get decisions from last 30 days
            recent_cutoff = datetime.utcnow() - timedelta(days=30)
            recent_decisions = db.query(EntityHistory).filter(
                and_(
                    EntityHistory.entity_name == entity_name,
                    EntityHistory.timestamp >= recent_cutoff
                )
            ).all()
            
            if len(recent_decisions) >= 5:
                escalation_count = sum(1 for d in recent_decisions if d.decision == "ESCALATE")
                escalation_rate = escalation_count / len(recent_decisions)
                
                # If escalation rate is high (>50%)
                if escalation_rate >= 0.5:
                    return {
                        "type": "escalation_trend",
                        "priority": "medium",
                        "icon": "📈",
                        "title": "High Escalation Rate Detected",
                        "message": f"{escalation_rate*100:.0f}% of recent tasks ({escalation_count}/{len(recent_decisions)}) required escalation.",
                        "suggestion": "Consider scheduling a review with your compliance team to address systemic issues.",
                        "action": "none",
                        "action_label": None
                    }
        except Exception as e:
            print(f"Error checking escalation trend: {e}")
        
        return None


def format_suggestions_for_display(suggestions: List[Dict]) -> str:
    """
    Format suggestions as a readable text summary
    
    Args:
        suggestions: List of suggestion dictionaries
        
    Returns:
        Formatted string for display
    """
    if not suggestions:
        return ""
    
    lines = []
    for i, sugg in enumerate(suggestions, 1):
        icon = sugg.get("icon", "💡")
        title = sugg.get("title", "Suggestion")
        message = sugg.get("message", "")
        lines.append(f"{icon} **{title}**: {message}")
    
    return "\n\n".join(lines)

