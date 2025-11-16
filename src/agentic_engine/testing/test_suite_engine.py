"""
Test Suite Engine Module

Generates and runs test scenarios through the orchestrator, collecting metrics.
"""

import time
import random
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.agentic_engine.orchestrator import AgenticAIOrchestrator
from .test_scenario import TestScenario, ComplexityLevel


class TestSuiteEngine:
    """
    Engine for generating and running test scenarios through the orchestrator.
    
    Generates both random and deterministic test scenarios, executes them
    through the orchestrator, and collects comprehensive metrics.
    """
    
    def __init__(self, orchestrator: Optional[AgenticAIOrchestrator] = None, db_session: Optional[Any] = None):
        """
        Initialize the test suite engine.
        
        Args:
            orchestrator: Optional orchestrator instance (creates new if None)
            db_session: Optional database session for orchestrator
        """
        self.orchestrator = orchestrator or AgenticAIOrchestrator(db_session=db_session)
        self.db_session = db_session
        
        # Predefined deterministic scenarios
        self.deterministic_scenarios = self._create_deterministic_scenarios()
    
    def _create_deterministic_scenarios(self) -> List[TestScenario]:
        """Create a set of deterministic test scenarios"""
        return [
            TestScenario(
                title="GDPR Article 30 Records",
                description="Test basic GDPR Article 30 records of processing activities requirement",
                required_tools=["entity_tool", "task_tool"],
                complexity=ComplexityLevel.LOW,
                expected_outputs={
                    "plan": "Should generate 3-7 step plan",
                    "entity_analysis": "Should analyze entity context",
                    "recommendation": "Should provide actionable recommendation"
                },
                task_description="Implement GDPR Article 30 records of processing activities",
                entity_context={
                    "entity_name": "TestCorp",
                    "entity_type": "PRIVATE_COMPANY",
                    "locations": ["EU"],
                    "industry": "TECHNOLOGY",
                    "has_personal_data": True
                },
                task_context={
                    "task_description": "Implement GDPR Article 30 records",
                    "task_category": "DATA_PROTECTION"
                }
            ),
            TestScenario(
                title="Multi-Jurisdiction Compliance",
                description="Test compliance analysis across multiple jurisdictions",
                required_tools=["entity_tool", "calendar_tool", "task_tool"],
                complexity=ComplexityLevel.MEDIUM,
                expected_outputs={
                    "plan": "Should handle multiple jurisdictions",
                    "jurisdiction_analysis": "Should analyze each jurisdiction",
                    "recommendation": "Should provide jurisdiction-specific guidance"
                },
                task_description="Analyze compliance requirements for US, EU, and UK operations",
                entity_context={
                    "entity_name": "GlobalTech",
                    "entity_type": "PRIVATE_COMPANY",
                    "locations": ["US", "EU", "UK"],
                    "industry": "TECHNOLOGY",
                    "has_personal_data": True,
                    "is_regulated": True
                },
                task_context={
                    "task_description": "Multi-jurisdiction compliance analysis",
                    "task_category": "DATA_PROTECTION"
                }
            ),
            TestScenario(
                title="High-Risk Entity Analysis",
                description="Test analysis for high-risk entity with violations",
                required_tools=["entity_tool", "task_tool"],
                complexity=ComplexityLevel.HIGH,
                expected_outputs={
                    "plan": "Should include risk assessment steps",
                    "risk_analysis": "Should identify high-risk factors",
                    "recommendation": "Should prioritize risk mitigation"
                },
                task_description="Analyze compliance posture for entity with previous violations",
                entity_context={
                    "entity_name": "RiskCorp",
                    "entity_type": "PRIVATE_COMPANY",
                    "locations": ["US", "EU"],
                    "industry": "FINANCE",
                    "has_personal_data": True,
                    "is_regulated": True,
                    "previous_violations": 3
                },
                task_context={
                    "task_description": "Comprehensive risk assessment",
                    "task_category": "DATA_PROTECTION"
                }
            )
        ]
    
    def generate_random_scenario(self, complexity: Optional[ComplexityLevel] = None) -> TestScenario:
        """
        Generate a random test scenario.
        
        Args:
            complexity: Optional complexity level (random if None)
            
        Returns:
            Randomly generated test scenario
        """
        if complexity is None:
            complexity = random.choice(list(ComplexityLevel))
        
        # Random entity types
        entity_types = ["PRIVATE_COMPANY", "PUBLIC_COMPANY", "NONPROFIT"]
        industries = ["TECHNOLOGY", "FINANCE", "HEALTHCARE", "RETAIL"]
        locations_pools = [
            ["US"],
            ["EU"],
            ["US", "EU"],
            ["US", "EU", "UK"],
            ["US", "CA", "MX"]
        ]
        
        # Random task categories
        task_categories = ["DATA_PROTECTION", "FINANCIAL_COMPLIANCE", "HEALTHCARE_COMPLIANCE"]
        task_templates = [
            "Implement {category} compliance framework",
            "Analyze {category} requirements for {location}",
            "Assess {category} risk for entity operations"
        ]
        
        entity_type = random.choice(entity_types)
        industry = random.choice(industries)
        locations = random.choice(locations_pools)
        task_category = random.choice(task_categories)
        task_template = random.choice(task_templates)
        
        task_description = task_template.format(
            category=task_category,
            location=locations[0] if locations else "US"
        )
        
        # Determine required tools based on complexity
        required_tools = ["entity_tool", "task_tool"]
        if complexity == ComplexityLevel.MEDIUM or complexity == ComplexityLevel.HIGH:
            required_tools.append("calendar_tool")
        if complexity == ComplexityLevel.HIGH:
            required_tools.append("http_tool")
        
        return TestScenario(
            title=f"Random {complexity.value.title()} Scenario",
            description=f"Randomly generated {complexity.value} complexity test scenario",
            required_tools=required_tools,
            complexity=complexity,
            expected_outputs={
                "plan": "Should generate valid plan",
                "execution": "Should complete execution",
                "recommendation": "Should provide recommendation"
            },
            task_description=task_description,
            entity_context={
                "entity_name": f"TestEntity_{random.randint(1000, 9999)}",
                "entity_type": entity_type,
                "locations": locations,
                "industry": industry,
                "has_personal_data": random.choice([True, False]),
                "is_regulated": random.choice([True, False]),
                "previous_violations": random.randint(0, 5) if complexity == ComplexityLevel.HIGH else 0
            },
            task_context={
                "task_description": task_description,
                "task_category": task_category
            },
            metadata={
                "generated_at": datetime.utcnow().isoformat(),
                "random_seed": random.randint(1, 10000)
            }
        )
    
    def run_scenario(
        self, 
        scenario: TestScenario,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Run a single test scenario through the orchestrator.
        
        Args:
            scenario: The test scenario to run
            max_iterations: Maximum iterations for orchestrator
            
        Returns:
            Dictionary containing execution results and metrics
        """
        start_time = time.time()
        
        # Prepare context
        context = {
            "entity": scenario.entity_context,
            "task": scenario.task_context
        }
        
        # Prepare task description
        task_description = scenario.task_description
        if not task_description:
            task_description = f"Test scenario: {scenario.title}"
        
        # Run orchestrator
        try:
            result = self.orchestrator.run(
                task=task_description,
                context=context,
                max_iterations=max_iterations
            )
            
            execution_time = time.time() - start_time
            
            # Extract metrics
            tools_used = []
            reasoning_passes = 0
            errors = []
            success = True
            
            # Collect tools used from step outputs
            for step_output in result.get("step_outputs", []):
                step_tools = step_output.get("tools_used", [])
                tools_used.extend(step_tools)
                
                if step_output.get("status") != "success":
                    success = False
                    if "error" in step_output:
                        errors.append(step_output["error"])
            
            # Count reasoning passes (reflections)
            reasoning_passes = len(result.get("reflections", []))
            
            # Get tool metrics from orchestrator
            tool_metrics = self.orchestrator.tool_metrics.copy()
            
            # Check if required tools were used
            tools_used_set = set(tools_used)
            required_tools_set = set(scenario.required_tools)
            missing_tools = required_tools_set - tools_used_set
            
            return {
                "scenario": scenario.to_dict(),
                "status": "success" if success else "partial",
                "execution_time": execution_time,
                "tools_used": list(set(tools_used)),  # Unique tools
                "required_tools": scenario.required_tools,
                "missing_tools": list(missing_tools),
                "reasoning_passes": reasoning_passes,
                "success": success,
                "errors": errors,
                "result": result,
                "tool_metrics": tool_metrics,
                "confidence_score": result.get("confidence_score", 0.0),
                "plan_steps": len(result.get("plan", [])),
                "executed_steps": len(result.get("step_outputs", [])),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "scenario": scenario.to_dict(),
                "status": "error",
                "execution_time": execution_time,
                "tools_used": [],
                "required_tools": scenario.required_tools,
                "missing_tools": scenario.required_tools,
                "reasoning_passes": 0,
                "success": False,
                "errors": [str(e)],
                "result": None,
                "tool_metrics": {},
                "confidence_score": 0.0,
                "plan_steps": 0,
                "executed_steps": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "exception": str(e)
            }
    
    def run_test_suite(
        self,
        scenarios: Optional[List[TestScenario]] = None,
        num_random: int = 5,
        complexity_distribution: Optional[Dict[ComplexityLevel, int]] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Run a suite of test scenarios.
        
        Args:
            scenarios: Optional list of specific scenarios to run
            num_random: Number of random scenarios to generate and run
            complexity_distribution: Optional dict mapping complexity to count
            max_iterations: Maximum iterations per scenario
            
        Returns:
            Dictionary containing all test results and aggregated metrics
        """
        all_results = []
        
        # Run deterministic scenarios
        if scenarios is None:
            scenarios = self.deterministic_scenarios.copy()
        
        for scenario in scenarios:
            result = self.run_scenario(scenario, max_iterations)
            all_results.append(result)
        
        # Generate and run random scenarios
        if complexity_distribution is None:
            complexity_distribution = {
                ComplexityLevel.LOW: num_random // 3,
                ComplexityLevel.MEDIUM: num_random // 3,
                ComplexityLevel.HIGH: num_random - 2 * (num_random // 3)
            }
        
        for complexity, count in complexity_distribution.items():
            for _ in range(count):
                random_scenario = self.generate_random_scenario(complexity)
                result = self.run_scenario(random_scenario, max_iterations)
                all_results.append(result)
        
        # Calculate aggregated metrics
        total_tests = len(all_results)
        successful_tests = sum(1 for r in all_results if r["success"])
        failed_tests = total_tests - successful_tests
        
        total_execution_time = sum(r["execution_time"] for r in all_results)
        avg_execution_time = total_execution_time / total_tests if total_tests > 0 else 0
        
        total_reasoning_passes = sum(r["reasoning_passes"] for r in all_results)
        avg_reasoning_passes = total_reasoning_passes / total_tests if total_tests > 0 else 0
        
        total_confidence = sum(r["confidence_score"] for r in all_results)
        avg_confidence = total_confidence / total_tests if total_tests > 0 else 0
        
        # Tool usage statistics
        all_tools_used = []
        for result in all_results:
            all_tools_used.extend(result["tools_used"])
        
        tool_usage_counts = {}
        for tool in all_tools_used:
            tool_usage_counts[tool] = tool_usage_counts.get(tool, 0) + 1
        
        # Error distribution
        error_types = {}
        for result in all_results:
            for error in result["errors"]:
                error_type = error.split(":")[0] if ":" in error else "Unknown"
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "test_results": all_results,
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
                "total_execution_time": total_execution_time,
                "avg_execution_time": avg_execution_time,
                "avg_reasoning_passes": avg_reasoning_passes,
                "avg_confidence": avg_confidence,
                "tool_usage_counts": tool_usage_counts,
                "error_distribution": error_types
            },
            "timestamp": datetime.utcnow().isoformat()
        }

