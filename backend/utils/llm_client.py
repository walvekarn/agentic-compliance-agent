"""
Unified LLM Client Gateway
==========================
SINGLE unified gateway for all LLM calls across the entire codebase.

All OpenAI calls MUST go through this module using client.responses.create().
No endpoint or page may directly call OpenAI.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from backend.config import settings

logger = logging.getLogger(__name__)

# Standardized model configuration for compliance tasks
COMPLIANCE_MODEL = "gpt-4o-mini"
STANDARD_MODEL = COMPLIANCE_MODEL  # Alias for backward compatibility
STANDARD_TEMPERATURE = 0.7
MAX_OUTPUT_TOKENS = 2048
COMPLIANCE_TIMEOUT = 45.0  # 45 seconds for compliance tasks
MAX_RETRIES = 2  # 2 retries for failed requests

# Try to import OpenAI client
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None


def get_compliance_response_schema() -> Dict[str, Any]:
    """
    Get the JSON schema for compliance analysis responses.
    
    Returns:
        JSON schema dict matching AnalysisResult structure
    """
    return {
        "type": "object",
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["AUTONOMOUS", "REVIEW_REQUIRED", "ESCALATE"],
                "description": "Final decision outcome"
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Confidence in decision (0-1)"
            },
            "risk_level": {
                "type": "string",
                "enum": ["LOW", "MEDIUM", "HIGH"],
                "description": "Classified risk level"
            },
            "risk_analysis": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "factor": {"type": "string"},
                        "score": {"type": "number", "minimum": 0, "maximum": 1},
                        "weight": {"type": "number", "minimum": 0, "maximum": 1},
                        "explanation": {"type": "string"}
                    },
                    "required": ["factor", "score", "weight", "explanation"]
                }
            },
            "why": {
                "type": "object",
                "properties": {
                    "reasoning_steps": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["reasoning_steps"]
            },
            "recommendations": {
                "type": "array",
                "items": {"type": "string"}
            },
            "escalation_reason": {
                "type": "string"
            }
        },
        "required": ["decision", "confidence", "risk_level", "risk_analysis", "why"]
    }


class LLMResponse:
    """Structured response from LLM gateway"""
    
    def __init__(
        self,
        parsed_json: Optional[Dict[str, Any]] = None,
        raw_text: Optional[str] = None,
        confidence: Optional[float] = None,
        status: str = "completed",
        error: Optional[str] = None
    ):
        self.parsed_json = parsed_json
        self.raw_text = raw_text
        self.confidence = confidence
        self.status = status
        self.error = error
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "status": self.status,
            "parsed_json": self.parsed_json,
            "raw_text": self.raw_text,
            "confidence": self.confidence,
            "error": self.error,
            "timestamp": self.timestamp
        }


class LLMClient:
    """
    Unified LLM client for all OpenAI calls.
    
    This is the SINGLE gateway for all LLM interactions.
    All code must use this client instead of directly calling OpenAI.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize the LLM client.
        
        Args:
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
            model: Model to use (defaults to COMPLIANCE_MODEL)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or COMPLIANCE_MODEL
        
        # Initialize OpenAI client if we have an API key
        if HAS_OPENAI and self.api_key and self.api_key != "mock" and not (isinstance(self.api_key, str) and self.api_key.startswith("sk-mock")):
            # Set timeout at client level
            self.client = OpenAI(
                api_key=self.api_key,
                timeout=COMPLIANCE_TIMEOUT
            )
            self.available = True
        else:
            self.client = None
            self.available = False
            if not HAS_OPENAI:
                logger.warning("⚠️ OpenAI package not installed - LLM features will be unavailable")
            else:
                if not self.api_key:
                    logger.warning("⚠️ LLM client initialized without OPENAI_API_KEY - will return mock responses")
                    logger.warning("   Set OPENAI_API_KEY environment variable to enable real LLM calls")
                elif isinstance(self.api_key, str) and self.api_key.startswith("sk-mock"):
                    logger.warning("⚠️ LLM client using mock API key - will return mock responses")
                else:
                    logger.warning(f"⚠️ LLM client API key validation failed - will return mock responses")
                    logger.warning(f"   Key present: {bool(self.api_key)}, length: {len(self.api_key) if self.api_key else 0}")
                    logger.warning(f"   Key starts with 'sk-': {self.api_key.startswith('sk-') if self.api_key else False}")
    
    def _make_request_with_retries(
        self,
        prompt: str,
        response_schema: Optional[Dict[str, Any]] = None,
        timeout: float = COMPLIANCE_TIMEOUT
    ) -> LLMResponse:
        """
        Make an LLM request with retry logic.
        
        Args:
            prompt: The prompt to send
            response_schema: Optional JSON schema for structured output
            timeout: Request timeout in seconds
            
        Returns:
            LLMResponse object
        """
        if not self.available:
            return LLMResponse(
                parsed_json=None,
                raw_text="Mock response - OpenAI API key not configured",
                confidence=None,
                status="error",
                error="LLM client not available"
            )
        
        last_error = None
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                # Prepare request parameters
                request_params = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a compliance analysis assistant. Provide structured, accurate responses."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": STANDARD_TEMPERATURE,
                    "max_tokens": MAX_OUTPUT_TOKENS
                }
                
                # Add JSON schema if provided
                if response_schema:
                    request_params["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "compliance_analysis_response",
                            "strict": True,
                            "schema": response_schema
                        }
                    }
                
                # Make the request using chat.completions.create()
                response = self.client.chat.completions.create(**request_params)
                
                # Extract content
                raw_text = ""
                parsed_json = None
                
                if hasattr(response, 'choices') and len(response.choices) > 0:
                    choice = response.choices[0]
                    if hasattr(choice, 'message'):
                        raw_text = choice.message.content if hasattr(choice.message, 'content') else str(choice.message)
                    elif hasattr(choice, 'content'):
                        raw_text = choice.content
                    else:
                        raw_text = str(choice)
                else:
                    raw_text = str(response)
                
                # Try to parse as JSON
                try:
                    parsed_json = json.loads(raw_text) if isinstance(raw_text, str) else raw_text
                except (json.JSONDecodeError, TypeError):
                    # If not JSON and we expected JSON schema, this is an error
                    if response_schema:
                        raise ValueError(f"Response is not valid JSON despite schema requirement: {raw_text[:200]}")
                    # Otherwise, keep raw text
                    parsed_json = None
                
                # Extract confidence from parsed JSON if available
                confidence = None
                if isinstance(parsed_json, dict):
                    confidence = parsed_json.get("confidence")
                    if confidence is not None:
                        # Ensure confidence is in 0-1 range
                        confidence = max(0.0, min(1.0, float(confidence)))
                
                return LLMResponse(
                    parsed_json=parsed_json,
                    raw_text=raw_text,
                    confidence=confidence,
                    status="completed",
                    error=None
                )
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"LLM request attempt {attempt + 1}/{MAX_RETRIES + 1} failed: {last_error}")
                
                # If this was the last attempt, return error
                if attempt == MAX_RETRIES:
                    return LLMResponse(
                        parsed_json=None,
                        raw_text=None,
                        confidence=None,
                        status="error",
                        error=f"LLM request failed after {MAX_RETRIES + 1} attempts: {last_error}"
                    )
                
                # Wait before retry (exponential backoff)
                wait_time = 2 ** attempt
                import time
                time.sleep(wait_time)
        
        # Should not reach here, but handle it
        return LLMResponse(
            parsed_json=None,
            raw_text=None,
            confidence=None,
            status="error",
            error=f"Unexpected error: {last_error}"
        )
    
    async def _make_request_with_retries_async(
        self,
        prompt: str,
        response_schema: Optional[Dict[str, Any]] = None,
        timeout: float = COMPLIANCE_TIMEOUT
    ) -> LLMResponse:
        """
        Make an async LLM request with retry logic.
        
        Args:
            prompt: The prompt to send
            response_schema: Optional JSON schema for structured output
            timeout: Request timeout in seconds
            
        Returns:
            LLMResponse object
        """
        if not self.available:
            return LLMResponse(
                parsed_json=None,
                raw_text="Mock response - OpenAI API key not configured",
                confidence=None,
                status="error",
                error="LLM client not available"
            )
        
        last_error = None
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                # Prepare request parameters
                request_params = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a compliance analysis assistant. Provide structured, accurate responses."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": STANDARD_TEMPERATURE,
                    "max_tokens": MAX_OUTPUT_TOKENS
                }
                
                # Add JSON schema if provided
                if response_schema:
                    request_params["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "compliance_analysis_response",
                            "strict": True,
                            "schema": response_schema
                        }
                    }
                
                # Make the async request using chat.completions.create()
                # Note: OpenAI client is sync, so we run it in executor with timeout
                loop = asyncio.get_event_loop()
                try:
                    response = await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda: self.client.chat.completions.create(**request_params)
                        ),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    raise asyncio.TimeoutError(f"Request timed out after {timeout} seconds")
                
                # Extract content from OpenAI response
                raw_text = ""
                parsed_json = None
                
                if hasattr(response, 'choices') and len(response.choices) > 0:
                    choice = response.choices[0]
                    if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                        raw_text = choice.message.content
                    elif hasattr(choice, 'content'):
                        raw_text = choice.content
                    else:
                        raw_text = str(choice)
                elif hasattr(response, 'content'):
                    raw_text = response.content
                else:
                    raw_text = str(response)
                
                # Ensure we have text
                if not raw_text:
                    raise ValueError("Empty response from LLM")
                
                # Try to parse as JSON
                try:
                    parsed_json = json.loads(raw_text) if isinstance(raw_text, str) else raw_text
                except (json.JSONDecodeError, TypeError):
                    # If not JSON and we expected JSON schema, this is an error
                    if response_schema:
                        raise ValueError(f"Response is not valid JSON despite schema requirement: {raw_text[:200]}")
                    # Otherwise, keep raw text
                    parsed_json = None
                
                # Extract confidence from parsed JSON if available
                confidence = None
                if isinstance(parsed_json, dict):
                    confidence = parsed_json.get("confidence")
                    if confidence is not None:
                        # Ensure confidence is in 0-1 range
                        confidence = max(0.0, min(1.0, float(confidence)))
                
                return LLMResponse(
                    parsed_json=parsed_json,
                    raw_text=raw_text,
                    confidence=confidence,
                    status="completed",
                    error=None
                )
                
            except asyncio.TimeoutError:
                last_error = f"Request timed out after {timeout} seconds"
                logger.warning(f"LLM request attempt {attempt + 1}/{MAX_RETRIES + 1} timed out")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"LLM request attempt {attempt + 1}/{MAX_RETRIES + 1} failed: {last_error}")
            
            # If this was the last attempt, return error
            if attempt == MAX_RETRIES:
                return LLMResponse(
                    parsed_json=None,
                    raw_text=None,
                    confidence=None,
                    status="error",
                    error=f"LLM request failed after {MAX_RETRIES + 1} attempts: {last_error}"
                )
            
            # Wait before retry (exponential backoff)
            wait_time = 2 ** attempt
            await asyncio.sleep(wait_time)
        
        # Should not reach here, but handle it
        return LLMResponse(
            parsed_json=None,
            raw_text=None,
            confidence=None,
            status="error",
            error=f"Unexpected error: {last_error}"
        )
    
    def run_compliance_analysis(
        self,
        prompt: str,
        use_json_schema: bool = True,
        timeout: Optional[float] = None
    ) -> LLMResponse:
        """
        Run compliance analysis using the unified gateway.
        
        This is the PRIMARY method for all compliance-related LLM calls.
        All endpoints should use this method.
        
        Args:
            prompt: The analysis prompt
            use_json_schema: Whether to enforce JSON schema (default: True)
            
        Returns:
            LLMResponse with parsed_json, raw_text, and confidence
        """
        response_schema = get_compliance_response_schema() if use_json_schema else None
        return self._make_request_with_retries(
            prompt=prompt,
            response_schema=response_schema,
            timeout=timeout or COMPLIANCE_TIMEOUT
        )
    
    async def run_compliance_analysis_async(
        self,
        prompt: str,
        use_json_schema: bool = True,
        timeout: Optional[float] = None
    ) -> LLMResponse:
        """
        Run compliance analysis asynchronously using the unified gateway.
        
        Args:
            prompt: The analysis prompt
            use_json_schema: Whether to enforce JSON schema (default: True)
            
        Returns:
            LLMResponse with parsed_json, raw_text, and confidence
        """
        response_schema = get_compliance_response_schema() if use_json_schema else None
        return await self._make_request_with_retries_async(
            prompt=prompt,
            response_schema=response_schema,
            timeout=timeout or COMPLIANCE_TIMEOUT
        )
    
    # Legacy methods for backward compatibility
    def call_sync(
        self,
        prompt: str,
        is_main_task: bool = True,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Legacy sync call method (for backward compatibility).
        
        Prefer run_compliance_analysis() for new code.
        """
        response = self.run_compliance_analysis(prompt, use_json_schema=False, timeout=timeout)
        return response.to_dict()
    
    async def call_async(
        self,
        prompt: str,
        is_main_task: bool = True,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Legacy async call method (for backward compatibility).
        
        Prefer run_compliance_analysis_async() for new code.
        """
        response = await self.run_compliance_analysis_async(prompt, use_json_schema=False, timeout=timeout)
        return response.to_dict()


# Global singleton instance
_global_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    Get or create the global LLM client instance.
    
    Returns:
        Global LLMClient instance
    """
    global _global_client
    if _global_client is None:
        _global_client = LLMClient()
    return _global_client


# Convenience functions
def run_compliance_analysis(prompt: str, use_json_schema: bool = True) -> LLMResponse:
    """
    Convenience function for compliance analysis using global client.
    
    Args:
        prompt: The analysis prompt
        use_json_schema: Whether to enforce JSON schema (default: True)
        
    Returns:
        LLMResponse with parsed_json, raw_text, and confidence
    """
    return get_llm_client().run_compliance_analysis(prompt, use_json_schema)


async def run_compliance_analysis_async(prompt: str, use_json_schema: bool = True) -> LLMResponse:
    """
    Convenience function for async compliance analysis using global client.
    
    Args:
        prompt: The analysis prompt
        use_json_schema: Whether to enforce JSON schema (default: True)
        
    Returns:
        LLMResponse with parsed_json, raw_text, and confidence
    """
    return await get_llm_client().run_compliance_analysis_async(prompt, use_json_schema)


# Legacy convenience functions for backward compatibility
async def call_llm_async(
    prompt: str,
    is_main_task: bool = True,
    model: Optional[str] = None,
    timeout: Optional[float] = None
) -> Dict[str, Any]:
    """
    Legacy convenience function (for backward compatibility).
    
    Prefer run_compliance_analysis_async() for new code.
    """
    client = get_llm_client()
    if model and model != client.model:
        client = LLMClient(model=model)
    return await client.call_async(prompt, is_main_task=is_main_task, timeout=timeout)


def call_llm_sync(
    prompt: str,
    is_main_task: bool = True,
    model: Optional[str] = None,
    timeout: Optional[float] = None
) -> Dict[str, Any]:
    """
    Legacy convenience function (for backward compatibility).
    
    Prefer run_compliance_analysis() for new code.
    """
    client = get_llm_client()
    if model and model != client.model:
        client = LLMClient(model=model)
    return client.call_sync(prompt, is_main_task=is_main_task, timeout=timeout)
