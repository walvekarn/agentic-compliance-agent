"""
Interfaces Module

Defines interfaces/abstractions to break circular dependencies and enable loose coupling.
"""

from .tool_base import ToolBase, ToolResult

__all__ = [
    "ToolBase",
    "ToolResult",
]

