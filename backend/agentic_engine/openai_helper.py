"""
Standardized OpenAI Helper Module
=================================
Provides consistent OpenAI API calls across the project with:
- Standardized model version (gpt-4o-mini)
- Timeout enforcement (120s main, 30s secondary)
- Standardized response format: {status, result, error, timestamp}
- Try/except with logging
- Sanitization and validation
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

# Standardized model configuration
STANDARD_MODEL = "gpt-4o-mini"
STANDARD_TEMPERATURE = 0.7
STANDARD_MAX_TOKENS = 4096

# Timeout constants
TIMEOUT_MAIN = 120.0  # 120 seconds for main tasks
TIMEOUT_SECONDARY = 30.0  # 30 seconds for secondary tasks


def sanitize_output(data: Any) -> Any:
    """
    Sanitize output to ensure it matches allowed structure.
    
    Args:
        data: Raw output data
        
    Returns:
        Sanitized data structure
    """
    if data is None:
        return None
    
    # If it's a string, try to parse as JSON
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            # If not JSON, return as-is (will be wrapped in result)
            return data
    
    # If it's a dict, ensure it has allowed structure
    if isinstance(data, dict):
        # Remove any keys that might contain sensitive data
        sanitized = {}
        for key, value in data.items():
            # Only allow alphanumeric and underscore keys
            if isinstance(key, str) and key.replace("_", "").replace("-", "").isalnum():
                sanitized[key] = sanitize_output(value)
        return sanitized
    
    # If it's a list, sanitize each item
    if isinstance(data, list):
        return [sanitize_output(item) for item in data]
    
    # For other types, return as-is
    return data


def validate_response_structure(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize response to match {status, result, error, timestamp} format.
    
    Args:
        response: Response dictionary to validate
        
    Returns:
        Validated response in standard format
    """
    # Ensure required fields exist
    validated = {
        "status": response.get("status", "error"),
        "result": response.get("result", None),
        "error": response.get("error", None),
        "timestamp": response.get("timestamp", datetime.utcnow().isoformat())
    }
    
    # Validate status field
    if validated["status"] not in ["completed", "timeout", "error"]:
        logger.warning(f"Invalid status '{validated['status']}', defaulting to 'error'")
        validated["status"] = "error"
        if not validated["error"]:
            validated["error"] = f"Invalid status: {response.get('status')}"
    
    # Sanitize result
    if validated["result"] is not None:
        validated["result"] = sanitize_output(validated["result"])
    
    return validated


async def call_openai_async(
    prompt: str,
    is_main_task: bool = True,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[float] = None
) -> Dict[str, Any]:
    """
    Make an async OpenAI API call with standardized configuration.
    
    Args:
        prompt: The prompt to send to OpenAI
        is_main_task: True for main tasks (120s timeout), False for secondary (30s timeout)
        model: Model to use (defaults to STANDARD_MODEL)
        temperature: Temperature setting (defaults to STANDARD_TEMPERATURE)
        max_tokens: Max tokens (defaults to STANDARD_MAX_TOKENS)
        timeout: Override timeout (defaults based on is_main_task)
        
    Returns:
        Standardized response: {status, result, error, timestamp}
    """
    timestamp = datetime.utcnow().isoformat()
    
    # Get configuration
    api_key = os.getenv("OPENAI_API_KEY")
    model = model or STANDARD_MODEL
    temperature = temperature if temperature is not None else STANDARD_TEMPERATURE
    max_tokens = max_tokens or STANDARD_MAX_TOKENS
    timeout = timeout or (TIMEOUT_MAIN if is_main_task else TIMEOUT_SECONDARY)
    
    # Check if API key is available
    if not api_key or api_key == "mock" or (isinstance(api_key, str) and api_key.startswith("sk-mock")):
        logger.warning("OpenAI API key not set, returning mock response")
        return {
            "status": "completed",
            "result": {"content": "Mock response - OpenAI API key not configured"},
            "error": None,
            "timestamp": timestamp
        }
    
    try:
        # Initialize LLM client
        llm = ChatOpenAI(
            openai_api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Make async call with timeout
        try:
            response = await asyncio.wait_for(
                llm.ainvoke(prompt),
                timeout=timeout
            )
            
            # Extract content
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Try to parse as JSON if possible
            result = None
            try:
                result = json.loads(content)
            except (json.JSONDecodeError, TypeError):
                # If not JSON, wrap in result structure
                result = {"content": content}
            
            # Sanitize and validate
            result = sanitize_output(result)
            
            return validate_response_structure({
                "status": "completed",
                "result": result,
                "error": None,
                "timestamp": timestamp
            })
            
        except asyncio.TimeoutError:
            logger.error(f"OpenAI API call timed out after {timeout}s")
            return validate_response_structure({
                "status": "timeout",
                "result": None,
                "error": f"Request timed out after {timeout} seconds",
                "timestamp": timestamp
            })
            
    except Exception as e:
        logger.error(f"OpenAI API call failed: {str(e)}", exc_info=True)
        return validate_response_structure({
            "status": "error",
            "result": None,
            "error": f"OpenAI API error: {str(e)}",
            "timestamp": timestamp
        })


def call_openai_sync(
    prompt: str,
    is_main_task: bool = True,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[float] = None
) -> Dict[str, Any]:
    """
    Make a synchronous OpenAI API call with standardized configuration.
    
    Args:
        prompt: The prompt to send to OpenAI
        is_main_task: True for main tasks (120s timeout), False for secondary (30s timeout)
        model: Model to use (defaults to STANDARD_MODEL)
        temperature: Temperature setting (defaults to STANDARD_TEMPERATURE)
        max_tokens: Max tokens (defaults to STANDARD_MAX_TOKENS)
        timeout: Override timeout (defaults based on is_main_task)
        
    Returns:
        Standardized response: {status, result, error, timestamp}
    """
    timestamp = datetime.utcnow().isoformat()
    
    # Get configuration
    api_key = os.getenv("OPENAI_API_KEY")
    model = model or STANDARD_MODEL
    temperature = temperature if temperature is not None else STANDARD_TEMPERATURE
    max_tokens = max_tokens or STANDARD_MAX_TOKENS
    timeout = timeout or (TIMEOUT_MAIN if is_main_task else TIMEOUT_SECONDARY)
    
    # Check if API key is available
    if not api_key or api_key == "mock" or (isinstance(api_key, str) and api_key.startswith("sk-mock")):
        logger.warning("OpenAI API key not set, returning mock response")
        return {
            "status": "completed",
            "result": {"content": "Mock response - OpenAI API key not configured"},
            "error": None,
            "timestamp": timestamp
        }
    
    try:
        # Initialize LLM client
        llm = ChatOpenAI(
            openai_api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Make sync call with timeout using asyncio
        try:
            # Run async call in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, use thread pool
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(
                            asyncio.wait_for(
                                llm.ainvoke(prompt),
                                timeout=timeout
                            )
                        )
                    )
                    response = future.result(timeout=timeout + 5)  # Add buffer
            else:
                # If no loop running, use asyncio.run
                response = asyncio.run(
                    asyncio.wait_for(
                        llm.ainvoke(prompt),
                        timeout=timeout
                    )
                )
            
            # Extract content
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Try to parse as JSON if possible
            result = None
            try:
                result = json.loads(content)
            except (json.JSONDecodeError, TypeError):
                # If not JSON, wrap in result structure
                result = {"content": content}
            
            # Sanitize and validate
            result = sanitize_output(result)
            
            return validate_response_structure({
                "status": "completed",
                "result": result,
                "error": None,
                "timestamp": timestamp
            })
            
        except asyncio.TimeoutError:
            logger.error(f"OpenAI API call timed out after {timeout}s")
            return validate_response_structure({
                "status": "timeout",
                "result": None,
                "error": f"Request timed out after {timeout} seconds",
                "timestamp": timestamp
            })
            
    except Exception as e:
        logger.error(f"OpenAI API call failed: {str(e)}", exc_info=True)
        return validate_response_structure({
            "status": "error",
            "result": None,
            "error": f"OpenAI API error: {str(e)}",
            "timestamp": timestamp
        })


def parse_agentic_response(response: Dict[str, Any]) -> tuple:
    """
    Parse standardized response format (compatible with parseAgenticResponse).
    
    Args:
        response: Standardized response dict with {status, result, error, timestamp}
        
    Returns:
        Tuple of (status, results, error, timestamp)
    """
    status = response.get("status")
    results = response.get("result")
    error = response.get("error")
    timestamp = response.get("timestamp")
    
    if status not in ["completed", "timeout", "error"]:
        return None, None, f"Invalid status: {status}", timestamp
    
    return status, results, error, timestamp

