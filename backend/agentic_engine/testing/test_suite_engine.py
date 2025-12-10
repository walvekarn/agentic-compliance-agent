"""
Test Suite Engine Module

Runs curated test scenarios and compares actual vs expected results.
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.agent.decision_engine import DecisionEngine
from backend.agent.risk_models import EntityContext, TaskContext, DecisionAnalysis
from .scenario_loader import load_scenarios_from_directory


class TestResult:
    """Result of a single test scenario"""
    
    def __init__(
        self,
        scenario: Dict[str, Any],
        actual_result: Optional[DecisionAnalysis] = None,
        execution_time: float = 0.0,
        error: Optional[str] = None
    ):
        self.scenario = scenario
        self.actual_result = actual_result
        self.execution_time = execution_time
        self.error = error
        
        # Expected values
        self.expected_decision = scenario.get("expected_decision")
        self.expected_risk_level = scenario.get("expected_risk_level")
        self.expected_min_confidence = scenario.get("expected_min_confidence", 0.0)
        
        # Actual values
        if actual_result:
            self.actual_decision = actual_result.decision.value
            self.actual_risk_level = actual_result.risk_level.value
            self.actual_confidence = actual_result.confidence
        else:
            self.actual_decision = None
            self.actual_risk_level = None
            self.actual_confidence = None
        
        # Scoring
        self.decision_correct = self._check_decision()
        self.risk_level_correct = self._check_risk_level()
        self.confidence_adequate = self._check_confidence()
        self.passed = self.decision_correct and self.risk_level_correct and self.confidence_adequate
    
    def _check_decision(self) -> bool:
        """Check if decision matches expected"""
        if not self.actual_decision or not self.expected_decision:
            return False
        return self.actual_decision == self.expected_decision
    
    def _check_risk_level(self) -> bool:
        """Check if risk level matches expected"""
        if not self.actual_risk_level or not self.expected_risk_level:
            return False
        return self.actual_risk_level == self.expected_risk_level
    
    def _check_confidence(self) -> bool:
        """Check if confidence meets minimum threshold"""
        if self.actual_confidence is None:
            return False
        return self.actual_confidence >= self.expected_min_confidence
    
    def get_diff(self) -> Dict[str, Any]:
        """Get differences between expected and actual"""
        diff = {}
        
        if not self.decision_correct:
            diff["decision"] = {
                "expected": self.expected_decision,
                "actual": self.actual_decision
            }
        
        if not self.risk_level_correct:
            diff["risk_level"] = {
                "expected": self.expected_risk_level,
                "actual": self.actual_risk_level
            }
        
        if not self.confidence_adequate:
            diff["confidence"] = {
                "expected_min": self.expected_min_confidence,
                "actual": self.actual_confidence,
                "deviation": self.actual_confidence - self.expected_min_confidence if self.actual_confidence is not None else None
            }
        
        return diff
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "scenario": self.scenario,
            "passed": self.passed,
            "decision_correct": self.decision_correct,
            "risk_level_correct": self.risk_level_correct,
            "confidence_adequate": self.confidence_adequate,
            "expected": {
                "decision": self.expected_decision,
                "risk_level": self.expected_risk_level,
                "min_confidence": self.expected_min_confidence
            },
            "actual": {
                "decision": self.actual_decision,
                "risk_level": self.actual_risk_level,
                "confidence": self.actual_confidence
            },
            "diff": self.get_diff(),
            "execution_time": self.execution_time,
            "error": self.error
        }


class TestSuiteEngine:
    """
    Engine for running curated test scenarios and comparing results.
    
    Loads scenarios from JSON files, runs them through the decision engine,
    and compares actual vs expected results.
    """
    
    def __init__(self, db_session: Optional[Any] = None):
        """
        Initialize the test suite engine.
        
        Args:
            db_session: Optional database session
        """
        self.decision_engine = DecisionEngine()
        self.db_session = db_session
    
    def run_scenario(
        self,
        scenario: Dict[str, Any]
    ) -> TestResult:
        """
        Run a single test scenario through the decision engine.
        
        Args:
            scenario: Scenario dictionary with input and expected results
            
        Returns:
            TestResult with comparison and scoring
        """
        start_time = time.time()
        
        try:
            # Extract input
            input_data = scenario.get("input", {})
            entity_data = input_data.get("entity", {})
            task_data = input_data.get("task", {})
            
            # Create EntityContext
            from backend.agent.risk_models import EntityType, IndustryCategory, Jurisdiction, TaskCategory
            
            # Convert location strings to Jurisdiction enum
            location_strings = entity_data.get("locations", ["US_FEDERAL"])
            jurisdictions = []
            for loc in location_strings:
                try:
                    # Try direct match first
                    jurisdictions.append(Jurisdiction(loc))
                except ValueError:
                    # Try common mappings
                    loc_mapping = {
                        "US": "US_FEDERAL",
                        "EU": "EU",
                        "UK": "UK",
                        "CA": "CANADA",
                        "AU": "AUSTRALIA"
                    }
                    mapped = loc_mapping.get(loc.upper(), "UNKNOWN")
                    try:
                        jurisdictions.append(Jurisdiction(mapped))
                    except ValueError:
                        jurisdictions.append(Jurisdiction.UNKNOWN)
            
            entity = EntityContext(
                name=entity_data.get("name", "TestEntity"),
                entity_type=EntityType(entity_data.get("entity_type", "PRIVATE_COMPANY")),
                industry=IndustryCategory(entity_data.get("industry", "TECHNOLOGY")),
                jurisdictions=jurisdictions,
                has_personal_data=entity_data.get("has_personal_data", False),
                is_regulated=entity_data.get("is_regulated", False),
                employee_count=entity_data.get("employee_count"),
                previous_violations=entity_data.get("previous_violations", 0)
            )
            
            # Create TaskContext
            task = TaskContext(
                description=task_data.get("description", ""),
                category=TaskCategory(task_data.get("category", "GENERAL_INQUIRY"))
            )
            
            # Run decision engine
            analysis = self.decision_engine.analyze_and_decide(entity, task)
            
            execution_time = time.time() - start_time
            
            return TestResult(
                scenario=scenario,
                actual_result=analysis,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                scenario=scenario,
                actual_result=None,
                execution_time=execution_time,
                error=str(e)
            )
    
    def run_test_suite(
        self,
        scenarios: Optional[List[Dict[str, Any]]] = None,
        scenarios_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a suite of test scenarios.
        
        Args:
            scenarios: Optional list of scenario dictionaries (loads from files if None)
            scenarios_dir: Optional path to scenarios directory
            
        Returns:
            Dictionary containing all test results and aggregated metrics
        """
        # Load scenarios if not provided
        if scenarios is None:
            from pathlib import Path
            if scenarios_dir:
                scenarios_path = Path(scenarios_dir)
            else:
                scenarios_path = None
            scenarios = load_scenarios_from_directory(scenarios_path)
        
        if not scenarios:
            return {
                "test_results": [],
                "summary": {
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 0,
                    "pass_rate": 0.0,
                    "decision_accuracy": 0.0,
                    "risk_level_accuracy": 0.0,
                    "confidence_adequacy": 0.0,
                    "avg_execution_time": 0.0,
                    "confidence_deviations": []
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Run all scenarios
        test_results = []
        for scenario in scenarios:
            result = self.run_scenario(scenario)
            test_results.append(result)
        
        # Calculate aggregated metrics
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r.passed)
        failed_tests = total_tests - passed_tests
        
        decision_correct = sum(1 for r in test_results if r.decision_correct)
        risk_level_correct = sum(1 for r in test_results if r.risk_level_correct)
        confidence_adequate = sum(1 for r in test_results if r.confidence_adequate)
        
        total_execution_time = sum(r.execution_time for r in test_results)
        avg_execution_time = total_execution_time / total_tests if total_tests > 0 else 0
        
        # Calculate confidence deviations
        confidence_deviations = []
        for result in test_results:
            if result.actual_confidence is not None and result.expected_min_confidence is not None:
                deviation = result.actual_confidence - result.expected_min_confidence
                confidence_deviations.append({
                    "scenario": result.scenario.get("title", "Unknown"),
                    "expected_min": result.expected_min_confidence,
                    "actual": result.actual_confidence,
                    "deviation": deviation,
                    "adequate": deviation >= 0
                })
        
        # Get failures with diffs
        failures = []
        for result in test_results:
            if not result.passed:
                failures.append({
                    "scenario": result.scenario.get("title", "Unknown"),
                    "diff": result.get_diff(),
                    "error": result.error
                })
        
        return {
            "test_results": [r.to_dict() for r in test_results],
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "pass_rate": passed_tests / total_tests if total_tests > 0 else 0.0,
                "decision_accuracy": decision_correct / total_tests if total_tests > 0 else 0.0,
                "risk_level_accuracy": risk_level_correct / total_tests if total_tests > 0 else 0.0,
                "confidence_adequacy": confidence_adequate / total_tests if total_tests > 0 else 0.0,
                "avg_execution_time": avg_execution_time,
                "confidence_deviations": confidence_deviations,
                "failures": failures
            },
            "timestamp": datetime.utcnow().isoformat()
        }
