"""
Agent Loop Module

Implements the main agent execution loop with plan-execute-reflect cycles.
Includes LLM-based planning, tool execution, reflection with hallucination detection,
and replanning capabilities.
"""

from typing import Dict, List, Any, Optional
import time
from datetime import datetime, timezone

from backend.agentic_engine.reasoning.reasoning_engine import ReasoningEngine
from backend.agentic_engine.tools.tool_registry import ToolRegistry


class AgentLoop:
    """
    Core agent loop handler for iterative reasoning and execution.
    
    Manages the multi-step execution loop that drives the agentic AI workflow.
    Flow:
    1. Plan using LLM → return JSON list of steps
    2. Execute Tools per step
    3. Reflect → LLM scoring + hallucination detection
    4. Replan if score < 0.75
    5. Return Final Output with comprehensive results
    """
    
    def __init__(
        self,
        max_steps: int = 10,
        enable_reflection: bool = True,
        enable_memory: bool = True,
        reasoning_engine: Optional[ReasoningEngine] = None,
        tools: Optional[Dict[str, Any]] = None,
        replan_threshold: float = 0.75
    ):
        """
        Initialize the agent loop.
        
        Args:
            max_steps: Maximum number of execution steps per task
            enable_reflection: Whether to enable reflection after each step
            enable_memory: Whether to enable memory updates during execution
            reasoning_engine: Optional ReasoningEngine instance for enhanced reasoning
            tools: Optional dictionary of available tools
            replan_threshold: Quality score threshold below which to replan (default: 0.75)
        """
        self.max_steps = max_steps
        self.enable_reflection = enable_reflection
        self.enable_memory = enable_memory
        self.replan_threshold = replan_threshold
        
        # Initialize reasoning engine if not provided
        if reasoning_engine is None:
            self.reasoning_engine = ReasoningEngine()
        else:
            self.reasoning_engine = reasoning_engine
        
        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self.tools = tools or {}
        
        # Execution state
        self.current_step = 0
        self.execution_history = []
        self.original_plan = []
        self.revised_plan = []
        self.tool_outputs = []
        self.reflections = []
        
        # Metrics tracking
        self.metrics = {
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "total_retries": 0,
            "replan_count": 0,
            "total_execution_time": 0.0,
            "step_times": [],
            "tools_used": [],
            "errors_encountered": []
        }
    
    def generate_plan(
        self,
        entity: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a strategic execution plan using LLM.
        
        Uses ReasoningEngine to break down the task into discrete, actionable steps.
        Returns a JSON list of steps.
        
        Args:
            entity: Entity name or identifier
            task: The task description to plan for
            context: Optional context information for planning
            
        Returns:
            List of plan steps, where each step contains:
                - step_id: Unique identifier for the step
                - description: What the step should accomplish
                - rationale: Why this step is important
                - expected_outcome: What should result
                - tools: Suggested tools for this step (optional)
        """
        try:
            # Use reasoning engine to generate plan
            plan = self.reasoning_engine.generate_plan(entity, task, context)
            
            # Ensure plan is a list
            if not isinstance(plan, list):
                plan = [plan] if plan else []
            
            # Validate and normalize plan structure
            validated_plan = []
            for i, step in enumerate(plan):
                if isinstance(step, dict):
                    validated_step = {
                        "step_id": step.get("step_id", f"step_{i + 1}"),
                        "description": step.get("description", f"Step {i + 1}"),
                        "rationale": step.get("rationale", "Required for task completion"),
                        "expected_outcome": step.get("expected_outcome", "Progress toward goal")
                    }
                    # Include optional fields
                    if "tools" in step:
                        validated_step["tools"] = step["tools"]
                    validated_plan.append(validated_step)
            
            return validated_plan
            
        except Exception as e:
            print(f"Error generating plan: {e}")
            # Return default plan on error
            return [
                {
                    "step_id": "step_1",
                    "description": f"Analyze task: {task}",
                    "rationale": "Initial analysis required",
                    "expected_outcome": "Understanding of task requirements"
                }
            ]
    
    def execute_tools(
        self,
        step: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute tools for a given step.
        
        Uses ToolRegistry to identify relevant tools and executes them.
        
        Args:
            step: The step to execute tools for
            context: Optional execution context
            
        Returns:
            List of tool execution results
        """
        tool_outputs = []
        step_description = step.get("description", "")
        
        # Identify tools needed for this step
        tool_names = self.tool_registry.match_tools_to_step(step_description, context)
        
        # Also check if step explicitly mentions tools
        if "tools" in step:
            explicit_tools = step.get("tools", [])
            if isinstance(explicit_tools, list):
                tool_names.extend(explicit_tools)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tools = []
        for tool in tool_names:
            if tool not in seen:
                seen.add(tool)
                unique_tools.append(tool)
        
        # Execute each tool
        for tool_name in unique_tools:
            if tool_name in self.tools:
                try:
                    tool = self.tools[tool_name]
                    
                    # Extract tool parameters from step and context
                    tool_params = self._extract_tool_params(step, context, tool_name)
                    
                    # Execute tool (try common method names)
                    tool_result = None
                    if hasattr(tool, "execute"):
                        tool_result = tool.execute(**tool_params)
                    elif hasattr(tool, "run"):
                        tool_result = tool.run(**tool_params)
                    else:
                        # Try to call tool directly with params
                        tool_result = {"success": False, "error": "Tool has no execute method"}
                    
                    tool_outputs.append({
                        "tool_name": tool_name,
                        "step_id": step.get("step_id"),
                        "params": tool_params,
                        "result": tool_result,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                    # Track tool usage
                    self.metrics["tools_used"].append(tool_name)
                    
                except Exception as e:
                    tool_outputs.append({
                        "tool_name": tool_name,
                        "step_id": step.get("step_id"),
                        "result": {"success": False, "error": str(e)},
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    self.metrics["errors_encountered"].append({
                        "step_id": step.get("step_id"),
                        "tool": tool_name,
                        "error": str(e)
                    })
        
        return tool_outputs
    
    def _extract_tool_params(
        self,
        step: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        tool_name: str
    ) -> Dict[str, Any]:
        """Extract tool parameters from step and context."""
        params = {}
        
        # Extract from context
        if context:
            if tool_name == "entity_tool" and "entity" in context:
                entity = context["entity"]
                if isinstance(entity, dict):
                    params.update({
                        "entity_name": entity.get("name", ""),
                        "entity_type": entity.get("type", "PRIVATE_COMPANY"),
                        "industry": entity.get("industry", "TECHNOLOGY"),
                    })
            
            if tool_name == "task_tool" and "task" in context:
                task = context["task"]
                if isinstance(task, dict):
                    params.update({
                        "task_description": task.get("description", step.get("description", "")),
                        "task_category": task.get("category"),
                    })
            
            if tool_name == "calendar_tool" and "task" in context:
                task = context["task"]
                if isinstance(task, dict):
                    if "deadline" in task:
                        params["deadline"] = task["deadline"]
        
        # Extract from step description if params still missing
        if not params and tool_name == "task_tool":
            params["task_description"] = step.get("description", "")
        
        return params
    
    def execute_step(
        self,
        step: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single step from the plan.
        
        Args:
            step: The step to execute
            context: Optional execution context
            
        Returns:
            Execution result containing output, tool results, and metadata
        """
        start_time = time.time()
        step_id = step.get("step_id", f"step_{self.current_step}")
        
        try:
            self.metrics["total_steps"] += 1
            
            # Execute tools for this step
            tool_outputs = self.execute_tools(step, context)
            
            # Use reasoning engine to execute the step
            if self.reasoning_engine:
                execution_result = self.reasoning_engine.run_step(step, context)
                
                # Ensure result has required fields
                if not isinstance(execution_result, dict):
                    execution_result = {"output": str(execution_result), "status": "success"}
                
                # Add tool outputs to result
                execution_result["tools_used"] = [t["tool_name"] for t in tool_outputs]
                execution_result["tool_outputs"] = tool_outputs
                
            else:
                # Default execution
                execution_result = {
                    "step_id": step_id,
                    "status": "success",
                    "output": f"Executed: {step.get('description', str(step))}",
                    "tools_used": [t["tool_name"] for t in tool_outputs],
                    "tool_outputs": tool_outputs,
                    "findings": [],
                    "risks": [],
                    "confidence": 0.7
                }
            
            # Ensure required fields
            execution_result.setdefault("step_id", step_id)
            execution_result.setdefault("status", "success")
            execution_result.setdefault("findings", [])
            execution_result.setdefault("risks", [])
            execution_result.setdefault("confidence", 0.7)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            execution_result["metrics"] = {
                "execution_time": round(execution_time, 3),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Track success/failure
            if execution_result.get("status") == "success":
                self.metrics["successful_steps"] += 1
            else:
                self.metrics["failed_steps"] += 1
            
            # Track timing
            self.metrics["step_times"].append(execution_time)
            self.metrics["total_execution_time"] += execution_time
            
            # Store in history
            self.execution_history.append(execution_result)
            self.current_step += 1
            
            return execution_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            self.metrics["failed_steps"] += 1
            self.metrics["errors_encountered"].append({
                "step_id": step_id,
                "error": error_msg
            })
            
            return {
                "step_id": step_id,
                "status": "failure",
                "output": None,
                "tools_used": [],
                "tool_outputs": [],
                "errors": [error_msg],
                "metrics": {
                    "execution_time": round(execution_time, 3),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
    
    def reflect_on_step(
        self,
        step: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Reflect on a completed step with LLM scoring and hallucination detection.
        
        Args:
            step: The original step that was executed
            result: The execution result to evaluate
            
        Returns:
            Reflection evaluation containing:
                - overall_quality: Overall quality rating (0.0 to 1.0)
                - correctness_score: Factual correctness rating (0.0 to 1.0)
                - completeness_score: Completeness rating (0.0 to 1.0)
                - confidence_score: Confidence level (0.0 to 1.0)
                - hallucination_detected: Boolean indicating if hallucination was detected
                - hallucination_indicators: List of indicators that suggest hallucination
                - issues: List of identified problems
                - suggestions: Recommended improvements
                - requires_retry: Whether the step should be re-executed
        """
        if not self.enable_reflection:
            return {
                "overall_quality": 0.7,
                "correctness_score": 0.7,
                "completeness_score": 0.7,
                "confidence_score": 0.7,
                "hallucination_detected": False,
                "hallucination_indicators": [],
                "issues": [],
                "suggestions": [],
                "requires_retry": False
            }
        
        try:
            # Use reasoning engine for reflection
            if self.reasoning_engine:
                reflection = self.reasoning_engine.reflect(step, result)
                
                # Ensure required fields
                if not isinstance(reflection, dict):
                    reflection = {"overall_quality": 0.5}
                
                # Add hallucination detection
                reflection = self._detect_hallucination(reflection, result)
                
                # Set defaults
                reflection.setdefault("overall_quality", reflection.get("correctness_score", 0.7))
                reflection.setdefault("correctness_score", 0.7)
                reflection.setdefault("completeness_score", 0.7)
                reflection.setdefault("confidence_score", 0.7)
                reflection.setdefault("hallucination_detected", False)
                reflection.setdefault("hallucination_indicators", [])
                reflection.setdefault("issues", [])
                reflection.setdefault("suggestions", [])
                reflection.setdefault("requires_retry", False)
                
                return reflection
            else:
                # Default reflection
                return {
                    "overall_quality": 0.7,
                    "correctness_score": 0.7,
                    "completeness_score": 0.7,
                    "confidence_score": 0.7,
                    "hallucination_detected": False,
                    "hallucination_indicators": [],
                    "issues": [],
                    "suggestions": [],
                    "requires_retry": False
                }
        
        except Exception as e:
            return {
                "overall_quality": 0.5,
                "correctness_score": 0.5,
                "completeness_score": 0.5,
                "confidence_score": 0.5,
                "hallucination_detected": False,
                "hallucination_indicators": [f"Reflection error: {str(e)}"],
                "issues": [f"Reflection error: {str(e)}"],
                "suggestions": ["Manual review recommended"],
                "requires_retry": False
            }
    
    def _detect_hallucination(
        self,
        reflection: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect potential hallucinations in the execution result.
        
        Args:
            reflection: Reflection data
            result: Execution result
            
        Returns:
            Reflection with hallucination detection added
        """
        indicators = []
        hallucination_detected = False
        
        # Check for common hallucination indicators
        output = result.get("output", "")
        findings = result.get("findings", [])
        
        # Indicator 1: Overly confident claims without evidence
        if isinstance(output, str):
            if any(phrase in output.lower() for phrase in ["definitely", "absolutely", "certainly"]) and not findings:
                indicators.append("High confidence claims without supporting evidence")
        
        # Indicator 2: Specific numbers or facts without tool outputs
        if not result.get("tool_outputs") and any(char.isdigit() for char in str(output)):
            indicators.append("Specific facts/numbers without tool verification")
        
        # Indicator 3: Low correctness score but high confidence
        correctness = reflection.get("correctness_score", 0.7)
        confidence = reflection.get("confidence_score", 0.7)
        if correctness < 0.6 and confidence > 0.8:
            indicators.append("Low correctness but high confidence (potential hallucination)")
        
        # Indicator 4: Missing data issues
        missing_data = reflection.get("missing_data", [])
        if missing_data and confidence > 0.7:
            indicators.append("High confidence despite missing data")
        
        # Determine if hallucination detected
        if len(indicators) >= 2 or (indicators and correctness < 0.5):
            hallucination_detected = True
        
        reflection["hallucination_detected"] = hallucination_detected
        reflection["hallucination_indicators"] = indicators
        
        return reflection
    
    def execute(
        self,
        entity: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete agent loop workflow.
        
        Flow:
        1. Plan using LLM → return JSON list of steps
        2. Execute Tools per step
        3. Reflect → LLM scoring + hallucination detection
        4. Replan if score < 0.75
        5. Return Final Output
        
        Args:
            entity: Entity name or identifier
            task: The task to execute
            context: Optional execution context
            
        Returns:
            Complete execution result containing:
                - plan: Original plan
                - revised_plan: Revised plan (if replanning occurred)
                - tool_outputs: All tool execution results
                - reflections: All reflection evaluations
                - risk_assessment: Overall risk assessment
                - recommendation: Final recommendation
                - audit_log: Audit log-ready JSON
                - metrics: Execution metrics
        """
        start_time = time.time()
        
        try:
            # Reset state
            self.current_step = 0
            self.execution_history = []
            self.original_plan = []
            self.revised_plan = []
            self.tool_outputs = []
            self.reflections = []
            self.reset_metrics()
            
            # Step 1: Generate initial plan using LLM
            plan = self.generate_plan(entity, task, context)
            self.original_plan = plan.copy()
            current_plan = plan.copy()
            
            # Step 2: Execute steps and reflect
            step_outputs = []
            max_replan_attempts = 2
            replan_count = 0
            
            while len(step_outputs) < self.max_steps and replan_count <= max_replan_attempts:
                # Execute remaining steps
                for step in current_plan[len(step_outputs):]:
                    if len(step_outputs) >= self.max_steps:
                        break
                    
                    # Execute step
                    result = self.execute_step(step, context)
                    step_outputs.append(result)
                    
                    # Collect tool outputs
                    if result.get("tool_outputs"):
                        self.tool_outputs.extend(result["tool_outputs"])
                    
                    # Reflect on step
                    if self.enable_reflection:
                        reflection = self.reflect_on_step(step, result)
                        self.reflections.append(reflection)
                        
                        # Check if replanning is needed
                        quality_score = reflection.get("overall_quality", 0.7)
                        
                        if quality_score < self.replan_threshold and replan_count < max_replan_attempts:
                            # Replan
                            replan_count += 1
                            self.metrics["replan_count"] += 1
                            
                            # Generate revised plan
                            revised_plan = self.generate_plan(
                                entity,
                                task,
                                {**(context or {}), "previous_attempts": step_outputs, "reflections": self.reflections}
                            )
                            self.revised_plan = revised_plan.copy()
                            current_plan = revised_plan.copy()
                            
                            # Reset step outputs to start fresh with new plan
                            step_outputs = []
                            self.reflections = []
                            break  # Break to restart with new plan
            
            # Step 3: Generate final outputs
            risk_assessment = self._generate_risk_assessment(step_outputs, self.reflections)
            recommendation = self._generate_recommendation(step_outputs, self.reflections, risk_assessment)
            audit_log = self._generate_audit_log(entity, task, context, step_outputs, self.reflections, risk_assessment, recommendation)
            
            # Calculate final metrics
            total_time = time.time() - start_time
            final_metrics = self.get_metrics()
            final_metrics["total_workflow_time"] = round(total_time, 3)
            final_metrics["replan_count"] = replan_count
            
            # Determine overall success
            success = all(r.get("status") == "success" for r in step_outputs) if step_outputs else False
            
            return {
                "plan": self.original_plan,
                "revised_plan": self.revised_plan if self.revised_plan else None,
                "tool_outputs": self.tool_outputs,
                "reflections": self.reflections,
                "risk_assessment": risk_assessment,
                "recommendation": recommendation,
                "audit_log": audit_log,
                "step_outputs": step_outputs,
                "success": success,
                "metrics": final_metrics
            }
        
        except Exception as e:
            total_time = time.time() - start_time
            error_msg = str(e)
            
            return {
                "plan": self.original_plan,
                "revised_plan": self.revised_plan if self.revised_plan else None,
                "tool_outputs": self.tool_outputs,
                "reflections": self.reflections,
                "risk_assessment": {"level": "UNKNOWN", "score": 0.0, "factors": []},
                "recommendation": f"Execution failed: {error_msg}",
                "audit_log": {
                    "status": "error",
                    "error": error_msg,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "step_outputs": self.execution_history,
                "success": False,
                "metrics": {
                    "total_workflow_time": round(total_time, 3),
                    "error": error_msg,
                    **self.get_metrics()
                }
            }
    
    def _generate_risk_assessment(
        self,
        step_outputs: List[Dict[str, Any]],
        reflections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate overall risk assessment from step outputs and reflections."""
        risk_factors = []
        risk_scores = []
        
        # Collect risk information from step outputs
        for output in step_outputs:
            if output.get("risks"):
                risk_factors.extend(output["risks"])
            if output.get("risk_score"):
                risk_scores.append(output["risk_score"])
        
        # Collect risk from reflections
        for reflection in reflections:
            if reflection.get("issues"):
                risk_factors.extend(reflection["issues"])
            if reflection.get("hallucination_detected"):
                risk_factors.append("Potential hallucination detected")
        
        # Calculate overall risk score
        if risk_scores:
            avg_risk_score = sum(risk_scores) / len(risk_scores)
        else:
            # Infer from reflections
            if reflections:
                quality_scores = [r.get("overall_quality", 0.7) for r in reflections]
                avg_quality = sum(quality_scores) / len(quality_scores)
                avg_risk_score = 1.0 - avg_quality  # Inverse of quality
            else:
                avg_risk_score = 0.5
        
        # Determine risk level
        if avg_risk_score >= 0.7:
            risk_level = "HIGH"
        elif avg_risk_score >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "level": risk_level,
            "score": round(avg_risk_score, 3),
            "factors": list(set(risk_factors)),  # Remove duplicates
            "step_count": len(step_outputs),
            "reflection_count": len(reflections)
        }
    
    def _generate_recommendation(
        self,
        step_outputs: List[Dict[str, Any]],
        reflections: List[Dict[str, Any]],
        risk_assessment: Dict[str, Any]
    ) -> str:
        """Generate final recommendation based on execution results."""
        if not step_outputs:
            return "No steps were executed. Unable to provide recommendation."
        
        # Check for failures
        failures = [s for s in step_outputs if s.get("status") != "success"]
        if failures:
            return f"Execution encountered {len(failures)} failure(s). Review required before proceeding."
        
        # Check risk level
        risk_level = risk_assessment.get("level", "UNKNOWN")
        if risk_level == "HIGH":
            return "High risk detected. Manual review and expert consultation recommended before proceeding."
        elif risk_level == "MEDIUM":
            return "Medium risk detected. Proceed with caution and consider additional validation."
        else:
            # Check for hallucinations
            hallucinations = [r for r in reflections if r.get("hallucination_detected")]
            if hallucinations:
                return "Low risk but potential hallucinations detected. Verify key facts before proceeding."
            else:
                return "Low risk. Proceed with confidence. All steps completed successfully."
    
    def _generate_audit_log(
        self,
        entity: str,
        task: str,
        context: Optional[Dict[str, Any]],
        step_outputs: List[Dict[str, Any]],
        reflections: List[Dict[str, Any]],
        risk_assessment: Dict[str, Any],
        recommendation: str
    ) -> Dict[str, Any]:
        """Generate audit log-ready JSON."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entity": entity,
            "task": task,
            "context": context or {},
            "plan": {
                "original": self.original_plan,
                "revised": self.revised_plan if self.revised_plan else None
            },
            "execution": {
                "step_count": len(step_outputs),
                "steps": [
                    {
                        "step_id": s.get("step_id"),
                        "status": s.get("status"),
                        "output": s.get("output"),
                        "tools_used": s.get("tools_used", []),
                        "confidence": s.get("confidence", 0.0)
                    }
                    for s in step_outputs
                ]
            },
            "reflections": [
                {
                    "overall_quality": r.get("overall_quality", 0.0),
                    "correctness_score": r.get("correctness_score", 0.0),
                    "completeness_score": r.get("completeness_score", 0.0),
                    "hallucination_detected": r.get("hallucination_detected", False),
                    "issues": r.get("issues", [])
                }
                for r in reflections
            ],
            "risk_assessment": risk_assessment,
            "recommendation": recommendation,
            "metrics": self.get_metrics()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current execution metrics."""
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
            "replan_count": 0,
            "total_execution_time": 0.0,
            "step_times": [],
            "tools_used": [],
            "errors_encountered": []
        }
