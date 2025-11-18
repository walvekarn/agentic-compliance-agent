"""
Failure Taxonomy and Retry Scoring Module

Defines failure categories and scoring mechanisms for retry logic.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class FailureCategory(str, Enum):
    """Categories of failures"""
    TRANSIENT = "transient"  # Temporary, likely to succeed on retry
    PERMANENT = "permanent"  # Unlikely to succeed on retry
    INPUT_ERROR = "input_error"  # Invalid input, needs correction
    SYSTEM_ERROR = "system_error"  # System-level issue
    TIMEOUT = "timeout"  # Operation timed out
    NETWORK = "network"  # Network-related issue
    PERMISSION = "permission"  # Authorization issue


class RetryStrategy(str, Enum):
    """Retry strategies"""
    IMMEDIATE = "immediate"  # Retry immediately
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # Wait with exponential backoff
    LINEAR_BACKOFF = "linear_backoff"  # Wait with linear backoff
    NO_RETRY = "no_retry"  # Don't retry


@dataclass
class FailureRecord:
    """Record of a failure occurrence"""
    failure_type: str
    category: FailureCategory
    tool_name: Optional[str]
    error_message: str
    timestamp: str
    context: Dict[str, Any]
    retry_strategy: RetryStrategy
    retry_score: float  # 0.0 to 1.0, likelihood of success on retry


class FailureTaxonomy:
    """
    Taxonomy for categorizing and scoring failures.
    """
    
    def __init__(self):
        """Initialize failure taxonomy"""
        self.failure_records: List[FailureRecord] = []
    
    def categorize_failure(
        self,
        failure_type: str,
        error_message: str,
        tool_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> FailureCategory:
        """
        Categorize a failure based on type and error message.
        
        Args:
            failure_type: Type of failure
            error_message: Error message
            tool_name: Optional tool name
            context: Optional context
            
        Returns:
            Failure category
        """
        error_lower = error_message.lower()
        
        if "timeout" in error_lower or "timed out" in error_lower:
            return FailureCategory.TIMEOUT
        elif "network" in error_lower or "connection" in error_lower:
            return FailureCategory.NETWORK
        elif "permission" in error_lower or "unauthorized" in error_lower or "forbidden" in error_lower:
            return FailureCategory.PERMISSION
        elif "invalid" in error_lower or "validation" in error_lower:
            return FailureCategory.INPUT_ERROR
        elif "system" in error_lower or "internal" in error_lower:
            return FailureCategory.SYSTEM_ERROR
        else:
            # Default: try to determine if transient
            if any(keyword in error_lower for keyword in ["temporary", "retry", "busy", "overloaded"]):
                return FailureCategory.TRANSIENT
            else:
                return FailureCategory.PERMANENT
    
    def calculate_retry_score(
        self,
        category: FailureCategory,
        failure_type: str,
        retry_count: int = 0
    ) -> float:
        """
        Calculate retry score (0.0 to 1.0) indicating likelihood of success on retry.
        
        Args:
            category: Failure category
            failure_type: Type of failure
            retry_count: Number of previous retries
            
        Returns:
            Retry score (0.0 = unlikely to succeed, 1.0 = very likely to succeed)
        """
        # Base scores by category
        base_scores = {
            FailureCategory.TRANSIENT: 0.8,
            FailureCategory.TIMEOUT: 0.7,
            FailureCategory.NETWORK: 0.6,
            FailureCategory.INPUT_ERROR: 0.2,
            FailureCategory.PERMISSION: 0.1,
            FailureCategory.SYSTEM_ERROR: 0.3,
            FailureCategory.PERMANENT: 0.1
        }
        
        base_score = base_scores.get(category, 0.5)
        
        # Reduce score with each retry
        retry_penalty = retry_count * 0.2
        final_score = max(0.0, base_score - retry_penalty)
        
        return final_score
    
    def get_retry_strategy(
        self,
        category: FailureCategory,
        retry_count: int = 0
    ) -> RetryStrategy:
        """
        Get recommended retry strategy for a failure.
        
        Args:
            category: Failure category
            retry_count: Number of previous retries
            
        Returns:
            Recommended retry strategy
        """
        # Don't retry if too many attempts
        if retry_count >= 3:
            return RetryStrategy.NO_RETRY
        
        # Don't retry permanent or permission errors
        if category in [FailureCategory.PERMANENT, FailureCategory.PERMISSION]:
            return RetryStrategy.NO_RETRY
        
        # Use exponential backoff for transient/timeout/network
        if category in [FailureCategory.TRANSIENT, FailureCategory.TIMEOUT, FailureCategory.NETWORK]:
            return RetryStrategy.EXPONENTIAL_BACKOFF
        
        # Use linear backoff for system errors
        if category == FailureCategory.SYSTEM_ERROR:
            return RetryStrategy.LINEAR_BACKOFF
        
        # Input errors might benefit from immediate retry with corrected input
        if category == FailureCategory.INPUT_ERROR:
            return RetryStrategy.IMMEDIATE
        
        return RetryStrategy.NO_RETRY
    
    def record_failure(
        self,
        failure_type: str,
        error_message: str,
        tool_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> FailureRecord:
        """
        Record a failure and categorize it.
        
        Args:
            failure_type: Type of failure
            error_message: Error message
            tool_name: Optional tool name
            context: Optional context
            
        Returns:
            Failure record
        """
        category = self.categorize_failure(failure_type, error_message, tool_name, context)
        retry_score = self.calculate_retry_score(category, failure_type)
        retry_strategy = self.get_retry_strategy(category)
        
        record = FailureRecord(
            failure_type=failure_type,
            category=category,
            tool_name=tool_name,
            error_message=error_message,
            timestamp=datetime.utcnow().isoformat(),
            context=context or {},
            retry_strategy=retry_strategy,
            retry_score=retry_score
        )
        
        self.failure_records.append(record)
        return record
    
    def get_failure_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about recorded failures.
        
        Returns:
            Dictionary with failure statistics
        """
        category_counts = {}
        strategy_counts = {}
        total_score = 0.0
        
        for record in self.failure_records:
            category = record.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
            
            strategy = record.retry_strategy.value
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
            total_score += record.retry_score
        
        avg_retry_score = total_score / len(self.failure_records) if self.failure_records else 0.0
        
        return {
            "total_failures": len(self.failure_records),
            "category_distribution": category_counts,
            "strategy_distribution": strategy_counts,
            "average_retry_score": avg_retry_score
        }

