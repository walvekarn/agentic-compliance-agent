"""API routes for audit trail management"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from src.agent.audit_service import AuditService
from src.db.base import get_db
from pydantic import BaseModel, Field

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


class AuditQueryParams(BaseModel):
    """Parameters for querying audit trail"""
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of entries to return")
    offset: int = Field(default=0, ge=0, description="Number of entries to skip")
    agent_type: Optional[str] = Field(default=None, description="Filter by agent type")
    entity_name: Optional[str] = Field(default=None, description="Filter by entity name")
    decision_outcome: Optional[str] = Field(default=None, description="Filter by decision outcome")
    risk_level: Optional[str] = Field(default=None, description="Filter by risk level")
    task_category: Optional[str] = Field(default=None, description="Filter by task category")
    start_date: Optional[datetime] = Field(default=None, description="Filter entries after this date")
    end_date: Optional[datetime] = Field(default=None, description="Filter entries before this date")


@router.get("/entries")
async def get_audit_entries(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of entries"),
    offset: int = Query(default=0, ge=0, description="Number of entries to skip"),
    agent_type: Optional[str] = Query(default=None, description="Filter by agent type"),
    entity_name: Optional[str] = Query(default=None, description="Filter by entity name"),
    decision_outcome: Optional[str] = Query(default=None, description="Filter by decision outcome"),
    risk_level: Optional[str] = Query(default=None, description="Filter by risk level"),
    task_category: Optional[str] = Query(default=None, description="Filter by task category"),
    start_date: Optional[datetime] = Query(default=None, description="Filter entries after this date"),
    end_date: Optional[datetime] = Query(default=None, description="Filter entries before this date"),
    db: Session = Depends(get_db)
):
    """
    Retrieve audit trail entries with optional filters
    
    Args:
        limit: Maximum number of entries to return (1-1000)
        offset: Number of entries to skip for pagination
        agent_type: Filter by agent type (e.g., 'decision_engine', 'openai_agent')
        entity_name: Filter by entity name
        decision_outcome: Filter by decision outcome (e.g., 'AUTONOMOUS', 'REVIEW_REQUIRED', 'ESCALATE')
        risk_level: Filter by risk level (e.g., 'LOW', 'MEDIUM', 'HIGH')
        task_category: Filter by task category
        start_date: Filter entries after this date (ISO 8601 format)
        end_date: Filter entries before this date (ISO 8601 format)
        db: Database session
        
    Returns:
        List of audit trail entries as JSON
    """
    try:
        from src.db.models import AuditTrail
        from sqlalchemy import func
        
        # Build base query for counting total matching records
        count_query = db.query(func.count(AuditTrail.audit_id))
        
        # Apply same filters as get_audit_trail
        if agent_type:
            count_query = count_query.filter(AuditTrail.agent_type == agent_type)
        if entity_name:
            count_query = count_query.filter(AuditTrail.entity_name == entity_name)
        if decision_outcome:
            count_query = count_query.filter(AuditTrail.decision_outcome == decision_outcome)
        if risk_level:
            count_query = count_query.filter(AuditTrail.risk_level == risk_level)
        if task_category:
            count_query = count_query.filter(AuditTrail.task_category == task_category)
        if start_date:
            count_query = count_query.filter(AuditTrail.timestamp >= start_date)
        if end_date:
            count_query = count_query.filter(AuditTrail.timestamp <= end_date)
        
        # Get total count of matching records
        total_count = count_query.scalar() or 0
        
        # Get paginated entries
        entries = AuditService.get_audit_trail(
            db=db,
            limit=limit,
            offset=offset,
            agent_type=agent_type,
            entity_name=entity_name,
            decision_outcome=decision_outcome,
            risk_level=risk_level,
            task_category=task_category,
            start_date=start_date,
            end_date=end_date
        )
        
        # Convert to JSON-serializable format
        result = {
            "total_count": total_count,
            "total_returned": len(entries),
            "limit": limit,
            "offset": offset,
            "entries": [entry.to_dict() for entry in entries]
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audit entries: {str(e)}")


@router.get("/entries/{audit_id}")
async def get_audit_entry(
    audit_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a specific audit trail entry by ID
    
    Args:
        audit_id: ID of the audit entry
        db: Database session
        
    Returns:
        Audit trail entry as JSON
    """
    try:
        entry = AuditService.get_audit_entry(db=db, audit_id=audit_id)
        
        if not entry:
            raise HTTPException(status_code=404, detail=f"Audit entry {audit_id} not found")
        
        return entry.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audit entry: {str(e)}")


@router.get("/statistics")
async def get_audit_statistics(
    start_date: Optional[datetime] = Query(default=None, description="Filter entries after this date"),
    end_date: Optional[datetime] = Query(default=None, description="Filter entries before this date"),
    db: Session = Depends(get_db)
):
    """
    Get statistics about audit trail entries
    
    Args:
        start_date: Filter entries after this date (ISO 8601 format)
        end_date: Filter entries before this date (ISO 8601 format)
        db: Database session
        
    Returns:
        Statistics about audit trail entries
    """
    try:
        stats = AuditService.get_audit_statistics(
            db=db,
            start_date=start_date,
            end_date=end_date
        )
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statistics: {str(e)}")


@router.get("/export/json")
async def export_audit_trail(
    limit: int = Query(default=1000, ge=1, le=10000, description="Maximum number of entries to export"),
    agent_type: Optional[str] = Query(default=None, description="Filter by agent type"),
    entity_name: Optional[str] = Query(default=None, description="Filter by entity name"),
    decision_outcome: Optional[str] = Query(default=None, description="Filter by decision outcome"),
    risk_level: Optional[str] = Query(default=None, description="Filter by risk level"),
    task_category: Optional[str] = Query(default=None, description="Filter by task category"),
    start_date: Optional[datetime] = Query(default=None, description="Filter entries after this date"),
    end_date: Optional[datetime] = Query(default=None, description="Filter entries before this date"),
    db: Session = Depends(get_db)
):
    """
    Export audit trail entries as JSON
    
    This endpoint returns a comprehensive JSON export of audit trail entries
    suitable for archiving, analysis, or compliance reporting.
    
    Args:
        limit: Maximum number of entries to export (1-10000)
        agent_type: Filter by agent type
        entity_name: Filter by entity name
        decision_outcome: Filter by decision outcome
        risk_level: Filter by risk level
        task_category: Filter by task category
        start_date: Filter entries after this date
        end_date: Filter entries before this date
        db: Database session
        
    Returns:
        JSON export of audit trail entries
    """
    try:
        entries = AuditService.export_audit_trail_json(
            db=db,
            limit=limit,
            agent_type=agent_type,
            entity_name=entity_name,
            decision_outcome=decision_outcome,
            risk_level=risk_level,
            task_category=task_category,
            start_date=start_date,
            end_date=end_date
        )
        
        result = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_entries": len(entries),
            "filters_applied": {
                "limit": limit,
                "agent_type": agent_type,
                "entity_name": entity_name,
                "decision_outcome": decision_outcome,
                "risk_level": risk_level,
                "task_category": task_category,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "entries": entries
        }
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export audit trail: {str(e)}")


@router.get("/filters")
async def get_available_filters(db: Session = Depends(get_db)):
    """
    Get available filter values for audit trail queries
    
    Returns all unique values for filterable fields to help users
    construct queries.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary of available filter values
    """
    try:
        from src.db.models import AuditTrail
        
        # Get all unique values for filterable fields
        agent_types = [row[0] for row in db.query(AuditTrail.agent_type).distinct().all()]
        decision_outcomes = [row[0] for row in db.query(AuditTrail.decision_outcome).distinct().all()]
        risk_levels = [row[0] for row in db.query(AuditTrail.risk_level).distinct().filter(AuditTrail.risk_level.isnot(None)).all()]
        task_categories = [row[0] for row in db.query(AuditTrail.task_category).distinct().filter(AuditTrail.task_category.isnot(None)).all()]
        
        return {
            "agent_types": sorted(agent_types),
            "decision_outcomes": sorted(decision_outcomes),
            "risk_levels": sorted(risk_levels),
            "task_categories": sorted(task_categories),
            "supported_date_format": "ISO 8601 (e.g., 2024-01-01T00:00:00)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve filter values: {str(e)}")


@router.get("/recent")
async def get_recent_decisions(
    limit: int = Query(default=10, ge=1, le=100, description="Number of recent decisions to return"),
    db: Session = Depends(get_db)
):
    """
    Get the most recent agent decisions
    
    A quick endpoint to view the latest decisions made by the compliance agent.
    
    Args:
        limit: Number of recent decisions to return (1-100)
        db: Database session
        
    Returns:
        List of recent audit trail entries
    """
    try:
        entries = AuditService.get_audit_trail(
            db=db,
            limit=limit,
            offset=0
        )
        
        return {
            "count": len(entries),
            "entries": [entry.to_dict() for entry in entries]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recent decisions: {str(e)}")


@router.get("/entity/{entity_name}")
async def get_audit_by_entity(
    entity_name: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get all audit trail entries for a specific entity
    
    Args:
        entity_name: Name of the entity
        limit: Maximum number of entries to return
        offset: Number of entries to skip
        db: Database session
        
    Returns:
        List of audit trail entries for the specified entity
    """
    try:
        entries = AuditService.get_audit_trail(
            db=db,
            limit=limit,
            offset=offset,
            entity_name=entity_name
        )
        
        if not entries and offset == 0:
            return {
                "message": f"No audit entries found for entity '{entity_name}'",
                "entity_name": entity_name,
                "entries": []
            }
        
        return {
            "entity_name": entity_name,
            "total_returned": len(entries),
            "limit": limit,
            "offset": offset,
            "entries": [entry.to_dict() for entry in entries]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve entity audit trail: {str(e)}")

