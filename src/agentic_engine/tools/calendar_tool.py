"""
Calendar Tool Module

Provides calendar and deadline management capabilities.
Calculates deadlines, urgency scores, and compliance timing.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re


class CalendarTool:
    """
    Tool for managing compliance calendars and deadlines.
    
    Provides:
    - Deadline calculation from various input formats
    - Urgency score calculation based on time remaining
    - Business day calculations
    - Compliance deadline tracking
    """
    
    def __init__(self):
        """Initialize calendar tool."""
        pass
    
    def calculate_deadline(
        self,
        base_date: Optional[str] = None,
        days_ahead: Optional[int] = None,
        deadline_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate deadline from various inputs.
        
        Args:
            base_date: Base date in ISO format (YYYY-MM-DD)
            days_ahead: Number of days ahead from base_date
            deadline_text: Natural language deadline (e.g., "30 days", "Q4 2024")
            
        Returns:
            Dictionary with calculated deadline and metadata
        """
        try:
            # Determine base date
            if base_date:
                start = datetime.fromisoformat(base_date.replace('Z', '+00:00'))
            else:
                start = datetime.utcnow()
            
            # Calculate deadline based on inputs
            if days_ahead is not None:
                deadline = start + timedelta(days=days_ahead)
                method = f"{days_ahead} days from {start.date()}"
            
            elif deadline_text:
                # Parse natural language deadline
                parsed_days = self._parse_deadline_text(deadline_text)
                if parsed_days:
                    deadline = start + timedelta(days=parsed_days)
                    method = f"Parsed '{deadline_text}' as {parsed_days} days"
                else:
                    # Try to parse as date
                    try:
                        deadline = datetime.fromisoformat(deadline_text)
                        method = f"Direct date: {deadline_text}"
                    except:
                        # Default to 30 days
                        deadline = start + timedelta(days=30)
                        method = f"Could not parse '{deadline_text}', defaulted to 30 days"
            
            else:
                # Default: 30 days ahead
                deadline = start + timedelta(days=30)
                method = "Default 30 days from now"
            
            # Calculate days remaining
            days_remaining = (deadline - datetime.utcnow()).days
            
            return {
                "deadline": deadline.isoformat(),
                "deadline_date": deadline.strftime("%Y-%m-%d"),
                "days_remaining": days_remaining,
                "calculation_method": method,
                "is_past_due": days_remaining < 0,
                "urgency": self._calculate_urgency_score(days_remaining)
            }
            
        except Exception as e:
            return {
                "error": f"Failed to calculate deadline: {str(e)}",
                "deadline": None,
                "days_remaining": None
            }
    
    def calculate_urgency_score(
        self,
        deadline: str,
        task_category: str = "GENERAL_INQUIRY"
    ) -> Dict[str, Any]:
        """
        Calculate urgency score for a task based on deadline and category.
        
        Args:
            deadline: Deadline in ISO format or natural language
            task_category: Task category for risk weighting
            
        Returns:
            Dictionary with urgency score and categorization
        """
        try:
            # Parse deadline
            try:
                deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            except:
                # Try to calculate from text
                calc_result = self.calculate_deadline(deadline_text=deadline)
                if calc_result.get('deadline'):
                    deadline_dt = datetime.fromisoformat(calc_result['deadline'])
                else:
                    return {"error": "Could not parse deadline", "urgency_score": 0.5}
            
            # Calculate days remaining
            days_remaining = (deadline_dt - datetime.utcnow()).days
            
            # Base urgency from time remaining
            base_urgency = self._calculate_urgency_score(days_remaining)
            
            # Apply task category multiplier
            category_multipliers = {
                "REGULATORY_FILING": 1.3,
                "INCIDENT_RESPONSE": 1.4,
                "FINANCIAL_REPORTING": 1.2,
                "DATA_PRIVACY": 1.1,
                "GENERAL_INQUIRY": 0.8
            }
            
            multiplier = category_multipliers.get(task_category, 1.0)
            final_urgency = min(base_urgency * multiplier, 1.0)
            
            # Categorize urgency
            if final_urgency >= 0.8:
                urgency_level = "CRITICAL"
            elif final_urgency >= 0.6:
                urgency_level = "HIGH"
            elif final_urgency >= 0.4:
                urgency_level = "MEDIUM"
            else:
                urgency_level = "LOW"
            
            return {
                "urgency_score": round(final_urgency, 2),
                "urgency_level": urgency_level,
                "days_remaining": days_remaining,
                "deadline": deadline_dt.isoformat(),
                "task_category": task_category,
                "is_overdue": days_remaining < 0,
                "recommendations": self._get_urgency_recommendations(urgency_level, days_remaining)
            }
            
        except Exception as e:
            return {
                "error": f"Failed to calculate urgency: {str(e)}",
                "urgency_score": 0.5,
                "urgency_level": "MEDIUM"
            }
    
    def _calculate_urgency_score(self, days_remaining: int) -> float:
        """
        Calculate base urgency score from days remaining.
        
        Args:
            days_remaining: Number of days until deadline
            
        Returns:
            Urgency score (0.0 to 1.0)
        """
        if days_remaining < 0:
            return 1.0  # Overdue - critical
        elif days_remaining <= 3:
            return 0.95  # 3 days or less - critical
        elif days_remaining <= 7:
            return 0.85  # 1 week - high urgency
        elif days_remaining <= 14:
            return 0.70  # 2 weeks - high urgency
        elif days_remaining <= 30:
            return 0.55  # 1 month - medium urgency
        elif days_remaining <= 60:
            return 0.35  # 2 months - medium-low urgency
        else:
            return 0.20  # More than 2 months - low urgency
    
    def _parse_deadline_text(self, text: str) -> Optional[int]:
        """
        Parse natural language deadline text into days.
        
        Args:
            text: Natural language deadline (e.g., "30 days", "2 weeks", "1 month")
            
        Returns:
            Number of days, or None if cannot parse
        """
        text_lower = text.lower()
        
        # Pattern: "X days"
        match = re.search(r'(\d+)\s*days?', text_lower)
        if match:
            return int(match.group(1))
        
        # Pattern: "X weeks"
        match = re.search(r'(\d+)\s*weeks?', text_lower)
        if match:
            return int(match.group(1)) * 7
        
        # Pattern: "X months"
        match = re.search(r'(\d+)\s*months?', text_lower)
        if match:
            return int(match.group(1)) * 30
        
        # Pattern: "X years"
        match = re.search(r'(\d+)\s*years?', text_lower)
        if match:
            return int(match.group(1)) * 365
        
        # Common phrases
        if 'tomorrow' in text_lower:
            return 1
        if 'next week' in text_lower:
            return 7
        if 'next month' in text_lower:
            return 30
        if 'quarter' in text_lower or 'q1' in text_lower or 'q2' in text_lower:
            return 90
        
        return None
    
    def _get_urgency_recommendations(self, urgency_level: str, days_remaining: int) -> List[str]:
        """Get recommendations based on urgency level."""
        if urgency_level == "CRITICAL":
            return [
                "Immediate action required",
                "Escalate to compliance team",
                "Review all requirements today",
                "Prepare emergency response if overdue"
            ]
        elif urgency_level == "HIGH":
            return [
                "Prioritize this task",
                "Schedule immediate review",
                "Allocate dedicated resources",
                "Daily progress monitoring"
            ]
        elif urgency_level == "MEDIUM":
            return [
                "Include in weekly planning",
                "Assign to compliance team",
                "Begin preliminary review",
                "Monitor regularly"
            ]
        else:
            return [
                "Add to backlog",
                "Review in monthly planning",
                "No immediate action needed"
            ]
    
    def get_deadlines(
        self,
        entity_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve deadlines for a given entity and date range.
        
        Args:
            entity_id: Entity identifier
            start_date: Start of date range (ISO format)
            end_date: End of date range (ISO format)
            
        Returns:
            List of deadlines (placeholder - would query database in production)
        """
        # Placeholder - would query database in production
        return [{
            "message": "Deadline retrieval not yet implemented",
            "entity_id": entity_id,
            "start_date": start_date,
            "end_date": end_date,
            "note": "This would query the compliance calendar database"
        }]
    
    def add_deadline(
        self,
        entity_id: str,
        deadline_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add a new deadline to the calendar.
        
        Args:
            entity_id: Entity identifier
            deadline_data: Deadline information
            
        Returns:
            Created deadline record (placeholder - would write to database)
        """
        # Placeholder - would write to database in production
        return {
            "message": "Deadline creation not yet implemented",
            "entity_id": entity_id,
            "deadline_data": deadline_data,
            "note": "This would create a deadline in the compliance calendar database"
        }

