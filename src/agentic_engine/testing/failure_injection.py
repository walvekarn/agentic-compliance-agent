"""
Failure Injection Layer Module

Simulates various failure modes for testing error recovery capabilities.
"""

import time
import random
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from datetime import datetime


class FailureType(str, Enum):
    """Types of failures that can be injected"""
    TOOL_TIMEOUT = "tool_timeout"
    INVALID_INPUT = "invalid_input"
    DEGRADED_OUTPUT = "degraded_output"
    MISSING_TOOL_RESULT = "missing_tool_result"
    NETWORK_ERROR = "network_error"
    PERMISSION_ERROR = "permission_error"


class FailureInjectionLayer:
    """
    Layer for injecting failures into orchestrator operations.
    
    Simulates real-world failure scenarios to test error recovery
    and resilience of the agentic system.
    """
    
    def __init__(self, enabled: bool = False, failure_rate: float = 0.1):
        """
        Initialize failure injection layer.
        
        Args:
            enabled: Whether failure injection is enabled
            failure_rate: Probability of injecting a failure (0.0 to 1.0)
        """
        self.enabled = enabled
        self.failure_rate = failure_rate
        self.injected_failures = []
        self.recovery_attempts = []
    
    def should_inject_failure(self, failure_type: FailureType) -> bool:
        """
        Determine if a failure should be injected.
        
        Args:
            failure_type: Type of failure to potentially inject
            
        Returns:
            True if failure should be injected
        """
        if not self.enabled:
            return False
        
        return random.random() < self.failure_rate
    
    def inject_tool_timeout(
        self, 
        tool_name: str, 
        timeout_seconds: float = 5.0
    ) -> Dict[str, Any]:
        """
        Simulate a tool timeout.
        
        Args:
            tool_name: Name of the tool that timed out
            timeout_seconds: How long to wait before timing out
            
        Returns:
            Error dictionary representing timeout
        """
        time.sleep(timeout_seconds)
        error = {
            "type": FailureType.TOOL_TIMEOUT.value,
            "tool": tool_name,
            "message": f"Tool {tool_name} timed out after {timeout_seconds}s",
            "timestamp": datetime.utcnow().isoformat()
        }
        self.injected_failures.append(error)
        raise TimeoutError(f"Tool {tool_name} execution timed out")
    
    def inject_invalid_input(
        self, 
        tool_name: str, 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulate invalid input error.
        
        Args:
            tool_name: Name of the tool
            input_data: Input data that is invalid
            
        Returns:
            Error dictionary
        """
        error = {
            "type": FailureType.INVALID_INPUT.value,
            "tool": tool_name,
            "message": f"Invalid input provided to {tool_name}",
            "input_data": input_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.injected_failures.append(error)
        raise ValueError(f"Invalid input for tool {tool_name}: {input_data}")
    
    def inject_degraded_output(
        self, 
        tool_name: str, 
        original_output: Any
    ) -> Dict[str, Any]:
        """
        Simulate degraded/hallucinated output.
        
        Args:
            tool_name: Name of the tool
            original_output: Original output to degrade
            
        Returns:
            Degraded output dictionary
        """
        # Degrade output by adding noise or reducing quality
        if isinstance(original_output, dict):
            degraded = original_output.copy()
            # Remove some keys or add noise
            if len(degraded) > 1:
                keys_to_remove = random.sample(list(degraded.keys()), min(1, len(degraded) - 1))
                for key in keys_to_remove:
                    degraded.pop(key, None)
            degraded["_degraded"] = True
            degraded["_quality_warning"] = "Output may be incomplete or inaccurate"
        elif isinstance(original_output, str):
            degraded = original_output[:len(original_output) // 2] + "... [degraded output]"
        else:
            degraded = {"_degraded": True, "_original_type": str(type(original_output))}
        
        error = {
            "type": FailureType.DEGRADED_OUTPUT.value,
            "tool": tool_name,
            "message": f"Tool {tool_name} returned degraded output",
            "timestamp": datetime.utcnow().isoformat()
        }
        self.injected_failures.append(error)
        
        return degraded
    
    def inject_missing_tool_result(
        self, 
        tool_name: str
    ) -> Dict[str, Any]:
        """
        Simulate missing tool result.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Error dictionary
        """
        error = {
            "type": FailureType.MISSING_TOOL_RESULT.value,
            "tool": tool_name,
            "message": f"Tool {tool_name} returned no result",
            "timestamp": datetime.utcnow().isoformat()
        }
        self.injected_failures.append(error)
        return None
    
    def inject_network_error(
        self, 
        tool_name: str
    ) -> Dict[str, Any]:
        """
        Simulate network error.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Error dictionary
        """
        error = {
            "type": FailureType.NETWORK_ERROR.value,
            "tool": tool_name,
            "message": f"Network error while calling {tool_name}",
            "timestamp": datetime.utcnow().isoformat()
        }
        self.injected_failures.append(error)
        raise ConnectionError(f"Network error: Failed to connect to {tool_name}")
    
    def inject_permission_error(
        self, 
        tool_name: str
    ) -> Dict[str, Any]:
        """
        Simulate permission/authorization error.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Error dictionary
        """
        error = {
            "type": FailureType.PERMISSION_ERROR.value,
            "tool": tool_name,
            "message": f"Permission denied for {tool_name}",
            "timestamp": datetime.utcnow().isoformat()
        }
        self.injected_failures.append(error)
        raise PermissionError(f"Permission denied: Cannot access {tool_name}")
    
    def wrap_tool_execution(
        self,
        tool_name: str,
        tool_func: Callable,
        failure_type: Optional[FailureType] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Wrap a tool execution with potential failure injection.
        
        Args:
            tool_name: Name of the tool
            tool_func: Function to execute
            failure_type: Optional specific failure type to inject
            *args: Arguments for tool function
            **kwargs: Keyword arguments for tool function
            
        Returns:
            Tool result (or degraded/error result)
        """
        if not self.enabled:
            return tool_func(*args, **kwargs)
        
        # Determine failure type if not specified
        if failure_type is None:
            if self.should_inject_failure(FailureType.TOOL_TIMEOUT):
                failure_type = FailureType.TOOL_TIMEOUT
            elif self.should_inject_failure(FailureType.INVALID_INPUT):
                failure_type = FailureType.INVALID_INPUT
            elif self.should_inject_failure(FailureType.DEGRADED_OUTPUT):
                failure_type = FailureType.DEGRADED_OUTPUT
            elif self.should_inject_failure(FailureType.MISSING_TOOL_RESULT):
                failure_type = FailureType.MISSING_TOOL_RESULT
            elif self.should_inject_failure(FailureType.NETWORK_ERROR):
                failure_type = FailureType.NETWORK_ERROR
            elif self.should_inject_failure(FailureType.PERMISSION_ERROR):
                failure_type = FailureType.PERMISSION_ERROR
        
        # Inject failure based on type
        if failure_type == FailureType.TOOL_TIMEOUT:
            return self.inject_tool_timeout(tool_name)
        elif failure_type == FailureType.INVALID_INPUT:
            return self.inject_invalid_input(tool_name, kwargs)
        elif failure_type == FailureType.MISSING_TOOL_RESULT:
            return self.inject_missing_tool_result(tool_name)
        elif failure_type == FailureType.NETWORK_ERROR:
            return self.inject_network_error(tool_name)
        elif failure_type == FailureType.PERMISSION_ERROR:
            return self.inject_permission_error(tool_name)
        elif failure_type == FailureType.DEGRADED_OUTPUT:
            # Execute tool first, then degrade output
            try:
                result = tool_func(*args, **kwargs)
                return self.inject_degraded_output(tool_name, result)
            except Exception as e:
                # If tool fails, return degraded error
                return self.inject_degraded_output(tool_name, {"error": str(e)})
        else:
            # No failure, execute normally
            return tool_func(*args, **kwargs)
    
    def record_recovery_attempt(
        self,
        failure: Dict[str, Any],
        recovery_action: str,
        success: bool
    ):
        """
        Record a recovery attempt.
        
        Args:
            failure: The failure that was recovered from
            recovery_action: Description of recovery action
            success: Whether recovery was successful
        """
        self.recovery_attempts.append({
            "failure": failure,
            "recovery_action": recovery_action,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_failure_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about injected failures.
        
        Returns:
            Dictionary with failure statistics
        """
        failure_counts = {}
        for failure in self.injected_failures:
            failure_type = failure.get("type", "unknown")
            failure_counts[failure_type] = failure_counts.get(failure_type, 0) + 1
        
        recovery_success_count = sum(1 for r in self.recovery_attempts if r["success"])
        recovery_total = len(self.recovery_attempts)
        
        return {
            "total_failures": len(self.injected_failures),
            "failure_counts": failure_counts,
            "recovery_attempts": recovery_total,
            "successful_recoveries": recovery_success_count,
            "recovery_success_rate": recovery_success_count / recovery_total if recovery_total > 0 else 0.0
        }

