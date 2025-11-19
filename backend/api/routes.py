"""API routes for the FastAPI application"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.agent.openai_agent import ComplianceAgent
from backend.db.base import get_db
from backend.db.models import ComplianceQuery, ComplianceRule
from backend.auth.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Compliance API", "Protected"], dependencies=[Depends(get_current_user)])


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for compliance queries"""
    query: str
    chat_history: Optional[List[dict]] = None


class QueryResponse(BaseModel):
    """Response model for compliance queries"""
    status: str
    response: str
    model: str
    query_id: Optional[int] = None


class RuleCreate(BaseModel):
    """Request model for creating compliance rules"""
    title: str
    description: str
    category: Optional[str] = None
    regulation_source: Optional[str] = None


class RuleResponse(BaseModel):
    """Response model for compliance rules"""
    id: int
    title: str
    description: str
    category: Optional[str]
    regulation_source: Optional[str]
    
    class Config:
        from_attributes = True


# Lazy agent initialization (avoids import-time API key requirement)
_agent = None

def get_agent():
    """Get or create the ComplianceAgent instance (lazy initialization)"""
    global _agent
    if _agent is None:
        _agent = ComplianceAgent()
    return _agent


@router.post("/query", response_model=QueryResponse)
async def process_compliance_query(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Process a compliance query using the OpenAI agent
    
    Args:
        request: QueryRequest containing the user's query
        http_request: HTTP request object
        db: Database session
        current_user: Authenticated user
        
    Returns:
        QueryResponse with the agent's answer
    """
    import asyncio
    
    logger.info(f"Processing compliance query from user {current_user.username}", extra={
        "user_id": current_user.id,
        "query_length": len(request.query) if request.query else 0,
        "has_chat_history": bool(request.chat_history)
    })
    
    try:
        # Validate input
        if not request.query or not request.query.strip():
            logger.warning("Empty query received", extra={"user_id": current_user.id})
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Process query with agent (with audit logging enabled) with timeout
        try:
            result = await asyncio.wait_for(
                get_agent().process_query(
                    query=request.query,
                    chat_history=request.chat_history,
                    log_audit=True,
                    db_session=db
                ),
                timeout=25.0  # 25 second timeout (frontend has 30s)
            )
        except asyncio.TimeoutError:
            logger.warning(f"Query timeout for user {current_user.username}", extra={
                "user_id": current_user.id,
                "query_length": len(request.query)
            })
            from backend.api.error_utils import raise_standardized_error
            raise_standardized_error(
                status_code=504,
                error_type="TimeoutError",
                message="Request timed out. The AI is taking too long to respond. Please try a simpler question or try again.",
                details={"timeout_seconds": 30}
            )
        
        # Handle error responses from agent
        if result.get("status") == "error":
            error_message = result.get("error", "Unknown error occurred")
            logger.error(f"Agent error for user {current_user.username}: {error_message}", extra={
                "user_id": current_user.id,
                "error": error_message,
                "model": result.get("model", "unknown")
            })
            # Log error query to database
            try:
                db_query = ComplianceQuery(
                    query=request.query,
                    response=f"Error: {error_message}",
                    model=result.get("model", "unknown"),
                    status="error",
                    meta_data={"error": error_message}
                )
                db.add(db_query)
                db.commit()
            except Exception as db_error:
                logger.error(f"Failed to log error query to database: {db_error}", exc_info=True)
            
            from backend.api.error_utils import raise_standardized_error
            raise_standardized_error(
                status_code=500,
                error_type="AgentError",
                message=error_message,
                details={"model": result.get("model", "unknown")}
            )
        
        # Store successful query in database
        try:
            db_query = ComplianceQuery(
                query=request.query,
                response=result.get("response", ""),
                model=result.get("model", "unknown"),
                status=result.get("status", "success"),
                meta_data={
                    "audit_id": result.get("audit_id"),
                    "audit_warning": result.get("audit_warning")
                }
            )
            db.add(db_query)
            db.commit()
            db.refresh(db_query)
            query_id = db_query.id
        except Exception as db_error:
            # Log database error but still return the result
            print(f"Failed to save query to database: {db_error}")
            db.rollback()
            query_id = None
        
        return QueryResponse(
            status=result.get("status", "success"),
            response=result.get("response", "No response generated"),
            model=result.get("model", "unknown"),
            query_id=query_id,
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error in process_compliance_query: {type(e).__name__}: {e}", exc_info=True, extra={
            "user_id": current_user.id if 'current_user' in locals() else None,
            "query_length": len(request.query) if request.query else 0
        })
        # Attempt to rollback any pending database transactions
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Unhandled error in route rollback: {rollback_error}", exc_info=True)
        from backend.api.error_utils import raise_standardized_error
        raise_standardized_error(
            status_code=500,
            error_type="InternalServerError",
            message=f"Internal server error: {str(e)}",
            details={"error_type": type(e).__name__}
        )


@router.get("/queries", response_model=List[dict])
def get_queries(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get list of previous compliance queries
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of compliance queries
    """
    queries = db.query(ComplianceQuery).offset(skip).limit(limit).all()
    return [
        {
            "id": q.id,
            "query": q.query,
            "response": q.response,
            "model": q.model,
            "status": q.status,
            "created_at": q.created_at.isoformat(),
        }
        for q in queries
    ]


@router.post("/rules", response_model=RuleResponse)
def create_rule(
    rule: RuleCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new compliance rule
    
    Args:
        rule: RuleCreate with rule details
        db: Database session
        
    Returns:
        Created rule
    """
    db_rule = ComplianceRule(
        title=rule.title,
        description=rule.description,
        category=rule.category,
        regulation_source=rule.regulation_source,
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.get("/rules", response_model=List[RuleResponse])
def get_rules(
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of compliance rules
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        category: Optional category filter
        db: Database session
        
    Returns:
        List of compliance rules
    """
    query = db.query(ComplianceRule)
    
    if category:
        query = query.filter(ComplianceRule.category == category)
    
    rules = query.offset(skip).limit(limit).all()
    return rules


@router.get("/rules/{rule_id}", response_model=RuleResponse)
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Get a specific compliance rule by ID
    
    Args:
        rule_id: ID of the rule
        db: Database session
        
    Returns:
        Compliance rule
    """
    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return rule


# Export email endpoint (stub implementation)
class EmailExportRequest(BaseModel):
    """Request model for email export"""
    recipient: str
    subject: str
    body: str
    attachment_data: Optional[Dict[str, Any]] = None


@router.post("/export/email")
async def export_email(
    request: EmailExportRequest,
    db: Session = Depends(get_db)
):
    """
    Email export functionality (NOT IMPLEMENTED).
    
    This endpoint is a placeholder. Email functionality requires SMTP configuration
    and email service integration.
    
    Args:
        request: EmailExportRequest with recipient, subject, body, and optional attachment
        db: Database session
        
    Returns:
        501 Not Implemented status
        
    Raises:
        HTTPException: Always raises 501 Not Implemented
    """
    raise HTTPException(
        status_code=501,
        detail={
            "status": "not_implemented",
            "message": "Email export functionality is not yet implemented. Please use download options instead.",
            "recipient": request.recipient,
            "subject": request.subject,
            "note": "This endpoint requires SMTP configuration and email service integration. Use download options (TXT, Excel, JSON) for now."
        }
    )

