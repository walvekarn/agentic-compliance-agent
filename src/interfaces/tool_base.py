"""
Tool Base Interface

Abstract base class for all tools to enable interface-driven access.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ToolResult:
    """Standard result structure for tool execution"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ToolBase(ABC):
    """
    Base interface for all tools.
    
    All tools should implement this interface to ensure
    consistent tool access patterns.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get tool name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get tool description"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with execution results
        """
        pass
    
    def validate_input(self, **kwargs) -> bool:
        """
        Validate input parameters (optional override).
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            True if valid, False otherwise
        """
        return True

