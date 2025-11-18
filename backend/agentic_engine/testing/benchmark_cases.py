"""
Benchmark Cases Module

Defines benchmark test cases for evaluating agentic engine performance.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class BenchmarkLevel(str, Enum):
    """Benchmark complexity levels"""
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"


@dataclass
class BenchmarkCase:
    """
    Represents a benchmark test case.
    
    Attributes:
        case_id: Unique identifier for the case
        title: Human-readable title
        description: Detailed description
        level: Complexity level (light/medium/heavy)
        task_description: The compliance task to analyze
        entity_context: Entity context data
        task_context: Task context data
        expected_metrics: Expected performance metrics
        metadata: Additional metadata
    """
    case_id: str
    title: str
    description: str
    level: BenchmarkLevel
    task_description: str
    entity_context: Dict[str, Any] = field(default_factory=dict)
    task_context: Dict[str, Any] = field(default_factory=dict)
    expected_metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "case_id": self.case_id,
            "title": self.title,
            "description": self.description,
            "level": self.level.value,
            "task_description": self.task_description,
            "entity_context": self.entity_context,
            "task_context": self.task_context,
            "expected_metrics": self.expected_metrics,
            "metadata": self.metadata
        }


class BenchmarkCases:
    """Collection of benchmark test cases"""
    
    @staticmethod
    def get_light_cases() -> List[BenchmarkCase]:
        """Get light complexity benchmark cases"""
        return [
            BenchmarkCase(
                case_id="light_001",
                title="Basic GDPR Article 30",
                description="Simple GDPR Article 30 records requirement",
                level=BenchmarkLevel.LIGHT,
                task_description="Implement GDPR Article 30 records of processing activities",
                entity_context={
                    "entity_name": "SimpleCorp",
                    "entity_type": "PRIVATE_COMPANY",
                    "locations": ["EU"],
                    "industry": "TECHNOLOGY",
                    "has_personal_data": True,
                    "is_regulated": False
                },
                task_context={
                    "task_description": "Implement GDPR Article 30 records",
                    "task_category": "DATA_PROTECTION"
                },
                expected_metrics={
                    "max_execution_time": 30.0,
                    "min_confidence": 0.7
                }
            ),
            BenchmarkCase(
                case_id="light_002",
                title="Single Jurisdiction Compliance",
                description="Compliance check for single jurisdiction",
                level=BenchmarkLevel.LIGHT,
                task_description="Analyze data protection requirements for US operations",
                entity_context={
                    "entity_name": "USCorp",
                    "entity_type": "PRIVATE_COMPANY",
                    "locations": ["US"],
                    "industry": "TECHNOLOGY",
                    "has_personal_data": True
                },
                task_context={
                    "task_description": "US data protection compliance",
                    "task_category": "DATA_PROTECTION"
                },
                expected_metrics={
                    "max_execution_time": 25.0,
                    "min_confidence": 0.7
                }
            )
        ]
    
    @staticmethod
    def get_medium_cases() -> List[BenchmarkCase]:
        """Get medium complexity benchmark cases"""
        return [
            BenchmarkCase(
                case_id="medium_001",
                title="Multi-Jurisdiction GDPR",
                description="GDPR compliance across multiple EU countries",
                level=BenchmarkLevel.MEDIUM,
                task_description="Analyze GDPR compliance requirements for operations in Germany, France, and Italy",
                entity_context={
                    "entity_name": "EuroCorp",
                    "entity_type": "PRIVATE_COMPANY",
                    "locations": ["DE", "FR", "IT"],
                    "industry": "FINANCE",
                    "has_personal_data": True,
                    "is_regulated": True,
                    "employee_count": 500
                },
                task_context={
                    "task_description": "Multi-jurisdiction GDPR compliance",
                    "task_category": "DATA_PROTECTION"
                },
                expected_metrics={
                    "max_execution_time": 60.0,
                    "min_confidence": 0.75
                }
            ),
            BenchmarkCase(
                case_id="medium_002",
                title="Cross-Border Data Transfer",
                description="Compliance analysis for cross-border data transfers",
                level=BenchmarkLevel.MEDIUM,
                task_description="Assess compliance requirements for transferring personal data from EU to US",
                entity_context={
                    "entity_name": "GlobalData",
                    "entity_type": "PRIVATE_COMPANY",
                    "locations": ["EU", "US"],
                    "industry": "TECHNOLOGY",
                    "has_personal_data": True,
                    "is_regulated": False
                },
                task_context={
                    "task_description": "Cross-border data transfer compliance",
                    "task_category": "DATA_PROTECTION"
                },
                expected_metrics={
                    "max_execution_time": 55.0,
                    "min_confidence": 0.75
                }
            )
        ]
    
    @staticmethod
    def get_heavy_cases() -> List[BenchmarkCase]:
        """Get heavy complexity benchmark cases"""
        return [
            BenchmarkCase(
                case_id="heavy_001",
                title="Complex Multi-Region Compliance",
                description="Comprehensive compliance across US, EU, UK, and APAC",
                level=BenchmarkLevel.HEAVY,
                task_description="Analyze comprehensive compliance requirements for data protection, financial regulations, and industry-specific requirements across US, EU, UK, and Singapore",
                entity_context={
                    "entity_name": "MegaCorp",
                    "entity_type": "PUBLIC_COMPANY",
                    "locations": ["US", "EU", "UK", "SG"],
                    "industry": "FINANCE",
                    "has_personal_data": True,
                    "is_regulated": True,
                    "employee_count": 5000,
                    "annual_revenue": 1000000000,
                    "previous_violations": 2
                },
                task_context={
                    "task_description": "Multi-region comprehensive compliance",
                    "task_category": "DATA_PROTECTION"
                },
                expected_metrics={
                    "max_execution_time": 120.0,
                    "min_confidence": 0.8
                }
            ),
            BenchmarkCase(
                case_id="heavy_002",
                title="High-Risk Entity Assessment",
                description="Comprehensive risk assessment for high-risk entity",
                level=BenchmarkLevel.HEAVY,
                task_description="Perform comprehensive compliance risk assessment for entity with multiple previous violations and complex regulatory requirements",
                entity_context={
                    "entity_name": "RiskCorp",
                    "entity_type": "PRIVATE_COMPANY",
                    "locations": ["US", "EU", "UK"],
                    "industry": "HEALTHCARE",
                    "has_personal_data": True,
                    "is_regulated": True,
                    "employee_count": 2000,
                    "previous_violations": 5
                },
                task_context={
                    "task_description": "Comprehensive risk assessment",
                    "task_category": "DATA_PROTECTION"
                },
                expected_metrics={
                    "max_execution_time": 100.0,
                    "min_confidence": 0.8
                }
            )
        ]
    
    @staticmethod
    def get_all_cases() -> List[BenchmarkCase]:
        """Get all benchmark cases"""
        cases = []
        cases.extend(BenchmarkCases.get_light_cases())
        cases.extend(BenchmarkCases.get_medium_cases())
        cases.extend(BenchmarkCases.get_heavy_cases())
        return cases
    
    @staticmethod
    def get_cases_by_level(level: BenchmarkLevel) -> List[BenchmarkCase]:
        """Get cases by complexity level"""
        if level == BenchmarkLevel.LIGHT:
            return BenchmarkCases.get_light_cases()
        elif level == BenchmarkLevel.MEDIUM:
            return BenchmarkCases.get_medium_cases()
        elif level == BenchmarkLevel.HEAVY:
            return BenchmarkCases.get_heavy_cases()
        else:
            return []

