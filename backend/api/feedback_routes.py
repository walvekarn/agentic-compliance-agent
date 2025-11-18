"""API routes for human feedback on AI decisions"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta

from backend.db.base import get_db
from backend.db.models import FeedbackLog
from backend.auth.security import get_current_user
from backend.agent.feedback_processor import FeedbackProcessor

router = APIRouter(tags=["Feedback", "Protected"], dependencies=[Depends(get_current_user)])


# Request/Response Models
class FeedbackSubmit(BaseModel):
    """Request model for submitting human feedback"""
    entity_name: Optional[str] = None
    task_description: str
    ai_decision: str  # AUTONOMOUS, REVIEW_REQUIRED, ESCALATE
    human_decision: str  # AUTONOMOUS, REVIEW_REQUIRED, ESCALATE
    notes: Optional[str] = None
    audit_trail_id: Optional[int] = None


class FeedbackResponse(BaseModel):
    """Response model for feedback submission"""
    feedback_id: int
    timestamp: str
    entity_name: Optional[str]
    task_description: str
    ai_decision: str
    human_decision: str
    notes: Optional[str]
    is_agreement: bool
    audit_trail_id: Optional[int]
    
    class Config:
        from_attributes = True


class FeedbackStats(BaseModel):
    """Statistics on AI decision accuracy based on human feedback"""
    total_feedback_count: int
    agreement_count: int
    override_count: int
    accuracy_percent: float
    most_overridden_decision: Optional[str]
    override_breakdown: dict  # {decision_type: override_count}


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(
    feedback: FeedbackSubmit,
    db: Session = Depends(get_db)
):
    """
    Submit human feedback on an AI decision
    
    Args:
        feedback: FeedbackSubmit with decision feedback
        db: Database session
        
    Returns:
        Created feedback entry
    """
    try:
        # Validate decisions are valid values
        valid_decisions = ["AUTONOMOUS", "REVIEW_REQUIRED", "ESCALATE"]
        if feedback.ai_decision not in valid_decisions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid AI decision. Must be one of: {', '.join(valid_decisions)}"
            )
        if feedback.human_decision not in valid_decisions:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid human decision. Must be one of: {', '.join(valid_decisions)}"
            )
        
        # Validate task description is not empty
        if not feedback.task_description or not feedback.task_description.strip():
            raise HTTPException(status_code=400, detail="Task description cannot be empty")
        
        # Calculate agreement
        is_agreement = 1 if feedback.ai_decision == feedback.human_decision else 0
        
        # Create feedback entry
        db_feedback = FeedbackLog(
            entity_name=feedback.entity_name,
            task_description=feedback.task_description.strip(),
            ai_decision=feedback.ai_decision,
            human_decision=feedback.human_decision,
            notes=feedback.notes.strip() if feedback.notes else None,
            is_agreement=is_agreement,
            audit_trail_id=feedback.audit_trail_id
        )
        
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        
        # Process feedback to update memory and thresholds
        if db_feedback.is_agreement == 0:  # Only process overrides
            try:
                processor = FeedbackProcessor(db)
                processing_result = processor.process_feedback(
                    db_feedback,
                    update_memory=True,
                    update_thresholds=True
                )
                # Store processing result in metadata
                if db_feedback.meta_data is None:
                    db_feedback.meta_data = {}
                db_feedback.meta_data["processing_result"] = processing_result
                db.commit()
            except Exception as e:
                # Don't fail feedback submission if processing fails
                print(f"Warning: Feedback processing failed: {e}")
        
        return FeedbackResponse(
            feedback_id=db_feedback.feedback_id,
            timestamp=db_feedback.timestamp.isoformat(),
            entity_name=db_feedback.entity_name,
            task_description=db_feedback.task_description,
            ai_decision=db_feedback.ai_decision,
            human_decision=db_feedback.human_decision,
            notes=db_feedback.notes,
            is_agreement=bool(db_feedback.is_agreement),
            audit_trail_id=db_feedback.audit_trail_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/feedback", response_model=List[FeedbackResponse])
def get_feedback(
    skip: int = 0,
    limit: int = 50,
    entity_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of feedback entries
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        entity_name: Optional filter by entity name
        db: Database session
        
    Returns:
        List of feedback entries
    """
    query = db.query(FeedbackLog)
    
    if entity_name:
        query = query.filter(FeedbackLog.entity_name == entity_name)
    
    feedback_entries = query.order_by(FeedbackLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return [
        FeedbackResponse(
            feedback_id=f.feedback_id,
            timestamp=f.timestamp.isoformat(),
            entity_name=f.entity_name,
            task_description=f.task_description,
            ai_decision=f.ai_decision,
            human_decision=f.human_decision,
            notes=f.notes,
            is_agreement=bool(f.is_agreement),
            audit_trail_id=f.audit_trail_id
        )
        for f in feedback_entries
    ]


@router.get("/feedback/stats", response_model=FeedbackStats)
def get_feedback_stats(db: Session = Depends(get_db)):
    """
    Get statistics on AI decision accuracy based on human feedback
    
    Args:
        db: Database session
        
    Returns:
        Feedback statistics including accuracy and override counts
    """
    try:
        # Total feedback count
        total_count = db.query(func.count(FeedbackLog.feedback_id)).scalar() or 0
        
        if total_count == 0:
            return FeedbackStats(
                total_feedback_count=0,
                agreement_count=0,
                override_count=0,
                accuracy_percent=0.0,
                most_overridden_decision=None,
                override_breakdown={}
            )
        
        # Agreement count (AI was correct)
        agreement_count = db.query(func.count(FeedbackLog.feedback_id)).filter(
            FeedbackLog.is_agreement == 1
        ).scalar() or 0
        
        # Override count (AI was corrected)
        override_count = total_count - agreement_count
        
        # Accuracy percentage
        accuracy_percent = (agreement_count / total_count * 100) if total_count > 0 else 0.0
        
        # Override breakdown by AI decision type
        override_breakdown = {}
        for decision_type in ["AUTONOMOUS", "REVIEW_REQUIRED", "ESCALATE"]:
            override_count_for_type = db.query(func.count(FeedbackLog.feedback_id)).filter(
                FeedbackLog.ai_decision == decision_type,
                FeedbackLog.is_agreement == 0
            ).scalar() or 0
            override_breakdown[decision_type] = override_count_for_type
        
        # Most overridden decision type
        most_overridden = max(override_breakdown, key=override_breakdown.get) if override_breakdown else None
        if most_overridden and override_breakdown[most_overridden] == 0:
            most_overridden = None
        
        return FeedbackStats(
            total_feedback_count=total_count,
            agreement_count=agreement_count,
            override_count=override_count,
            accuracy_percent=round(accuracy_percent, 2),
            most_overridden_decision=most_overridden,
            override_breakdown=override_breakdown
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve feedback stats: {str(e)}"
        )


@router.get("/feedback/{feedback_id}", response_model=FeedbackResponse)
def get_feedback_by_id(feedback_id: int, db: Session = Depends(get_db)):
    """
    Get a specific feedback entry by ID
    
    Args:
        feedback_id: ID of the feedback entry
        db: Database session
        
    Returns:
        Feedback entry
    """
    feedback = db.query(FeedbackLog).filter(FeedbackLog.feedback_id == feedback_id).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback entry not found")
    
    return FeedbackResponse(
        feedback_id=feedback.feedback_id,
        timestamp=feedback.timestamp.isoformat(),
        entity_name=feedback.entity_name,
        task_description=feedback.task_description,
        ai_decision=feedback.ai_decision,
        human_decision=feedback.human_decision,
        notes=feedback.notes,
        is_agreement=bool(feedback.is_agreement),
        audit_trail_id=feedback.audit_trail_id
    )


@router.get("/feedback/overrides", response_model=Dict[str, Any])
def get_override_statistics(
    entity_name: Optional[str] = None,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get override tracking statistics.
    
    Args:
        entity_name: Optional entity name filter
        days: Number of days to look back
        db: Database session
    
    Returns:
        Dictionary with override statistics and tracking information
    """
    try:
        processor = FeedbackProcessor(db)
        stats = processor.get_override_statistics(entity_name, days)
        
        # Get detailed override breakdown
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        query = db.query(FeedbackLog).filter(
            FeedbackLog.is_agreement == 0,
            FeedbackLog.timestamp >= cutoff_date
        )
        
        if entity_name:
            query = query.filter(FeedbackLog.entity_name == entity_name)
        
        overrides = query.order_by(FeedbackLog.timestamp.desc()).all()
        
        # Detailed override list
        override_details = []
        for override in overrides:
            override_type = processor._classify_override_type(override)
            override_details.append({
                "feedback_id": override.feedback_id,
                "timestamp": override.timestamp.isoformat() if override.timestamp else None,
                "entity_name": override.entity_name,
                "task_description": override.task_description[:100] + "..." if len(override.task_description) > 100 else override.task_description,
                "ai_decision": override.ai_decision,
                "human_decision": override.human_decision,
                "override_type": override_type,
                "notes": override.notes,
                "audit_trail_id": override.audit_trail_id
            })
        
        return {
            **stats,
            "override_details": override_details[:50],  # Limit to 50 most recent
            "total_tracked": len(override_details)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve override statistics: {str(e)}"
        )

