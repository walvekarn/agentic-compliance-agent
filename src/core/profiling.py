"""
Performance Profiling

Timing decorators and performance metrics collection.
"""

import time
from functools import wraps
from typing import Dict, Any, Callable, TypeVar, Optional
from datetime import datetime
from collections import defaultdict

T = TypeVar('T')

# Global performance metrics
_performance_metrics: Dict[str, list] = defaultdict(list)
_metrics_lock = None


def get_performance_metrics() -> Dict[str, Any]:
    """
    Get aggregated performance metrics.
    
    Returns:
        Dictionary with metrics for each function
    """
    global _performance_metrics
    
    aggregated = {}
    for func_name, timings in _performance_metrics.items():
        if timings:
            aggregated[func_name] = {
                "call_count": len(timings),
                "total_time": sum(timings),
                "average_time": sum(timings) / len(timings),
                "min_time": min(timings),
                "max_time": max(timings),
                "last_call": timings[-1] if timings else 0
            }
    
    return aggregated


def clear_performance_metrics() -> None:
    """Clear all performance metrics"""
    global _performance_metrics
    _performance_metrics.clear()


def profile_execution(func: Callable) -> Callable:
    """
    Decorator to profile function execution time.
    
    Usage:
        @profile_execution
        def my_function():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            _performance_metrics[func.__name__].append(execution_time)
    
    return wrapper


def profile_agent_loop(func: Callable) -> Callable:
    """
    Decorator specifically for agent loop execution.
    
    Captures multi-pass execution costs.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        reasoning_passes = 0
        tool_calls = 0
        
        try:
            result = func(*args, **kwargs)
            
            # Extract metrics from result if available
            if isinstance(result, dict):
                reasoning_passes = result.get("reasoning_passes", 0)
                tool_calls = result.get("tool_calls", 0)
            
            return result
        finally:
            execution_time = time.time() - start_time
            
            # Store detailed metrics
            metric_key = f"{func.__name__}_detailed"
            _performance_metrics[metric_key].append({
                "execution_time": execution_time,
                "reasoning_passes": reasoning_passes,
                "tool_calls": tool_calls,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    return wrapper


class PerformanceTimer:
    """
    Context manager for timing code blocks.
    
    Usage:
        with PerformanceTimer("operation_name"):
            # code to time
            ...
    """
    
    def __init__(self, operation_name: str):
        """
        Initialize timer.
        
        Args:
            operation_name: Name of the operation being timed
        """
        self.operation_name = operation_name
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            execution_time = time.time() - self.start_time
            _performance_metrics[self.operation_name].append(execution_time)
        return False
    
    @property
    def elapsed(self) -> float:
        """Get elapsed time so far"""
        if self.start_time:
            return time.time() - self.start_time
        return 0.0

