"""
Failure Simulator Module

Simulates failures and tests error recovery capabilities.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.agentic_engine.orchestrator import AgenticAIOrchestrator
from .failure_injection import FailureInjectionLayer, FailureType
from .failure_taxonomy import FailureTaxonomy


class FailureSimulator:
    """
    Simulates failures in the agentic engine and tracks recovery.
    """
    
    def __init__(
        self,
        orchestrator: Optional[AgenticAIOrchestrator] = None,
        db_session: Optional[Any] = None
    ):
        """
        Initialize failure simulator.
        
        Args:
            orchestrator: Optional orchestrator instance
            db_session: Optional database session
        """
        self.orchestrator = orchestrator or AgenticAIOrchestrator(db_session=db_session)
        self.db_session = db_session
        self.failure_injection = FailureInjectionLayer(enabled=False)
        self.failure_taxonomy = FailureTaxonomy()
    
    def simulate_failure(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        failure_type: FailureType = FailureType.TOOL_TIMEOUT,
        failure_rate: float = 1.0,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Simulate a specific failure type during orchestrator execution.
        
        Args:
            task: Task to execute
            context: Optional context
            failure_type: Type of failure to inject
            failure_rate: Probability of failure (0.0 to 1.0)
            max_iterations: Maximum iterations
            
        Returns:
            Dictionary with execution results and failure/recovery information
        """
        # Enable failure injection with specific type
        self.failure_injection.enabled = True
        self.failure_injection.failure_rate = failure_rate
        
        # Temporarily wrap orchestrator tools with failure injection
        original_tools = self.orchestrator.tools.copy()
        
        # Wrap tools with failure injection
        for tool_name, tool in self.orchestrator.tools.items():
            # Store original methods
            if hasattr(tool, 'fetch_entity_details'):
                original_method = tool.fetch_entity_details
                def wrapped_entity(*args, **kwargs):
                    return self.failure_injection.wrap_tool_execution(
                        tool_name, original_method, failure_type, *args, **kwargs
                    )
                tool.fetch_entity_details = wrapped_entity
            
            if hasattr(tool, 'calculate_deadline'):
                original_method = tool.calculate_deadline
                def wrapped_calendar(*args, **kwargs):
                    return self.failure_injection.wrap_tool_execution(
                        tool_name, original_method, failure_type, *args, **kwargs
                    )
                tool.calculate_deadline = wrapped_calendar
            
            if hasattr(tool, 'run_task_risk_analyzer'):
                original_method = tool.run_task_risk_analyzer
                def wrapped_task(*args, **kwargs):
                    return self.failure_injection.wrap_tool_execution(
                        tool_name, original_method, failure_type, *args, **kwargs
                    )
                tool.run_task_risk_analyzer = wrapped_task
            
            if hasattr(tool, 'get_sync'):
                original_method = tool.get_sync
                def wrapped_http(*args, **kwargs):
                    return self.failure_injection.wrap_tool_execution(
                        tool_name, original_method, failure_type, *args, **kwargs
                    )
                tool.get_sync = wrapped_http
        
        start_time = time.time()
        recovery_timeline = []
        
        try:
            # Run orchestrator with failure injection
            result = self.orchestrator.run(
                task=task,
                context=context,
                max_iterations=max_iterations
            )
            
            execution_time = time.time() - start_time
            
            # Analyze failures and recoveries
            failures = self.failure_injection.injected_failures
            recovery_attempts = self.failure_injection.recovery_attempts
            
            # Record failures in taxonomy
            for failure in failures:
                self.failure_taxonomy.record_failure(
                    failure_type=failure.get("type", "unknown"),
                    error_message=failure.get("message", ""),
                    tool_name=failure.get("tool"),
                    context=failure
                )
            
            # Build recovery timeline
            for i, failure in enumerate(failures):
                recovery_timeline.append({
                    "timestamp": failure.get("timestamp", datetime.utcnow().isoformat()),
                    "event": "failure",
                    "failure_type": failure.get("type"),
                    "tool": failure.get("tool"),
                    "message": failure.get("message")
                })
                
                # Check if there was a recovery attempt
                if i < len(recovery_attempts):
                    attempt = recovery_attempts[i]
                    recovery_timeline.append({
                        "timestamp": attempt.get("timestamp", datetime.utcnow().isoformat()),
                        "event": "recovery_attempt",
                        "action": attempt.get("recovery_action"),
                        "success": attempt.get("success", False)
                    })
            
            # Get failure statistics
            failure_stats = self.failure_injection.get_failure_statistics()
            taxonomy_stats = self.failure_taxonomy.get_failure_statistics()
            
            return {
                "status": "completed",
                "execution_time": execution_time,
                "result": result,
                "failures": failures,
                "recovery_attempts": recovery_attempts,
                "recovery_timeline": recovery_timeline,
                "failure_statistics": failure_stats,
                "taxonomy_statistics": taxonomy_stats,
                "injected_failure_type": failure_type.value,
                "failure_rate": failure_rate,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Record the exception as a failure
            failure_record = self.failure_taxonomy.record_failure(
                failure_type=failure_type.value,
                error_message=str(e),
                tool_name=None,
                context={"exception": str(e)}
            )
            
            return {
                "status": "error",
                "execution_time": execution_time,
                "result": None,
                "failures": self.failure_injection.injected_failures,
                "recovery_attempts": self.failure_injection.recovery_attempts,
                "recovery_timeline": recovery_timeline,
                "failure_statistics": self.failure_injection.get_failure_statistics(),
                "taxonomy_statistics": self.failure_taxonomy.get_failure_statistics(),
                "injected_failure_type": failure_type.value,
                "failure_rate": failure_rate,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        finally:
            # Restore original tools
            self.orchestrator.tools = original_tools
            self.failure_injection.enabled = False

