"""
Proactive Suggestions Service

Generates contextual suggestions based on triggers:
- Deadlines: Upcoming regulatory deadlines
- Risk Trends: Rising risk patterns
- Violations: Previous compliance violations
- Multiple Incidents: Recurring incidents
- Regulatory Patterns: Regulatory changes or patterns
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.db.models import EntityHistory, AuditTrail

logger = logging.getLogger(__name__)


class ProactiveSuggestionService:
    """Service for generating proactive suggestions based on triggers"""
    
    @staticmethod
    def check_triggers(
        db: Session,
        entity_name: str,
        task_category: Optional[str] = None
    ) -> List[Dict]:
        """
        Check all triggers and return list of suggestion objects.
        
        Args:
            db: Database session
            entity_name: Organization name
            task_category: Optional task category filter
        
        Returns:
            List of suggestion objects with trigger type, priority, message, and action
        """
        suggestions = []
        
        # Trigger 1: Deadlines
        deadline_suggestions = ProactiveSuggestionService._check_deadlines(
            db, entity_name, task_category
        )
        suggestions.extend(deadline_suggestions)
        
        # Trigger 2: Risk Trends
        risk_trend_suggestions = ProactiveSuggestionService._check_risk_trends(
            db, entity_name, task_category
        )
        suggestions.extend(risk_trend_suggestions)
        
        # Trigger 3: Violations
        violation_suggestions = ProactiveSuggestionService._check_violations(
            db, entity_name
        )
        suggestions.extend(violation_suggestions)
        
        # Trigger 4: Multiple Incidents
        incident_suggestions = ProactiveSuggestionService._check_multiple_incidents(
            db, entity_name, task_category
        )
        suggestions.extend(incident_suggestions)
        
        # Trigger 5: Regulatory Patterns
        regulatory_suggestions = ProactiveSuggestionService._check_regulatory_patterns(
            db, entity_name, task_category
        )
        suggestions.extend(regulatory_suggestions)
        
        return suggestions
    
    @staticmethod
    def _check_deadlines(
        db: Session,
        entity_name: str,
        task_category: Optional[str] = None
    ) -> List[Dict]:
        """
        Check for upcoming deadlines trigger.
        
        Returns suggestions for:
        - Deadlines within 7 days (critical)
        - Deadlines within 30 days (high priority)
        - Multiple upcoming deadlines
        """
        suggestions = []
        
        try:
            now = datetime.now(timezone.utc)
            seven_days = now + timedelta(days=7)
            thirty_days = now + timedelta(days=30)
            
            # Query for tasks with deadlines in metadata
            query = db.query(AuditTrail).filter(
                and_(
                    AuditTrail.entity_name == entity_name,
                    AuditTrail.timestamp >= now - timedelta(days=90)
                )
            )
            
            if task_category:
                query = query.filter(AuditTrail.task_category == task_category)
            
            recent_tasks = query.all()
            
            # Count tasks with deadlines mentioned
            deadline_tasks = []
            for task in recent_tasks:
                metadata = task.meta_data or {}
                if metadata.get('deadline') or metadata.get('regulatory_deadline'):
                    deadline_tasks.append(task)
            
            # Check for critical deadlines (within 7 days)
            critical_count = 0
            upcoming_count = 0
            
            for task in deadline_tasks:
                metadata = task.meta_data or {}
                deadline_str = metadata.get('deadline') or metadata.get('regulatory_deadline')
                
                if deadline_str:
                    try:
                        if isinstance(deadline_str, str):
                            deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                        else:
                            continue
                        
                        days_until = (deadline - now).days
                        
                        if 0 <= days_until <= 7:
                            critical_count += 1
                        elif 8 <= days_until <= 30:
                            upcoming_count += 1
                    except:
                        continue
            
            if critical_count > 0:
                suggestions.append({
                    "trigger": "deadlines",
                    "trigger_type": "critical_deadline",
                    "priority": "high",
                    "icon": "🚨",
                    "title": "Critical Deadline Approaching",
                    "message": f"{critical_count} regulatory deadline(s) due within 7 days.",
                    "suggestion": "Immediate action required. Review and prioritize these tasks to avoid compliance penalties.",
                    "action": "view_deadlines",
                    "action_label": "View Critical Deadlines →",
                    "metadata": {
                        "critical_count": critical_count,
                        "upcoming_count": upcoming_count,
                        "timeframe": "7_days"
                    }
                })
            elif upcoming_count >= 3:
                suggestions.append({
                    "trigger": "deadlines",
                    "trigger_type": "multiple_upcoming",
                    "priority": "medium",
                    "icon": "📅",
                    "title": "Multiple Upcoming Deadlines",
                    "message": f"{upcoming_count} deadline(s) approaching within 30 days.",
                    "suggestion": "Plan ahead to ensure all deadlines are met. Consider scheduling compliance reviews.",
                    "action": "view_calendar",
                    "action_label": "View Compliance Calendar →",
                    "metadata": {
                        "upcoming_count": upcoming_count,
                        "timeframe": "30_days"
                    }
                })
        
        except Exception as e:
            logger.error(f"Error checking deadlines: {e}")
        
        return suggestions
    
    @staticmethod
    def _check_risk_trends(
        db: Session,
        entity_name: str,
        task_category: Optional[str] = None
    ) -> List[Dict]:
        """
        Check for risk trends trigger.
        
        Returns suggestions for:
        - Rising risk scores over time
        - Increasing escalation rate
        - Trend from LOW to HIGH risk
        """
        suggestions = []
        
        try:
            now = datetime.now(timezone.utc)
            thirty_days_ago = now - timedelta(days=30)
            sixty_days_ago = now - timedelta(days=60)
            
            # Get recent decisions
            recent_query = db.query(EntityHistory).filter(
                and_(
                    EntityHistory.entity_name == entity_name,
                    EntityHistory.timestamp >= thirty_days_ago,
                    EntityHistory.risk_score.isnot(None)
                )
            )
            
            if task_category:
                recent_query = recent_query.filter(EntityHistory.task_category == task_category)
            
            recent_decisions = recent_query.order_by(EntityHistory.timestamp.desc()).all()
            
            # Get older decisions for comparison
            older_query = db.query(EntityHistory).filter(
                and_(
                    EntityHistory.entity_name == entity_name,
                    EntityHistory.timestamp >= sixty_days_ago,
                    EntityHistory.timestamp < thirty_days_ago,
                    EntityHistory.risk_score.isnot(None)
                )
            )
            
            if task_category:
                older_query = older_query.filter(EntityHistory.task_category == task_category)
            
            older_decisions = older_query.all()
            
            if len(recent_decisions) >= 3 and len(older_decisions) >= 3:
                # Calculate average risk scores
                recent_avg = sum(d.risk_score for d in recent_decisions if d.risk_score) / len(recent_decisions)
                older_avg = sum(d.risk_score for d in older_decisions if d.risk_score) / len(older_decisions)
                
                risk_increase = recent_avg - older_avg
                
                # Check escalation trend
                recent_escalations = sum(1 for d in recent_decisions if d.decision == "ESCALATE")
                older_escalations = sum(1 for d in older_decisions if d.decision == "ESCALATE")
                recent_escalation_rate = recent_escalations / len(recent_decisions)
                older_escalation_rate = older_escalations / len(older_decisions) if older_decisions else 0
                
                # Rising risk trend
                if risk_increase >= 0.15:
                    suggestions.append({
                        "trigger": "risk_trends",
                        "trigger_type": "rising_risk",
                        "priority": "high",
                        "icon": "📈",
                        "title": "Rising Risk Trend Detected",
                        "message": f"Average risk score increased by {risk_increase:.2f} over the last 30 days ({older_avg:.2f} → {recent_avg:.2f}).",
                        "suggestion": "Review recent decisions to identify patterns. Consider scheduling a compliance audit to address systemic issues.",
                        "action": "view_risk_analysis",
                        "action_label": "View Risk Analysis →",
                        "metadata": {
                            "recent_avg_risk": recent_avg,
                            "older_avg_risk": older_avg,
                            "risk_increase": risk_increase,
                            "recent_count": len(recent_decisions),
                            "older_count": len(older_decisions)
                        }
                    })
                
                # Escalation trend
                if recent_escalation_rate >= 0.5 and recent_escalation_rate > older_escalation_rate + 0.2:
                    suggestions.append({
                        "trigger": "risk_trends",
                        "trigger_type": "escalation_trend",
                        "priority": "medium",
                        "icon": "⚠️",
                        "title": "Increasing Escalation Rate",
                        "message": f"Escalation rate increased to {recent_escalation_rate*100:.0f}% (from {older_escalation_rate*100:.0f}%).",
                        "suggestion": "More tasks are requiring expert review. Consider training or process improvements to reduce escalation needs.",
                        "action": "view_escalation_trends",
                        "action_label": "View Escalation Trends →",
                        "metadata": {
                            "recent_escalation_rate": recent_escalation_rate,
                            "older_escalation_rate": older_escalation_rate,
                            "recent_escalations": recent_escalations,
                            "total_recent": len(recent_decisions)
                        }
                    })
        
        except Exception as e:
            logger.error(f"Error checking risk trends: {e}")
        
        return suggestions
    
    @staticmethod
    def _check_violations(
        db: Session,
        entity_name: str
    ) -> List[Dict]:
        """
        Check for violations trigger.
        
        Returns suggestions for:
        - Recent violations
        - Multiple violations
        - Violation patterns
        """
        suggestions = []
        
        try:
            # Query entity history for violation indicators
            # Violations are typically indicated in metadata or by high-risk escalations
            now = datetime.now(timezone.utc)
            ninety_days_ago = now - timedelta(days=90)
            
            # Check for high-risk escalations that might indicate violations
            violation_indicators = db.query(EntityHistory).filter(
                and_(
                    EntityHistory.entity_name == entity_name,
                    EntityHistory.timestamp >= ninety_days_ago,
                    EntityHistory.risk_level == "HIGH",
                    EntityHistory.decision == "ESCALATE"
                )
            ).order_by(EntityHistory.timestamp.desc()).all()
            
            if len(violation_indicators) >= 2:
                # Check metadata for explicit violation flags
                explicit_violations = []
                for indicator in violation_indicators:
                    metadata = indicator.meta_data or {}
                    if metadata.get('violation') or metadata.get('compliance_issue'):
                        explicit_violations.append(indicator)
                
                if len(explicit_violations) >= 1:
                    suggestions.append({
                        "trigger": "violations",
                        "trigger_type": "recent_violations",
                        "priority": "high",
                        "icon": "🚨",
                        "title": "Compliance Violations Detected",
                        "message": f"{len(explicit_violations)} compliance violation(s) identified in the last 90 days.",
                        "suggestion": "Immediate action required. Review violation details and implement corrective measures. Consider engaging compliance specialist.",
                        "action": "view_violations",
                        "action_label": "View Violations →",
                        "metadata": {
                            "violation_count": len(explicit_violations),
                            "timeframe": "90_days",
                            "most_recent": explicit_violations[0].timestamp.isoformat() if explicit_violations else None
                        }
                    })
                elif len(violation_indicators) >= 3:
                    suggestions.append({
                        "trigger": "violations",
                        "trigger_type": "multiple_high_risk",
                        "priority": "medium",
                        "icon": "⚠️",
                        "title": "Multiple High-Risk Escalations",
                        "message": f"{len(violation_indicators)} high-risk escalations in the last 90 days may indicate compliance issues.",
                        "suggestion": "Review escalated cases for patterns. Consider proactive compliance measures to prevent future issues.",
                        "action": "view_high_risk_cases",
                        "action_label": "View High-Risk Cases →",
                        "metadata": {
                            "escalation_count": len(violation_indicators),
                            "timeframe": "90_days"
                        }
                    })
        
        except Exception as e:
            logger.error(f"Error checking violations: {e}")
        
        return suggestions
    
    @staticmethod
    def _check_multiple_incidents(
        db: Session,
        entity_name: str,
        task_category: Optional[str] = None
    ) -> List[Dict]:
        """
        Check for multiple incidents trigger.
        
        Returns suggestions for:
        - Recurring incidents of the same type
        - Multiple incidents within short timeframe
        - Incident response pattern
        """
        suggestions = []
        
        try:
            now = datetime.now(timezone.utc)
            thirty_days_ago = now - timedelta(days=30)
            
            # Query for incident response tasks
            query = db.query(EntityHistory).filter(
                and_(
                    EntityHistory.entity_name == entity_name,
                    EntityHistory.timestamp >= thirty_days_ago,
                    EntityHistory.task_category == "INCIDENT_RESPONSE"
                )
            )
            
            if task_category:
                query = query.filter(EntityHistory.task_category == task_category)
            
            incidents = query.order_by(EntityHistory.timestamp.desc()).all()
            
            if len(incidents) >= 2:
                # Group by similar task descriptions or categories
                incident_types = {}
                for incident in incidents:
                    # Use task description or category as key
                    key = incident.task_description[:50] if incident.task_description else "Unknown"
                    if key not in incident_types:
                        incident_types[key] = []
                    incident_types[key].append(incident)
                
                # Find recurring incidents
                recurring = {k: v for k, v in incident_types.items() if len(v) >= 2}
                
                if recurring:
                    most_common = max(recurring.items(), key=lambda x: len(x[1]))
                    incident_type, incident_list = most_common
                    
                    suggestions.append({
                        "trigger": "multiple_incidents",
                        "trigger_type": "recurring_incidents",
                        "priority": "high",
                        "icon": "🔄",
                        "title": "Recurring Incidents Detected",
                        "message": f"{len(incident_list)} similar incident(s) occurred in the last 30 days: '{incident_type[:50]}...'",
                        "suggestion": "Recurring incidents indicate systemic issues. Conduct root cause analysis and implement preventive measures.",
                        "action": "view_incidents",
                        "action_label": "View Incident History →",
                        "metadata": {
                            "incident_count": len(incident_list),
                            "incident_type": incident_type,
                            "timeframe": "30_days",
                            "most_recent": incident_list[0].timestamp.isoformat() if incident_list else None
                        }
                    })
                elif len(incidents) >= 3:
                    suggestions.append({
                        "trigger": "multiple_incidents",
                        "trigger_type": "multiple_incidents",
                        "priority": "medium",
                        "icon": "⚠️",
                        "title": "Multiple Incidents in Short Timeframe",
                        "message": f"{len(incidents)} incident response task(s) in the last 30 days.",
                        "suggestion": "High incident frequency may indicate underlying issues. Review incident patterns and strengthen preventive controls.",
                        "action": "view_incident_analysis",
                        "action_label": "View Incident Analysis →",
                        "metadata": {
                            "incident_count": len(incidents),
                            "timeframe": "30_days"
                        }
                    })
        
        except Exception as e:
            logger.error(f"Error checking multiple incidents: {e}")
        
        return suggestions
    
    @staticmethod
    def _check_regulatory_patterns(
        db: Session,
        entity_name: str,
        task_category: Optional[str] = None
    ) -> List[Dict]:
        """
        Check for regulatory patterns trigger.
        
        Returns suggestions for:
        - New regulations affecting entity
        - Regulatory changes in jurisdictions
        - Pattern of regulatory filings
        """
        suggestions = []
        
        try:
            now = datetime.now(timezone.utc)
            ninety_days_ago = now - timedelta(days=90)
            
            # Query for regulatory filing tasks
            query = db.query(EntityHistory).filter(
                and_(
                    EntityHistory.entity_name == entity_name,
                    EntityHistory.timestamp >= ninety_days_ago,
                    EntityHistory.task_category == "REGULATORY_FILING"
                )
            )
            
            if task_category:
                query = query.filter(EntityHistory.task_category == task_category)
            
            regulatory_filings = query.order_by(EntityHistory.timestamp.desc()).all()
            
            # Check for jurisdiction patterns
            jurisdiction_counts = {}
            for filing in regulatory_filings:
                jurisdictions = filing.jurisdictions or []
                for jur in jurisdictions:
                    jurisdiction_counts[jur] = jurisdiction_counts.get(jur, 0) + 1
            
            # Multiple filings in same jurisdiction
            if len(regulatory_filings) >= 3:
                most_active_jurisdiction = max(jurisdiction_counts.items(), key=lambda x: x[1]) if jurisdiction_counts else None
                
                if most_active_jurisdiction and most_active_jurisdiction[1] >= 3:
                    suggestions.append({
                        "trigger": "regulatory_patterns",
                        "trigger_type": "active_jurisdiction",
                        "priority": "medium",
                        "icon": "🌍",
                        "title": "Active Regulatory Jurisdiction",
                        "message": f"{most_active_jurisdiction[1]} regulatory filing(s) in {most_active_jurisdiction[0]} in the last 90 days.",
                        "suggestion": "High regulatory activity in this jurisdiction. Ensure compliance team is up-to-date with latest requirements.",
                        "action": "view_jurisdiction_activity",
                        "action_label": "View Jurisdiction Activity →",
                        "metadata": {
                            "jurisdiction": most_active_jurisdiction[0],
                            "filing_count": most_active_jurisdiction[1],
                            "total_filings": len(regulatory_filings),
                            "timeframe": "90_days"
                        }
                    })
            
            # Check for regulatory changes (indicated in metadata)
            regulatory_changes = []
            for filing in regulatory_filings:
                metadata = filing.meta_data or {}
                if metadata.get('regulatory_change') or metadata.get('new_regulation'):
                    regulatory_changes.append(filing)
            
            if len(regulatory_changes) >= 1:
                suggestions.append({
                    "trigger": "regulatory_patterns",
                    "trigger_type": "regulatory_changes",
                    "priority": "high",
                    "icon": "📜",
                    "title": "Regulatory Changes Detected",
                    "message": f"{len(regulatory_changes)} regulatory change(s) affecting your organization.",
                    "suggestion": "New regulations may require policy updates or process changes. Review changes and update compliance procedures.",
                    "action": "view_regulatory_changes",
                    "action_label": "View Regulatory Changes →",
                    "metadata": {
                        "change_count": len(regulatory_changes),
                        "timeframe": "90_days"
                    }
                })
        
        except Exception as e:
            logger.error(f"Error checking regulatory patterns: {e}")
        
        return suggestions
    
    # Legacy method for backward compatibility
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
        Generate proactive suggestions (legacy method).
        
        This method calls check_triggers and adds additional context-based suggestions.
        """
        # Get trigger-based suggestions
        suggestions = ProactiveSuggestionService.check_triggers(
            db, entity_name, task_category
        )
        
        # Add context-based suggestions
        if has_deadline:
            # Check if deadline is missing from suggestions
            has_deadline_suggestion = any(s.get("trigger") == "deadlines" for s in suggestions)
            if not has_deadline_suggestion:
                suggestions.append({
                    "trigger": "deadlines",
                    "trigger_type": "deadline_present",
                    "priority": "low",
                    "icon": "📅",
                    "title": "Deadline Present",
                    "message": "This task has a regulatory deadline.",
                    "suggestion": "Ensure adequate time is allocated for review and completion.",
                    "action": "none",
                    "action_label": None
                })
        
        return suggestions


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
