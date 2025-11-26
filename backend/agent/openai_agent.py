"""OpenAI-based compliance agent using unified LLM client"""

from typing import Dict, Any, List, Optional
import logging
from backend.utils.llm_client import LLMClient, call_llm_async, call_llm_sync
from backend.config import settings

logger = logging.getLogger(__name__)


class ComplianceAgent:
    """Compliance agent powered by OpenAI via LangChain"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the compliance agent
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use (defaults to gpt-4o-mini)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL if hasattr(settings, 'OPENAI_MODEL') else None
        self.llm_client = LLMClient(api_key=self.api_key, model=self.model)
    
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
            # Build prompt with chat history if available
            prompt = query
            if chat_history:
                history_text = "\n".join([f"User: {h.get('user', '')}\nAssistant: {h.get('assistant', '')}" for h in chat_history[-5:]])
                prompt = f"Previous conversation:\n{history_text}\n\nCurrent query: {query}"
            
            # Use unified LLM client
            openai_response = await self.llm_client.call_async(
                prompt=prompt,
                is_main_task=False  # Query is secondary task
            )
            
            if openai_response["status"] == "completed":
                # LLMClient returns: {"status": "completed", "raw_text": "...", "parsed_json": {...}}
                response_text = openai_response.get("raw_text", "")
                # If raw_text is empty but we have parsed_json, extract from it
                if not response_text and openai_response.get("parsed_json"):
                    parsed = openai_response["parsed_json"]
                    if isinstance(parsed, dict):
                        # Try common response fields
                        response_text = parsed.get("content") or parsed.get("response") or parsed.get("answer") or str(parsed)
                    else:
                        response_text = str(parsed)
                # Fallback if still empty
                if not response_text:
                    response_text = openai_response.get("error", "No response generated")
            else:
                # Handle error or timeout
                error_msg = openai_response.get("error", "Unknown error")
                logger.error(f"LLM query failed: {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg,
                    "model": self.model or "gpt-4o-mini",
                }
            
            result = {
                "status": "success",
                "response": response_text,
                "model": self.model or "gpt-4o-mini",
            }
            
            # Log to audit trail if requested and db_session provided
            if log_audit and db_session:
                try:
                    from backend.agent.audit_service import AuditService
                    
                    # Estimate confidence based on response length and quality
                    confidence = self._estimate_confidence(response_text)
                    
                    audit_entry = AuditService.log_custom_decision(
                        db=db_session,
                        task_description=query[:500],  # Truncate long queries
                        decision_outcome="RESPONSE_PROVIDED",
                        confidence_score=confidence,
                        reasoning_chain=[
                            "Query processed by OpenAI agent",
                            f"Model: {self.model or 'gpt-4o-mini'}",
                            f"Response length: {len(response_text)} characters"
                        ],
                        agent_type="openai_agent",
                        task_category="GENERAL_INQUIRY",
                        metadata={
                            "query_length": len(query),
                            "response_length": len(response_text),
                            "has_chat_history": chat_history is not None
                        }
                    )
                    result["audit_id"] = audit_entry.id
                except Exception as audit_error:
                    # Don't fail the query if audit logging fails
                    logger.warning(f"Failed to log audit: {str(audit_error)}")
                    result["audit_warning"] = f"Failed to log audit: {str(audit_error)}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "model": self.model or "gpt-4o-mini",
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
            # Use unified LLM client
            openai_response = self.llm_client.call_sync(
                prompt=query,
                is_main_task=False  # Query is secondary task
            )
            
            if openai_response["status"] == "completed":
                # LLMClient returns: {"status": "completed", "raw_text": "...", "parsed_json": {...}}
                response_text = openai_response.get("raw_text", "")
                # If raw_text is empty but we have parsed_json, extract from it
                if not response_text and openai_response.get("parsed_json"):
                    parsed = openai_response["parsed_json"]
                    if isinstance(parsed, dict):
                        # Try common response fields
                        response_text = parsed.get("content") or parsed.get("response") or parsed.get("answer") or str(parsed)
                    else:
                        response_text = str(parsed)
                # Fallback if still empty
                if not response_text:
                    response_text = openai_response.get("error", "No response generated")
            else:
                # Handle error or timeout
                error_msg = openai_response.get("error", "Unknown error")
                logger.error(f"LLM query failed: {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg,
                    "model": self.model or "gpt-4o-mini",
                }
            
            result = {
                "status": "success",
                "response": response_text,
                "model": self.model or "gpt-4o-mini",
            }
            
            # Log to audit trail if requested and db_session provided
            if log_audit and db_session:
                try:
                    from backend.agent.audit_service import AuditService
                    
                    # Estimate confidence based on response length and quality
                    confidence = self._estimate_confidence(response_text)
                    
                    audit_entry = AuditService.log_custom_decision(
                        db=db_session,
                        task_description=query[:500],  # Truncate long queries
                        decision_outcome="RESPONSE_PROVIDED",
                        confidence_score=confidence,
                        reasoning_chain=[
                            "Query processed by OpenAI agent (sync)",
                            f"Model: {self.model or 'gpt-4o-mini'}",
                            f"Response length: {len(response_text)} characters"
                        ],
                        agent_type="openai_agent",
                        task_category="GENERAL_INQUIRY",
                        metadata={
                            "query_length": len(query),
                            "response_length": len(response_text),
                            "sync_mode": True
                        }
                    )
                    result["audit_id"] = audit_entry.id
                except Exception as audit_error:
                    # Don't fail the query if audit logging fails
                    logger.warning(f"Failed to log audit: {str(audit_error)}")
                    result["audit_warning"] = f"Failed to log audit: {str(audit_error)}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "model": self.model or "gpt-4o-mini",
            }
