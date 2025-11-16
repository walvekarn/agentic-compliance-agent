"""
Benchmark Runner Module

Runs benchmark cases and calculates performance metrics.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.agentic_engine.orchestrator import AgenticAIOrchestrator
from .benchmark_cases import BenchmarkCases, BenchmarkCase, BenchmarkLevel


class BenchmarkRunner:
    """
    Runs benchmark cases and calculates performance metrics.
    """
    
    def __init__(
        self,
        orchestrator: Optional[AgenticAIOrchestrator] = None,
        db_session: Optional[Any] = None
    ):
        """
        Initialize benchmark runner.
        
        Args:
            orchestrator: Optional orchestrator instance
            db_session: Optional database session
        """
        self.orchestrator = orchestrator or AgenticAIOrchestrator(db_session=db_session)
        self.db_session = db_session
    
    def run_benchmark_case(
        self,
        case: BenchmarkCase,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Run a single benchmark case.
        
        Args:
            case: Benchmark case to run
            max_iterations: Maximum iterations
            
        Returns:
            Dictionary with execution results and metrics
        """
        start_time = time.time()
        
        # Prepare context
        context = {
            "entity": case.entity_context,
            "task": case.task_context
        }
        
        try:
            # Run orchestrator
            result = self.orchestrator.run(
                task=case.task_description,
                context=context,
                max_iterations=max_iterations
            )
            
            execution_time = time.time() - start_time
            
            # Calculate metrics
            metrics = self._calculate_metrics(result, execution_time, case)
            
            return {
                "case_id": case.case_id,
                "case": case.to_dict(),
                "status": "success",
                "execution_time": execution_time,
                "result": result,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "case_id": case.case_id,
                "case": case.to_dict(),
                "status": "error",
                "execution_time": execution_time,
                "result": None,
                "metrics": {
                    "accuracy": 0.0,
                    "reasoning_depth_score": 0.0,
                    "tool_precision_score": 0.0,
                    "reflection_correction_score": 0.0,
                    "average_execution_time": execution_time
                },
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _calculate_metrics(
        self,
        result: Dict[str, Any],
        execution_time: float,
        case: BenchmarkCase
    ) -> Dict[str, Any]:
        """
        Calculate performance metrics from execution result.
        
        Args:
            result: Execution result from orchestrator
            execution_time: Total execution time
            case: Original benchmark case
            
        Returns:
            Dictionary with calculated metrics
        """
        # Accuracy: based on confidence score and completion
        confidence_score = result.get("confidence_score", 0.0)
        step_outputs = result.get("step_outputs", [])
        successful_steps = sum(1 for s in step_outputs if s.get("status") == "success")
        total_steps = len(step_outputs)
        step_success_rate = successful_steps / total_steps if total_steps > 0 else 0.0
        accuracy = (confidence_score * 0.6 + step_success_rate * 0.4)
        
        # Reasoning depth score: based on number of reasoning passes
        reflections = result.get("reflections", [])
        reasoning_passes = len(reflections)
        # Normalize: 0-10 passes = 0.0-1.0 score
        reasoning_depth_score = min(1.0, reasoning_passes / 10.0)
        
        # Tool precision score: based on tool usage and success
        tool_metrics = self.orchestrator.tool_metrics
        total_tool_calls = tool_metrics.get("total_tool_calls", 0)
        tool_success_count = sum(tool_metrics.get("tool_success_count", {}).values())
        tool_error_count = sum(tool_metrics.get("tool_error_count", {}).values())
        tool_precision_score = tool_success_count / (total_tool_calls + 1) if total_tool_calls > 0 else 0.0
        
        # Reflection correction score: based on reflections requiring retry
        reflections_requiring_retry = sum(
            1 for r in reflections if r.get("requires_retry", False)
        )
        total_reflections = len(reflections)
        # Higher score if reflections catch issues (require retry when needed)
        # But also penalize if too many retries needed
        if total_reflections > 0:
            retry_rate = reflections_requiring_retry / total_reflections
            # Optimal is some retries (0.1-0.3), too few or too many is bad
            if 0.1 <= retry_rate <= 0.3:
                reflection_correction_score = 1.0
            elif retry_rate < 0.1:
                reflection_correction_score = retry_rate * 10  # Scale up
            else:
                reflection_correction_score = max(0.0, 1.0 - (retry_rate - 0.3) * 2)  # Penalize excess
        else:
            reflection_correction_score = 0.5  # Neutral if no reflections
        
        return {
            "accuracy": round(accuracy, 3),
            "reasoning_depth_score": round(reasoning_depth_score, 3),
            "tool_precision_score": round(tool_precision_score, 3),
            "reflection_correction_score": round(reflection_correction_score, 3),
            "average_execution_time": round(execution_time, 2),
            "confidence_score": round(confidence_score, 3),
            "reasoning_passes": reasoning_passes,
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "tool_calls": total_tool_calls,
            "tool_success_rate": round(tool_success_count / (total_tool_calls + 1), 3) if total_tool_calls > 0 else 0.0
        }
    
    def run_benchmark_suite(
        self,
        levels: Optional[List[BenchmarkLevel]] = None,
        max_cases_per_level: int = 10,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Run a benchmark suite.
        
        Args:
            levels: Optional list of levels to run (all if None)
            max_cases_per_level: Maximum cases per level
            max_iterations: Maximum iterations per case
            
        Returns:
            Dictionary with all benchmark results and aggregated metrics
        """
        if levels is None:
            levels = [BenchmarkLevel.LIGHT, BenchmarkLevel.MEDIUM, BenchmarkLevel.HEAVY]
        
        all_results = []
        
        # Get and run cases for each level
        for level in levels:
            cases = BenchmarkCases.get_cases_by_level(level)
            cases_to_run = cases[:max_cases_per_level]
            
            for case in cases_to_run:
                result = self.run_benchmark_case(case, max_iterations)
                all_results.append(result)
        
        # Calculate aggregated metrics
        total_cases = len(all_results)
        successful_cases = sum(1 for r in all_results if r["status"] == "success")
        
        if successful_cases > 0:
            # Aggregate metrics from successful cases
            metrics_list = [r["metrics"] for r in all_results if r["status"] == "success"]
            
            avg_accuracy = sum(m.get("accuracy", 0) for m in metrics_list) / len(metrics_list)
            avg_reasoning_depth = sum(m.get("reasoning_depth_score", 0) for m in metrics_list) / len(metrics_list)
            avg_tool_precision = sum(m.get("tool_precision_score", 0) for m in metrics_list) / len(metrics_list)
            avg_reflection_correction = sum(m.get("reflection_correction_score", 0) for m in metrics_list) / len(metrics_list)
            avg_execution_time = sum(m.get("average_execution_time", 0) for m in metrics_list) / len(metrics_list)
        else:
            avg_accuracy = 0.0
            avg_reasoning_depth = 0.0
            avg_tool_precision = 0.0
            avg_reflection_correction = 0.0
            avg_execution_time = 0.0
        
        # Results by level
        results_by_level = {}
        for level in levels:
            level_results = [r for r in all_results if r["case"]["level"] == level.value]
            results_by_level[level.value] = {
                "total": len(level_results),
                "successful": sum(1 for r in level_results if r["status"] == "success"),
                "failed": sum(1 for r in level_results if r["status"] == "error")
            }
        
        return {
            "benchmark_results": all_results,
            "summary": {
                "total_cases": total_cases,
                "successful_cases": successful_cases,
                "failed_cases": total_cases - successful_cases,
                "success_rate": successful_cases / total_cases if total_cases > 0 else 0.0,
                "average_accuracy": round(avg_accuracy, 3),
                "average_reasoning_depth_score": round(avg_reasoning_depth, 3),
                "average_tool_precision_score": round(avg_tool_precision, 3),
                "average_reflection_correction_score": round(avg_reflection_correction, 3),
                "average_execution_time": round(avg_execution_time, 2),
                "results_by_level": results_by_level
            },
            "timestamp": datetime.utcnow().isoformat()
        }

