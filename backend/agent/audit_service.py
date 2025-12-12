"""Audit trail service for logging agent decisions"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.db.models import AuditTrail
from backend.agent.risk_models import DecisionAnalysis

logger = logging.getLogger(__name__)


class AuditService:
    """Service for logging and retrieving agent decisions in audit trail"""
    
    # System prompt patterns to detect and filter out
    SYSTEM_PROMPT_PATTERNS = [
        "you are helping a user",
        "you are an expert compliance",
        "you are an expert compliance analyst",
        "you are a helpful ai assistant",
        "your role is to",
        "system:",
        "assistant:",
        "current page:",
        "entity:",
        "task:",
        "recent decision:",
        "form context:",
        "please provide a clear",
        "based on the context above",
    ]
    
    @staticmethod
    def _is_system_prompt(text: str) -> bool:
        """Check if text looks like a system prompt rather than user input."""
        if not text:
            return False
        text_lower = text.lower().strip()
        # Check if it starts with system prompt patterns
        if any(text_lower.startswith(pattern) for pattern in ["you are", "system:", "your role", "current page:"]):
            return True
        # Check if it contains multiple system prompt indicators (likely a combined prompt)
        pattern_count = sum(1 for pattern in AuditService.SYSTEM_PROMPT_PATTERNS if pattern in text_lower)
        return pattern_count >= 2  # If 2+ patterns found, it's likely a system prompt
    
    @staticmethod
    def _extract_user_task(text: str) -> str:
        """Extract the user's actual task from a combined system+user prompt."""
        if not text:
            return "Unknown task"
        
        text_lower = text.lower()
        
        # Common patterns for where user content starts
        markers = [
            "user question:",
            "user query:",
            "current query:",
            "query:",
            "task:",
            "analyze compliance task for",
        ]
        
        # Try to find the user's actual question
        for marker in markers:
            if marker in text_lower:
                idx = text_lower.index(marker) + len(marker)
                extracted = text[idx:].strip()
                # Clean up common trailing phrases
                for trailing in ["please provide", "based on", "explain", "help"]:
                    if extracted.lower().startswith(trailing):
                        # Try to find the actual question after these phrases
                        trailing_idx = extracted.lower().index(trailing) + len(trailing)
                        extracted = extracted[trailing_idx:].strip()
                        if extracted.startswith("a "):
                            extracted = extracted[2:].strip()
                # If we found meaningful content, return it
                if len(extracted) > 10:
                    return extracted[:500] if len(extracted) > 500 else extracted
        
        # If text starts with system prompt, try to extract from the end
        if text_lower.startswith(("you are", "system:", "your role")):
            # Look for "User Question:" or similar near the end
            for marker in ["user question:", "user query:", "query:"]:
                if marker in text_lower:
                    idx = text_lower.index(marker) + len(marker)
                    extracted = text[idx:].strip()
                    if len(extracted) > 10:
                        return extracted[:500] if len(extracted) > 500 else extracted
            return "Compliance query"
        
        # Otherwise, return the text as-is (but limit length)
        return text[:500] if len(text) > 500 else text
    
    @staticmethod
    def _validate_audit_entry(entry_data: dict) -> dict:
        """Ensure all required fields have values"""
        required_fields = {
            "entity_name": "Unknown Entity",
            "task_description": "No description",
            "decision_outcome": "REVIEW_REQUIRED",
            "risk_level": "MEDIUM",
            "confidence_score": 0.5,
            "agent_type": "decision_engine",
            "reasoning_chain": []
        }
        
        for field, default in required_fields.items():
            # Check if field is missing or None (but allow 0 for numeric fields)
            if field not in entry_data or entry_data[field] is None:
                logger.warning(f"Audit entry missing {field}, using default: {default}")
                entry_data[field] = default
            # For string fields, also check if empty string
            elif isinstance(default, str) and not entry_data[field]:
                logger.warning(f"Audit entry has empty {field}, using default: {default}")
                entry_data[field] = default
        
        return entry_data
    
    @staticmethod
    def log_decision_analysis(
        db: Session,
        analysis: DecisionAnalysis,
        agent_type: str = "decision_engine",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditTrail:
        """
        Log a decision analysis to the audit trail
        
        Args:
            db: Database session
            analysis: DecisionAnalysis object containing full decision details
            agent_type: Type of agent making the decision (decision_engine, openai_agent)
            metadata: Additional metadata to store
            
        Returns:
            AuditTrail object that was created
        """
        # Extract risk factors as dict
        risk_factors_dict = {
            "jurisdiction_risk": analysis.risk_factors.jurisdiction_risk,
            "entity_risk": analysis.risk_factors.entity_risk,
            "task_risk": analysis.risk_factors.task_risk,
            "data_sensitivity_risk": analysis.risk_factors.data_sensitivity_risk,
            "regulatory_risk": analysis.risk_factors.regulatory_risk,
            "impact_risk": analysis.risk_factors.impact_risk,
            "overall_score": analysis.risk_factors.overall_score
        }
        
        # Prepare entry data
        entry_data = {
            "timestamp": analysis.timestamp,
            "agent_type": agent_type,
            "task_description": analysis.task_context.description,
            "task_category": analysis.task_context.category.value,
            "entity_name": analysis.entity_context.name,
            "entity_type": analysis.entity_context.entity_type.value,
            "decision_outcome": analysis.decision.value,
            "confidence_score": analysis.confidence,
            "risk_level": analysis.risk_level.value,
            "risk_score": analysis.risk_factors.overall_score,
            "reasoning_chain": analysis.reasoning,
            "risk_factors": risk_factors_dict,
            "recommendations": analysis.recommendations,
            "escalation_reason": analysis.escalation_reason,
            "entity_context": analysis.entity_context.model_dump(mode='json'),
            "task_context": analysis.task_context.model_dump(mode='json'),
            "meta_data": metadata or {}
        }
        
        # Validate entry data
        validated_data = AuditService._validate_audit_entry(entry_data)
        
        # Log what's being saved
        logger.info(f"Creating audit entry: entity={validated_data.get('entity_name')}, decision={validated_data.get('decision_outcome')}")
        
        # Create audit trail entry
        audit_entry = AuditTrail(**validated_data)
        
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        
        return audit_entry
    
    @staticmethod
    def log_custom_decision(
        db: Session,
        task_description: str,
        decision_outcome: str,
        confidence_score: float,
        reasoning_chain: List[str],
        agent_type: str = "openai_agent",
        task_category: Optional[str] = None,
        entity_name: Optional[str] = None,
        entity_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        risk_score: Optional[float] = None,
        risk_factors: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[str]] = None,
        escalation_reason: Optional[str] = None,
        entity_context: Optional[Dict[str, Any]] = None,
        task_context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditTrail:
        """
        Log a custom decision to the audit trail (for non-DecisionAnalysis scenarios)
        
        Args:
            db: Database session
            task_description: Description of the task
            decision_outcome: Decision made (e.g., AUTONOMOUS, REVIEW_REQUIRED, ESCALATE)
            confidence_score: Confidence in the decision (0-1)
            reasoning_chain: List of reasoning steps
            agent_type: Type of agent making the decision
            task_category: Category of the task
            entity_name: Name of the entity
            entity_type: Type of entity
            risk_level: Risk level (LOW, MEDIUM, HIGH)
            risk_score: Numeric risk score (0-1)
            risk_factors: Dictionary of risk factors
            recommendations: List of recommendations
            escalation_reason: Reason for escalation if applicable
            entity_context: Full entity context
            task_context: Full task context
            metadata: Additional metadata
            
        Returns:
            AuditTrail object that was created
        """
        # Filter out system prompts - use original task from metadata if available
        original_task_description = (metadata or {}).get("original_task_description") if metadata else None
        
        if AuditService._is_system_prompt(task_description):
            if original_task_description:
                task_description = original_task_description
            else:
                # Try to extract user task from the prompt
                task_description = AuditService._extract_user_task(task_description)
        
        # Prepare entry data
        entry_data = {
            "timestamp": datetime.utcnow(),
            "agent_type": agent_type,
            "task_description": task_description,
            "task_category": task_category,
            "entity_name": entity_name,
            "entity_type": entity_type,
            "decision_outcome": decision_outcome,
            "confidence_score": confidence_score,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "reasoning_chain": reasoning_chain,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "escalation_reason": escalation_reason,
            "entity_context": entity_context,
            "task_context": task_context,
            "meta_data": metadata or {}
        }
        
        # Validate entry data
        validated_data = AuditService._validate_audit_entry(entry_data)
        
        # Log what's being saved
        logger.info(f"Creating audit entry: entity={validated_data.get('entity_name')}, decision={validated_data.get('decision_outcome')}")
        
        # Create audit trail entry
        audit_entry = AuditTrail(**validated_data)
        
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        
        return audit_entry
    
    @staticmethod
    def get_audit_trail(
        db: Session,
        limit: int = 100,
        offset: int = 0,
        agent_type: Optional[str] = None,
        entity_name: Optional[str] = None,
        decision_outcome: Optional[str] = None,
        risk_level: Optional[str] = None,
        task_category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditTrail]:
        """
        Retrieve audit trail entries with optional filters
        
        Args:
            db: Database session
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            agent_type: Filter by agent type
            entity_name: Filter by entity name
            decision_outcome: Filter by decision outcome
            risk_level: Filter by risk level
            task_category: Filter by task category
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            
        Returns:
            List of AuditTrail objects
        """
        query = db.query(AuditTrail)
        
        # Apply filters
        if agent_type:
            query = query.filter(AuditTrail.agent_type == agent_type)
        if entity_name:
            query = query.filter(AuditTrail.entity_name == entity_name)
        if decision_outcome:
            query = query.filter(AuditTrail.decision_outcome == decision_outcome)
        if risk_level:
            query = query.filter(AuditTrail.risk_level == risk_level)
        if task_category:
            query = query.filter(AuditTrail.task_category == task_category)
        if start_date:
            query = query.filter(AuditTrail.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditTrail.timestamp <= end_date)
        
        # Order by timestamp descending (newest first)
        query = query.order_by(AuditTrail.timestamp.desc())
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    @staticmethod
    def get_audit_entry(db: Session, audit_id: int) -> Optional[AuditTrail]:
        """
        Retrieve a specific audit trail entry by ID
        
        Args:
            db: Database session
            audit_id: ID of the audit entry
            
        Returns:
            AuditTrail object or None if not found
        """
        return db.query(AuditTrail).filter(AuditTrail.id == audit_id).first()
    
    @staticmethod
    def get_audit_statistics(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about audit trail entries
        
        Args:
            db: Database session
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            
        Returns:
            Dictionary containing statistics
        """
        query = db.query(AuditTrail)
        
        if start_date:
            query = query.filter(AuditTrail.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditTrail.timestamp <= end_date)
        
        all_entries = query.all()
        total_count = len(all_entries)
        
        if total_count == 0:
            return {
                "total_decisions": 0,
                "by_outcome": {},
                "by_risk_level": {},
                "by_agent_type": {},
                "by_task_category": {},
                "average_confidence": 0,
                "average_risk_score": 0
            }
        
        # Count by decision outcome
        by_outcome = {}
        by_risk_level = {}
        by_agent_type = {}
        by_task_category = {}
        total_confidence = 0
        total_risk_score = 0
        risk_score_count = 0
        
        for entry in all_entries:
            # Count outcomes
            by_outcome[entry.decision_outcome] = by_outcome.get(entry.decision_outcome, 0) + 1
            
            # Count risk levels
            if entry.risk_level:
                by_risk_level[entry.risk_level] = by_risk_level.get(entry.risk_level, 0) + 1
            
            # Count agent types
            by_agent_type[entry.agent_type] = by_agent_type.get(entry.agent_type, 0) + 1
            
            # Count task categories
            if entry.task_category:
                by_task_category[entry.task_category] = by_task_category.get(entry.task_category, 0) + 1
            
            # Sum confidence and risk scores
            total_confidence += entry.confidence_score
            if entry.risk_score is not None:
                total_risk_score += entry.risk_score
                risk_score_count += 1
        
        from datetime import datetime
        return {
            "total_decisions": total_count,
            "high_risk_count": by_risk_level.get("HIGH", 0),
            "medium_risk_count": by_risk_level.get("MEDIUM", 0),
            "low_risk_count": by_risk_level.get("LOW", 0),
            "autonomous_count": by_outcome.get("AUTONOMOUS", 0),
            "review_required_count": by_outcome.get("REVIEW_REQUIRED", 0),
            "escalate_count": by_outcome.get("ESCALATE", 0),
            "by_outcome": by_outcome,
            "by_risk_level": by_risk_level,
            "by_agent_type": by_agent_type,
            "by_task_category": by_task_category,
            "average_confidence": total_confidence / total_count if total_count > 0 else 0,
            "average_risk_score": total_risk_score / risk_score_count if risk_score_count > 0 else 0,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def export_audit_trail_json(
        db: Session,
        limit: Optional[int] = None,
        **filters
    ) -> List[Dict[str, Any]]:
        """
        Export audit trail entries as JSON-serializable dictionaries
        
        Args:
            db: Database session
            limit: Maximum number of entries to export
            **filters: Additional filters to apply
            
        Returns:
            List of dictionaries representing audit trail entries
        """
        entries = AuditService.get_audit_trail(
            db,
            limit=limit or 1000,
            **filters
        )
        
        return [entry.to_dict() for entry in entries]
    
    @staticmethod
    def log_agentic_loop_output(
        db: Session,
        entity_name: str,
        task_description: str,
        agent_loop_result: Dict[str, Any],
        agent_type: str = "agentic_engine",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditTrail:
        """
        Log agentic loop execution output to audit trail.
        
        Args:
            db: Database session
            entity_name: Name of the entity
            task_description: Description of the task
            agent_loop_result: Complete agent loop result dictionary
            agent_type: Type of agent (default: "agentic_engine")
            metadata: Additional metadata
        
        Returns:
            AuditTrail object that was created
        """
        # Prefer original task description from metadata if the provided text looks like a system prompt
        meta = metadata or {}
        original_task_description = meta.get("original_task_description")
        if task_description and "you are helping a user" in task_description.lower() and original_task_description:
            task_description = original_task_description

        # Extract key information from agent loop result
        plan = agent_loop_result.get("plan", [])
        step_outputs = agent_loop_result.get("step_outputs", [])
        reflections = agent_loop_result.get("reflections", [])
        risk_assessment = agent_loop_result.get("risk_assessment", {})
        recommendation = agent_loop_result.get("recommendation", "")
        metrics = agent_loop_result.get("metrics", {})
        audit_log = agent_loop_result.get("audit_log", {})
        
        # Determine decision outcome from recommendation or risk assessment
        decision_outcome = "REVIEW_REQUIRED"  # Default
        risk_level = risk_assessment.get("level", "MEDIUM")
        
        if risk_level == "LOW":
            decision_outcome = "AUTONOMOUS"
        elif risk_level == "HIGH":
            decision_outcome = "ESCALATE"
        
        # Calculate confidence from reflections
        confidence_score = 0.7  # Default
        if reflections:
            avg_quality = sum(r.get("overall_quality", 0.7) for r in reflections) / len(reflections)
            confidence_score = avg_quality
        
        # Build reasoning chain
        reasoning_chain = []
        reasoning_chain.append(f"Agentic loop executed with {len(plan)} plan steps")
        reasoning_chain.append(f"Completed {len(step_outputs)} execution steps")
        reasoning_chain.append(f"Performed {len(reflections)} reflection evaluations")
        
        if agent_loop_result.get("revised_plan"):
            reasoning_chain.append("Plan was revised during execution")
        
        if risk_assessment:
            reasoning_chain.append(f"Risk assessment: {risk_level} (score: {risk_assessment.get('score', 0.0):.2f})")
        
        reasoning_chain.append(f"Final recommendation: {recommendation}")
        
        # Extract risk factors if available
        risk_factors = None
        if risk_assessment:
            risk_factors = {
                "risk_level": risk_assessment.get("level"),
                "risk_score": risk_assessment.get("score"),
                "risk_factors": risk_assessment.get("factors", [])
            }
        
        # Build comprehensive metadata
        comprehensive_metadata = {
            "agent_type": agent_type,
            "plan_steps": len(plan),
            "execution_steps": len(step_outputs),
            "reflections": len(reflections),
            "replan_count": metrics.get("replan_count", 0),
            "total_execution_time": metrics.get("total_workflow_time", 0.0),
            "success": agent_loop_result.get("success", False),
            "tool_outputs_count": len(agent_loop_result.get("tool_outputs", [])),
            "audit_log": audit_log,
            **meta
        }
        
        # Filter out system prompts - use original task from metadata if available
        original_task_description = meta.get("original_task_description") if meta else None
        
        if AuditService._is_system_prompt(task_description):
            if original_task_description:
                task_description = original_task_description
            else:
                # Try to extract user task from the prompt
                task_description = AuditService._extract_user_task(task_description)
        
        # Prepare entry data
        entry_data = {
            "timestamp": datetime.now(timezone.utc),
            "agent_type": agent_type,
            "task_description": task_description,
            "task_category": None,  # Could extract from task if available
            "entity_name": entity_name,
            "entity_type": None,
            "decision_outcome": decision_outcome,
            "confidence_score": confidence_score,
            "risk_level": risk_level,
            "risk_score": risk_assessment.get("score") if risk_assessment else None,
            "reasoning_chain": reasoning_chain,
            "risk_factors": risk_factors,
            "recommendations": [recommendation] if recommendation else None,
            "escalation_reason": None,
            "entity_context": {"entity_name": entity_name},
            "task_context": {"task_description": task_description},
            "meta_data": comprehensive_metadata
        }
        
        # Validate entry data
        validated_data = AuditService._validate_audit_entry(entry_data)
        
        # Log what's being saved
        logger.info(f"Creating audit entry: entity={validated_data.get('entity_name')}, decision={validated_data.get('decision_outcome')}")
        
        # Create audit trail entry
        audit_entry = AuditTrail(**validated_data)
        
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        
        return audit_entry

