"""
Compliance Query Service

Business logic for compliance queries.
"""

from typing import Optional, Dict, Any
from src.agent.openai_agent import ComplianceAgent
from src.repositories.compliance_query_repository import ComplianceQueryRepository
from src.db.models import ComplianceQuery


class ComplianceQueryService:
    """Service for compliance query processing"""
    
    def __init__(
        self,
        agent: ComplianceAgent,
        compliance_query_repository: ComplianceQueryRepository
    ):
        """
        Initialize compliance query service.
        
        Args:
            agent: Compliance agent instance
            compliance_query_repository: Repository for compliance queries
        """
        self.agent = agent
        self.compliance_query_repository = compliance_query_repository
    
    async def process_query(
        self,
        query: str,
        chat_history: Optional[list] = None,
        log_audit: bool = True
    ) -> Dict[str, Any]:
        """
        Process a compliance query.
        
        Args:
            query: User query
            chat_history: Optional chat history
            log_audit: Whether to log to database
            
        Returns:
            Query result dictionary
        """
        import asyncio
        
        # Process query with agent
        result = await self.agent.process_query(
            query=query,
            chat_history=chat_history,
            log_audit=False,  # We'll handle logging here
            db_session=None  # We'll use repository instead
        )
        
        # Log to database if requested
        if log_audit and result.get("status") != "error":
            db_query = ComplianceQuery(
                query=query,
                response=result.get("response", ""),
                model=result.get("model", "unknown"),
                status=result.get("status", "success"),
                meta_data={"chat_history_length": len(chat_history) if chat_history else 0}
            )
            self.compliance_query_repository.create(db_query)
            result["query_id"] = db_query.id
        elif log_audit and result.get("status") == "error":
            # Log error query
            error_message = result.get("error", "Unknown error")
            db_query = ComplianceQuery(
                query=query,
                response=f"Error: {error_message}",
                model=result.get("model", "unknown"),
                status="error",
                meta_data={"error": error_message}
            )
            self.compliance_query_repository.create(db_query)
            result["query_id"] = db_query.id
        
        return result

