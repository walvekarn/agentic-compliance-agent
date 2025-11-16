"""OpenAI-based compliance agent using LangChain"""

from langchain_openai import ChatOpenAI
from typing import Dict, Any, List, Optional
import os


class ComplianceAgent:
    """Compliance agent powered by OpenAI via LangChain"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the compliance agent
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use (defaults to gpt-4o-mini)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Initialize OpenAI LLM
        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            model=self.model,
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4096")),
        )
    
    async def process_query(
        self,
        query: str,
        chat_history: Optional[List] = None,
        log_audit: bool = True,
        db_session = None
    ) -> Dict[str, Any]:
        """
        Process a compliance query
        
        Args:
            query: User's compliance question or request
            chat_history: Optional chat history for context
            log_audit: Whether to log this query to audit trail
            db_session: Optional database session for audit logging
            
        Returns:
            Dictionary containing the response and metadata
        """
        try:
            # For now, use direct LLM call
            # In production, you'd use AgentExecutor with tools
            response = await self.llm.ainvoke(query)
            
            result = {
                "status": "success",
                "response": response.content,
                "model": self.model,
            }
            
            # Log to audit trail if requested and db_session provided
            if log_audit and db_session:
                try:
                    from src.agent.audit_service import AuditService
                    
                    # Estimate confidence based on response length and quality
                    confidence = self._estimate_confidence(response.content)
                    
                    audit_entry = AuditService.log_custom_decision(
                        db=db_session,
                        task_description=query[:500],  # Truncate long queries
                        decision_outcome="RESPONSE_PROVIDED",
                        confidence_score=confidence,
                        reasoning_chain=[
                            "Query processed by OpenAI agent",
                            f"Model: {self.model}",
                            f"Response length: {len(response.content)} characters"
                        ],
                        agent_type="openai_agent",
                        task_category="GENERAL_INQUIRY",
                        metadata={
                            "query_length": len(query),
                            "response_length": len(response.content),
                            "has_chat_history": chat_history is not None
                        }
                    )
                    result["audit_id"] = audit_entry.id
                except Exception as audit_error:
                    # Don't fail the query if audit logging fails
                    result["audit_warning"] = f"Failed to log audit: {str(audit_error)}"
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "model": self.model,
            }
    
    def _estimate_confidence(self, response: str) -> float:
        """
        Estimate confidence in response based on heuristics
        
        Args:
            response: The response text
            
        Returns:
            Confidence score between 0 and 1
        """
        # Simple heuristic: longer, more detailed responses get higher confidence
        # This is a placeholder - in production, you'd use more sophisticated methods
        length = len(response)
        if length < 50:
            return 0.4
        elif length < 200:
            return 0.6
        elif length < 500:
            return 0.75
        else:
            return 0.85
    
    def process_query_sync(
        self,
        query: str,
        log_audit: bool = True,
        db_session = None
    ) -> Dict[str, Any]:
        """
        Synchronous version of process_query
        
        Args:
            query: User's compliance question or request
            log_audit: Whether to log this query to audit trail
            db_session: Optional database session for audit logging
            
        Returns:
            Dictionary containing the response and metadata
        """
        try:
            response = self.llm.invoke(query)
            
            result = {
                "status": "success",
                "response": response.content,
                "model": self.model,
            }
            
            # Log to audit trail if requested and db_session provided
            if log_audit and db_session:
                try:
                    from src.agent.audit_service import AuditService
                    
                    # Estimate confidence based on response length and quality
                    confidence = self._estimate_confidence(response.content)
                    
                    audit_entry = AuditService.log_custom_decision(
                        db=db_session,
                        task_description=query[:500],  # Truncate long queries
                        decision_outcome="RESPONSE_PROVIDED",
                        confidence_score=confidence,
                        reasoning_chain=[
                            "Query processed by OpenAI agent (sync)",
                            f"Model: {self.model}",
                            f"Response length: {len(response.content)} characters"
                        ],
                        agent_type="openai_agent",
                        task_category="GENERAL_INQUIRY",
                        metadata={
                            "query_length": len(query),
                            "response_length": len(response.content),
                            "sync_mode": True
                        }
                    )
                    result["audit_id"] = audit_entry.id
                except Exception as audit_error:
                    # Don't fail the query if audit logging fails
                    result["audit_warning"] = f"Failed to log audit: {str(audit_error)}"
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "model": self.model,
            }

