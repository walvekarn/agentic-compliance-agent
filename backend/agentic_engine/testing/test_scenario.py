"""
Test Scenario Module

Defines test scenario data structures for agentic engine testing.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class ComplexityLevel(str, Enum):
    """Complexity levels for test scenarios"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class TestScenario:
    """
    Represents a test scenario for the agentic engine.
    
    Attributes:
        title: Human-readable title for the scenario
        description: Detailed description of what the scenario tests
        required_tools: List of tool names that should be used
        complexity: Complexity level (low, medium, high)
        expected_outputs: Dictionary of expected output keys and descriptions
        task_description: The compliance task to analyze
        entity_context: Optional entity context data
        task_context: Optional task context data
        metadata: Additional metadata for the scenario
    """
    title: str
    description: str
    required_tools: List[str] = field(default_factory=list)
    complexity: ComplexityLevel = ComplexityLevel.MEDIUM
    expected_outputs: Dict[str, str] = field(default_factory=dict)
    task_description: str = ""
    entity_context: Optional[Dict[str, Any]] = field(default_factory=dict)
    task_context: Optional[Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to dictionary for serialization"""
        return {
            "title": self.title,
            "description": self.description,
            "required_tools": self.required_tools,
            "complexity": self.complexity.value,
            "expected_outputs": self.expected_outputs,
            "task_description": self.task_description,
            "entity_context": self.entity_context,
            "task_context": self.task_context,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestScenario":
        """Create scenario from dictionary"""
        return cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            required_tools=data.get("required_tools", []),
            complexity=ComplexityLevel(data.get("complexity", "medium")),
            expected_outputs=data.get("expected_outputs", {}),
            task_description=data.get("task_description", ""),
            entity_context=data.get("entity_context", {}),
            task_context=data.get("task_context", {}),
            metadata=data.get("metadata", {})
        )

