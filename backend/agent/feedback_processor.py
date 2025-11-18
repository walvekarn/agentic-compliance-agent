"""
Feedback Processor Module

Processes human feedback to update memory and adjust thresholds.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from backend.db.models import FeedbackLog, MemoryRecord
from backend.agentic_engine.memory.memory_store import MemoryStore


class FeedbackProcessor:
    """Processes feedback to update memory and thresholds"""
    
    def __init__(self, db_session: Session):
        """
        Initialize feedback processor.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
        self.memory_store = MemoryStore()
    
    def process_feedback(
        self,
        feedback: FeedbackLog,
        update_memory: bool = True,
        update_thresholds: bool = True
    ) -> Dict[str, Any]:
        """
        Process feedback to update memory and thresholds.
        
        Args:
            feedback: FeedbackLog entry
            update_memory: Whether to update memory
            update_thresholds: Whether to update thresholds
        
        Returns:
            Dictionary with processing results
        """
        results = {
            "memory_updated": False,
            "thresholds_updated": False,
            "memory_key": None,
            "threshold_adjustments": {}
        }
        
        # Update memory if feedback indicates disagreement
        if update_memory and feedback.is_agreement == 0:
            memory_result = self._update_memory_from_feedback(feedback)
            results["memory_updated"] = memory_result["success"]
            results["memory_key"] = memory_result.get("memory_key")
        
        # Update thresholds based on feedback patterns
        if update_thresholds:
            threshold_result = self._update_thresholds_from_feedback(feedback)
            results["thresholds_updated"] = threshold_result["success"]
            results["threshold_adjustments"] = threshold_result.get("adjustments", {})
        
        return results
    
    def _update_memory_from_feedback(self, feedback: FeedbackLog) -> Dict[str, Any]:
        """Update memory based on feedback."""
        try:
            # Create memory entry for override pattern
            memory_key = f"feedback_override_{feedback.feedback_id}"
            
            memory_content = {
                "feedback_id": feedback.feedback_id,
                "entity_name": feedback.entity_name,
                "task_description": feedback.task_description,
                "ai_decision": feedback.ai_decision,
                "human_decision": feedback.human_decision,
                "override_reason": feedback.notes,
                "timestamp": feedback.timestamp.isoformat() if feedback.timestamp else None,
                "audit_trail_id": feedback.audit_trail_id
            }
            
            # Store in memory
            memory_record = MemoryRecord(
                memory_key=memory_key,
                memory_type="episodic",
                content=memory_content,
                summary=f"Override: AI suggested {feedback.ai_decision}, human chose {feedback.human_decision}",
                entity_name=feedback.entity_name,
                task_category=None,  # Could extract from task_description
                importance_score=0.8,  # High importance for overrides
                meta_data={
                    "feedback_id": feedback.feedback_id,
                    "is_override": True,
                    "override_type": self._classify_override_type(feedback)
                }
            )
            
            self.db.add(memory_record)
            self.db.commit()
            
            return {
                "success": True,
                "memory_key": memory_key
            }
        
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _update_thresholds_from_feedback(self, feedback: FeedbackLog) -> Dict[str, Any]:
        """Update thresholds based on feedback patterns."""
        try:
            adjustments = {}
            
            # Analyze feedback patterns to suggest threshold adjustments
            if feedback.is_agreement == 0:
                # Get recent feedback for same entity/task pattern
                recent_feedback = self.db.query(FeedbackLog).filter(
                    FeedbackLog.entity_name == feedback.entity_name,
                    FeedbackLog.is_agreement == 0
                ).order_by(FeedbackLog.timestamp.desc()).limit(10).all()
                
                if len(recent_feedback) >= 3:
                    # Analyze override patterns
                    ai_decision_counts = {}
                    human_decision_counts = {}
                    
                    for fb in recent_feedback:
                        ai_decision_counts[fb.ai_decision] = ai_decision_counts.get(fb.ai_decision, 0) + 1
                        human_decision_counts[fb.human_decision] = human_decision_counts.get(fb.human_decision, 0) + 1
                    
                    # If AI is consistently too conservative (AUTONOMOUS -> REVIEW_REQUIRED)
                    if ai_decision_counts.get("AUTONOMOUS", 0) > 0:
                        autonomous_overrides = sum(1 for fb in recent_feedback 
                                                  if fb.ai_decision == "AUTONOMOUS" and fb.human_decision != "AUTONOMOUS")
                        if autonomous_overrides >= 2:
                            adjustments["suggest_lower_autonomous_threshold"] = True
                    
                    # If AI is consistently too aggressive (ESCALATE -> REVIEW_REQUIRED)
                    if ai_decision_counts.get("ESCALATE", 0) > 0:
                        escalate_overrides = sum(1 for fb in recent_feedback 
                                                if fb.ai_decision == "ESCALATE" and fb.human_decision != "ESCALATE")
                        if escalate_overrides >= 2:
                            adjustments["suggest_lower_escalate_threshold"] = True
                    
                    # Store threshold suggestions in metadata
                    if adjustments:
                        # Update feedback metadata with threshold suggestions
                        if feedback.meta_data is None:
                            feedback.meta_data = {}
                        feedback.meta_data["threshold_suggestions"] = adjustments
                        self.db.commit()
            
            return {
                "success": True,
                "adjustments": adjustments
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "adjustments": {}
            }
    
    def _classify_override_type(self, feedback: FeedbackLog) -> str:
        """Classify the type of override."""
        ai = feedback.ai_decision
        human = feedback.human_decision
        
        if ai == "AUTONOMOUS" and human == "REVIEW_REQUIRED":
            return "too_conservative"
        elif ai == "AUTONOMOUS" and human == "ESCALATE":
            return "too_aggressive"
        elif ai == "REVIEW_REQUIRED" and human == "AUTONOMOUS":
            return "too_cautious"
        elif ai == "REVIEW_REQUIRED" and human == "ESCALATE":
            return "underestimated_risk"
        elif ai == "ESCALATE" and human == "REVIEW_REQUIRED":
            return "overestimated_risk"
        elif ai == "ESCALATE" and human == "AUTONOMOUS":
            return "too_restrictive"
        else:
            return "unknown"
    
    def get_override_statistics(
        self,
        entity_name: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get override statistics.
        
        Args:
            entity_name: Optional entity name filter
            days: Number of days to look back
        
        Returns:
            Dictionary with override statistics
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = self.db.query(FeedbackLog).filter(
            FeedbackLog.is_agreement == 0,
            FeedbackLog.timestamp >= cutoff_date
        )
        
        if entity_name:
            query = query.filter(FeedbackLog.entity_name == entity_name)
        
        overrides = query.all()
        
        override_types = {}
        for override in overrides:
            override_type = self._classify_override_type(override)
            override_types[override_type] = override_types.get(override_type, 0) + 1
        
        return {
            "total_overrides": len(overrides),
            "override_breakdown": override_types,
            "timeframe_days": days,
            "entity_name": entity_name
        }

