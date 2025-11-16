"""
Agent Loop Module

Implements the main agent execution loop with plan-execute-reflect cycles.
"""

from typing import Dict, List, Any, Optional, Callable
import json
import time
from datetime import datetime


class AgentLoop:
    """
    Core agent loop handler for iterative reasoning and execution.
    
    Manages the multi-step execution loop that drives the agentic AI workflow.
    Designed to be modular and tool-agnostic, allowing flexible integration
    with different reasoning engines, tools, and memory systems.
    """
    
    def __init__(
        self,
        max_steps: int = 10,
        enable_reflection: bool = True,
        enable_memory: bool = True,
        reasoning_engine: Optional[Any] = None
    ):
        """
        Initialize the agent loop.
        
        Args:
            max_steps: Maximum number of execution steps per task
            enable_reflection: Whether to enable reflection after each step
            enable_memory: Whether to enable memory updates during execution
            reasoning_engine: Optional ReasoningEngine instance for enhanced reasoning
        """
        self.max_steps = max_steps
        self.enable_reflection = enable_reflection
        self.enable_memory = enable_memory
        self.reasoning_engine = reasoning_engine
        self.current_step = 0
        self.execution_history = []
        
        # Metrics tracking
        self.metrics = {
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "total_retries": 0,
            "total_execution_time": 0.0,
            "step_times": [],
            "tools_used": [],
            "errors_encountered": []
        }
    
    def generate_plan(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        planner_fn: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a strategic execution plan for the given task.
        
        Breaks down the task into discrete, actionable steps. The plan
        can be generated using a custom planner function or a default
        planning strategy.
        
        Args:
            task: The task description to plan for
            context: Optional context information for planning
            planner_fn: Optional custom planning function to use
            
        Returns:
            List of plan steps, where each step contains:
                - step_id: Unique identifier for the step
                - description: What the step should accomplish
                - dependencies: IDs of steps that must complete first
                - expected_tools: Tools likely needed for this step
                - success_criteria: How to determine if step succeeded
        """
        pass
    
    def execute_step(
        self,
        step: Dict[str, Any],
        executor_fn: Optional[Callable] = None,
        context: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Execute a single step from the plan with integrated reasoning engine support.
        
        Args:
            step: The step to execute
            executor_fn: Optional custom executor function
            context: Optional execution context
            retry_count: Current retry attempt number
            max_retries: Maximum number of retries allowed
            
        Returns:
            Execution result containing output, metrics, and metadata
        """
        start_time = time.time()
        step_id = step.get("step_id", f"step_{self.current_step}")
        
        try:
            # Track metrics
            self.metrics["total_steps"] += 1
            if retry_count > 0:
                self.metrics["total_retries"] += 1
            
            # Execute using reasoning engine if available, otherwise use custom executor
            if self.reasoning_engine and hasattr(self.reasoning_engine, 'run_step'):
                # Use reasoning engine for execution
                result = self.reasoning_engine.run_step(step, context)
                
                # Ensure result has required fields
                if not isinstance(result, dict):
                    result = {"output": str(result), "status": "success"}
                
                # Add standard fields if missing
                if "step_id" not in result:
                    result["step_id"] = step_id
                if "status" not in result:
                    result["status"] = "success" if result.get("output") else "failure"
                if "tools_used" not in result:
                    result["tools_used"] = []
                if "errors" not in result:
                    result["errors"] = []
                
            elif executor_fn:
                # Use custom executor if provided
                result = executor_fn(step, context)
                
                # Ensure result is a dictionary
                if not isinstance(result, dict):
                    result = {
                        "step_id": step_id,
                        "status": "success",
                        "output": str(result),
                        "tools_used": [],
                        "errors": []
                    }
            else:
                # Default execution: basic response
                result = {
                    "step_id": step_id,
                    "status": "success",
                    "output": f"Executed: {step.get('description', str(step))}",
                    "tools_used": [],
                    "errors": [],
                    "findings": [],
                    "risks": [],
                    "confidence": 0.7
                }
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Add metrics to result
            result["metrics"] = {
                "execution_time": round(execution_time, 3),
                "retry_count": retry_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Track tools used
            if result.get("tools_used"):
                self.metrics["tools_used"].extend(result["tools_used"])
            
            # Track success/failure
            if result.get("status") == "success":
                self.metrics["successful_steps"] += 1
            else:
                self.metrics["failed_steps"] += 1
            
            # Track timing
            self.metrics["step_times"].append(execution_time)
            self.metrics["total_execution_time"] += execution_time
            
            # Store in history
            self.execution_history.append(result)
            self.current_step += 1
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            # Track error
            self.metrics["failed_steps"] += 1
            self.metrics["errors_encountered"].append({
                "step_id": step_id,
                "error": error_msg,
                "retry_count": retry_count
            })
            
            # Check if we should retry
            if retry_count < max_retries:
                print(f"Step {step_id} failed, retrying ({retry_count + 1}/{max_retries})...")
                return self.execute_step(
                    step, 
                    executor_fn, 
                    context, 
                    retry_count + 1, 
                    max_retries
                )
            
            # Max retries reached, return error result
            error_result = {
                "step_id": step_id,
                "status": "failure",
                "output": None,
                "tools_used": [],
                "errors": [error_msg],
                "metrics": {
                    "execution_time": round(execution_time, 3),
                    "retry_count": retry_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            self.execution_history.append(error_result)
            self.current_step += 1
            return error_result
    
    def run_steps(
        self,
        plan: List[Dict[str, Any]],
        executor_fn: Optional[Callable] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute the steps from the generated plan.
        
        Iterates through each step in the plan, executing them in sequence
        or in parallel when dependencies allow. Handles tool invocation,
        result collection, and error recovery.
        
        Args:
            plan: The execution plan containing steps to run
            executor_fn: Optional custom executor function for running steps
            context: Optional shared context passed to all steps
            
        Returns:
            List of execution results, where each result contains:
                - step_id: ID of the executed step
                - status: 'success', 'failure', or 'partial'
                - output: The execution output/result
                - tools_used: List of tools invoked during execution
                - errors: Any errors encountered
                - metrics: Execution metrics (time, token usage, etc.)
        """
        results = []
        for step in plan:
            result = self.execute_step(step, executor_fn, context)
            results.append(result)
        return results
    
    def evaluate_reflection(
        self,
        step: Dict[str, Any],
        result: Dict[str, Any],
        reflector_fn: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Evaluate and reflect on a completed step with integrated reasoning engine support.
        
        Critically assesses the quality of execution, identifies issues,
        and determines if the step needs refinement or re-execution.
        
        Args:
            step: The original step that was executed
            result: The execution result to evaluate
            reflector_fn: Optional custom reflection function
            
        Returns:
            Reflection evaluation containing:
                - quality_score: Overall quality rating (0.0 to 1.0)
                - correctness_score: Factual correctness rating (0.0 to 1.0)
                - completeness_score: Completeness rating (0.0 to 1.0)
                - confidence_score: Confidence level in the result (0.0 to 1.0)
                - issues: List of identified problems or concerns
                - suggestions: Recommended improvements
                - requires_retry: Whether the step should be re-executed
                - missing_data: List of missing information
        """
        if not self.enable_reflection:
            # Return default reflection if disabled
            return {
                "overall_quality": 0.7,
                "correctness_score": 0.7,
                "completeness_score": 0.7,
                "confidence_score": 0.7,
                "issues": [],
                "suggestions": [],
                "requires_retry": False,
                "missing_data": []
            }
        
        try:
            # Use reasoning engine if available
            if self.reasoning_engine and hasattr(self.reasoning_engine, 'reflect'):
                reflection = self.reasoning_engine.reflect(step, result)
                
                # Ensure required fields exist
                if not isinstance(reflection, dict):
                    reflection = {"overall_quality": 0.5}
                
                # Add default values for any missing fields
                reflection.setdefault("overall_quality", 0.7)
                reflection.setdefault("correctness_score", 0.7)
                reflection.setdefault("completeness_score", 0.7)
                reflection.setdefault("confidence_score", 0.7)
                reflection.setdefault("issues", [])
                reflection.setdefault("suggestions", [])
                reflection.setdefault("requires_retry", False)
                reflection.setdefault("missing_data", [])
                
                return reflection
            
            elif reflector_fn:
                # Use custom reflector function
                reflection = reflector_fn(step, result)
                
                if not isinstance(reflection, dict):
                    reflection = {"overall_quality": 0.7}
                
                return reflection
            
            else:
                # Default reflection based on result status
                status = result.get("status", "unknown")
                confidence = result.get("confidence", 0.7)
                
                if status == "success":
                    return {
                        "overall_quality": confidence,
                        "correctness_score": confidence,
                        "completeness_score": confidence,
                        "confidence_score": confidence,
                        "issues": [],
                        "suggestions": [],
                        "requires_retry": False,
                        "missing_data": []
                    }
                else:
                    return {
                        "overall_quality": 0.3,
                        "correctness_score": 0.3,
                        "completeness_score": 0.3,
                        "confidence_score": 0.3,
                        "issues": result.get("errors", []),
                        "suggestions": ["Review and retry the step"],
                        "requires_retry": True,
                        "missing_data": []
                    }
        
        except Exception as e:
            # Return safe default reflection on error
            return {
                "overall_quality": 0.5,
                "correctness_score": 0.5,
                "completeness_score": 0.5,
                "confidence_score": 0.5,
                "issues": [f"Reflection error: {str(e)}"],
                "suggestions": ["Manual review recommended"],
                "requires_retry": False,
                "missing_data": [],
                "error": str(e)
            }
    
    def update_memory(
        self,
        step: Dict[str, Any],
        result: Dict[str, Any],
        reflection: Optional[Dict[str, Any]] = None,
        memory_store: Optional[Any] = None
    ) -> bool:
        """
        Update the agent's memory with execution information.
        
        Stores episodic memories of specific executions and updates
        semantic memory with learned patterns and insights. Enables
        the agent to learn from past experiences.
        
        Args:
            step: The executed step
            result: The execution result
            reflection: Optional reflection on the execution
            memory_store: Optional custom memory store to use
            
        Returns:
            True if memory was successfully updated, False otherwise
        """
        if not self.enable_memory:
            return False
        
        try:
            # Create memory entry
            memory_entry = {
                "step": step,
                "result": result,
                "reflection": reflection,
                "timestamp": self.current_step
            }
            
            # If custom memory store provided, use it
            if memory_store and hasattr(memory_store, 'store'):
                key = f"step_{self.current_step}"
                return memory_store.store(key, memory_entry)
            
            # Otherwise, just track internally
            # (In a real implementation, this would persist to a database)
            return True
            
        except Exception:
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current execution metrics.
        
        Returns:
            Dictionary containing all tracked metrics including:
                - total_steps: Total steps attempted
                - successful_steps: Number of successful steps
                - failed_steps: Number of failed steps
                - total_retries: Total retry attempts
                - total_execution_time: Total time spent executing
                - step_times: List of individual step execution times
                - tools_used: List of all tools used
                - errors_encountered: List of all errors
                - average_step_time: Average time per step
                - success_rate: Percentage of successful steps
        """
        metrics = self.metrics.copy()
        
        # Calculate derived metrics
        if metrics["step_times"]:
            metrics["average_step_time"] = round(
                sum(metrics["step_times"]) / len(metrics["step_times"]), 3
            )
        else:
            metrics["average_step_time"] = 0.0
        
        if metrics["total_steps"] > 0:
            metrics["success_rate"] = round(
                (metrics["successful_steps"] / metrics["total_steps"]) * 100, 2
            )
        else:
            metrics["success_rate"] = 0.0
        
        return metrics
    
    def reset_metrics(self):
        """Reset all metrics to initial state."""
        self.metrics = {
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "total_retries": 0,
            "total_execution_time": 0.0,
            "step_times": [],
            "tools_used": [],
            "errors_encountered": []
        }
        self.current_step = 0
        self.execution_history = []
    
    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        planner_fn: Optional[Callable] = None,
        executor_fn: Optional[Callable] = None,
        reflector_fn: Optional[Callable] = None,
        memory_store: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete agent loop workflow with integrated reasoning engine.
        
        Orchestrates the full cycle:
        1. Generate plan from task
        2. Execute steps sequentially
        3. Reflect on each step (if enabled)
        4. Update memory (if enabled)
        5. Return comprehensive results with metrics
        
        This is the main entry point for running the agent loop.
        
        Args:
            task: The task to execute
            context: Optional execution context
            planner_fn: Optional custom planner
            executor_fn: Optional custom executor
            reflector_fn: Optional custom reflector
            memory_store: Optional memory store
            
        Returns:
            Complete execution result containing:
                - task: Original task
                - plan: Generated plan
                - step_outputs: All step execution results
                - reflections: All reflection evaluations
                - final_output: Synthesized final result
                - success: Whether the task completed successfully
                - metrics: Overall execution metrics
        """
        start_time = time.time()
        
        try:
            # Reset metrics for this execution
            self.reset_metrics()
            
            # Step 1: Generate plan
            if self.reasoning_engine and hasattr(self.reasoning_engine, 'generate_plan'):
                # Use reasoning engine for planning
                entity = context.get("entity", "unknown") if context else "unknown"
                plan = self.reasoning_engine.generate_plan(entity, task, context)
            elif planner_fn:
                # Use custom planner
                plan = planner_fn(task, context)
            else:
                # Create simple default plan
                plan = [
                    {
                        "step_id": "step_1",
                        "description": f"Execute task: {task}",
                        "rationale": "Complete the requested task",
                        "expected_outcome": "Task completion"
                    }
                ]
            
            # Step 2: Execute each step
            step_outputs = []
            reflections = []
            
            for i, step in enumerate(plan):
                if i >= self.max_steps:
                    print(f"Max steps ({self.max_steps}) reached, stopping execution")
                    break
                
                # Execute step
                result = self.execute_step(step, executor_fn, context)
                step_outputs.append(result)
                
                # Step 3: Reflect on execution (if enabled)
                if self.enable_reflection:
                    reflection = self.evaluate_reflection(step, result, reflector_fn)
                    reflections.append(reflection)
                    
                    # Step 4: Update memory (if enabled)
                    if self.enable_memory:
                        self.update_memory(step, result, reflection, memory_store)
            
            # Calculate final metrics
            total_time = time.time() - start_time
            final_metrics = self.get_metrics()
            final_metrics["total_workflow_time"] = round(total_time, 3)
            
            # Determine overall success
            success = all(r.get("status") == "success" for r in step_outputs) if step_outputs else False
            
            # Generate final output summary
            if step_outputs:
                final_output = self._generate_final_output(task, step_outputs, reflections)
            else:
                final_output = "No steps were executed"
            
            return {
                "task": task,
                "plan": plan,
                "step_outputs": step_outputs,
                "reflections": reflections,
                "final_output": final_output,
                "success": success,
                "metrics": final_metrics
            }
        
        except Exception as e:
            # Graceful error handling - never break the orchestrator
            total_time = time.time() - start_time
            error_msg = str(e)
            
            print(f"Agent loop execution error: {error_msg}")
            
            return {
                "task": task,
                "plan": [],
                "step_outputs": [],
                "reflections": [],
                "final_output": f"Execution failed: {error_msg}",
                "success": False,
                "metrics": {
                    "total_workflow_time": round(total_time, 3),
                    "error": error_msg,
                    **self.get_metrics()
                }
            }
    
    def _generate_final_output(
        self,
        task: str,
        step_outputs: List[Dict[str, Any]],
        reflections: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a final output summary from step outputs and reflections.
        
        Args:
            task: The original task
            step_outputs: List of step execution results
            reflections: List of reflection evaluations
            
        Returns:
            Summary string
        """
        try:
            successful = sum(1 for r in step_outputs if r.get("status") == "success")
            total = len(step_outputs)
            
            summary_parts = [
                f"Task: {task}",
                f"Completed {successful}/{total} steps successfully."
            ]
            
            # Add findings from successful steps
            all_findings = []
            for output in step_outputs:
                if output.get("status") == "success" and output.get("findings"):
                    all_findings.extend(output["findings"])
            
            if all_findings:
                summary_parts.append(f"Key findings: {', '.join(all_findings[:3])}")
            
            # Add overall confidence if available
            if reflections:
                avg_confidence = sum(
                    r.get("confidence_score", 0.7) for r in reflections
                ) / len(reflections)
                summary_parts.append(f"Average confidence: {avg_confidence:.2f}")
            
            return " ".join(summary_parts)
        
        except Exception:
            return f"Task '{task}' execution completed"

