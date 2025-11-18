"""
Orchestrator Module

Coordinates the overall agentic workflow, managing the interaction between
reasoning, tools, memory, and scoring components.
"""

from typing import Dict, List, Any, Optional
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from backend.agentic_engine.openai_helper import call_openai_sync, STANDARD_MODEL
from backend.agentic_engine.agent_loop import AgentLoop
from backend.agentic_engine.memory.memory_store import MemoryStore
from backend.agentic_engine.tools.entity_tool import EntityTool
from backend.agentic_engine.tools.calendar_tool import CalendarTool
from backend.agentic_engine.tools.http_tool import HTTPTool
from backend.agentic_engine.tools.task_tool import TaskTool
from backend.agentic_engine.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class AgenticAIOrchestrator:
    """
    Main orchestrator for the agentic AI engine.
    
    Coordinates the plan-execute-reflect cycle for compliance task analysis,
    managing reasoning engines, tools, memory systems, and scoring components.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, db_session: Optional[Any] = None):
        """
        Initialize the agentic AI orchestrator.
        
        Args:
            config: Optional configuration dictionary for the orchestrator
            db_session: Optional database session for tools that need database access
        """
        self.config = config or {}
        
        # Initialize OpenAI configuration using existing environment variables
        # Support mock mode when API key is not set
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", STANDARD_MODEL)
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))
        self.mock_mode = not self.api_key or self.api_key == "mock" or (isinstance(self.api_key, str) and self.api_key.startswith("sk-mock"))
        
        if self.mock_mode:
            logger.warning("Running in mock mode - OpenAI API key not set. Agentic features will use simulated responses.")
        
        # Initialize components
        self.agent_loop = AgentLoop(
            max_steps=self.config.get("max_steps", 10),
            enable_reflection=True,
            enable_memory=True
        )
        self.memory_store = MemoryStore()
        
        # Initialize tools
        self.tools = {
            "entity_tool": EntityTool(db_session=db_session),
            "calendar_tool": CalendarTool(),
            "http_tool": HTTPTool(),
            "task_tool": TaskTool()
        }
        
        # Initialize ToolRegistry for intelligent tool selection
        self.tool_registry = ToolRegistry()
        
        # Load prompts
        self.prompts = self._load_prompts()
        
        # Track execution state
        self.execution_state = {
            "plan": [],
            "step_outputs": [],
            "reflections": [],
            "final_recommendation": "",
            "confidence_score": 0.0
        }
        
        # Track tool usage metrics
        self.tool_metrics = {
            "tools_called": [],
            "tool_call_count": {},
            "tool_success_count": {},
            "tool_error_count": {},
            "total_tool_calls": 0
        }
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load prompts from the prompts directory."""
        prompts = {}
        prompts_dir = Path(__file__).parent / "reasoning" / "prompts"
        
        try:
            # Load planner prompt
            planner_path = prompts_dir / "planner_prompt.txt"
            if planner_path.exists():
                with open(planner_path, 'r') as f:
                    prompts['planner'] = f.read()
            
            # Load executor prompt
            executor_path = prompts_dir / "executor_prompt.txt"
            if executor_path.exists():
                with open(executor_path, 'r') as f:
                    prompts['executor'] = f.read()
            
            # Load reflection prompt
            reflection_path = prompts_dir / "reflection_prompt.txt"
            if reflection_path.exists():
                with open(reflection_path, 'r') as f:
                    prompts['reflection'] = f.read()
        except Exception as e:
            print(f"Warning: Could not load prompts: {e}")
        
        return prompts
    
    def _identify_required_tools(self, step: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Identify which tools this step might need using ToolRegistry for intelligent matching.
        
        Args:
            step: The step to analyze
            context: Optional context information
            
        Returns:
            List of tool names that might be useful for this step
        """
        step_description = step.get("description", "")
        
        # Use ToolRegistry for intelligent tool matching
        matched_tools = self.tool_registry.match_tools_to_step(step_description, context)
        
        # Also check if step explicitly mentions tools
        if "tools" in step:
            step_tools = step.get("tools", [])
            if isinstance(step_tools, list):
                matched_tools.extend(step_tools)
        
        # Remove duplicates and return, preserving order (most relevant first)
        seen = set()
        result = []
        for tool in matched_tools:
            if tool not in seen:
                seen.add(tool)
                result.append(tool)
        
        return result
    
    def _execute_tools(
        self, 
        tool_names: List[str], 
        step: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute tools and gather results with safety checks.
        
        Args:
            tool_names: List of tool names to execute
            step: The step being executed
            context: Optional context from the overall plan
            
        Returns:
            Dictionary containing tool_results and tools_used
        """
        tool_results = {}
        tools_used = []
        tool_errors = []
        
        for tool_name in tool_names:
            tool = self.tools.get(tool_name)
            if not tool:
                tool_errors.append(f"Tool {tool_name} not found")
                continue
            
            # Safety check: Verify tool is read-only if required
            if self.tool_registry.is_read_only(tool_name):
                # Additional safety: Check if tool requires HTTP and if it's allowed
                if self.tool_registry.requires_http(tool_name):
                    # For HTTP tools, validate URL safety
                    step_desc = step.get("description", "")
                    if "http://" in step_desc or "https://" in step_desc:
                        # Extract and validate URL
                        import re
                        urls = re.findall(r'https?://[^\s]+', step_desc)
                        if not urls:
                            tool_errors.append(f"HTTP tool {tool_name} requires valid URL in step description")
                            continue
            
            try:
                # Extract relevant context for each tool
                entity_data = context.get("entity", {}) if context else {}
                task_data = context.get("task", {}) if context else {}
                
                if tool_name == "entity_tool" and entity_data:
                    # Track tool call
                    self.tool_metrics["total_tool_calls"] += 1
                    self.tool_metrics["tools_called"].append(tool_name)
                    self.tool_metrics["tool_call_count"][tool_name] = self.tool_metrics["tool_call_count"].get(tool_name, 0) + 1
                    
                    result = tool.fetch_entity_details(
                        entity_name=entity_data.get("entity_name", ""),
                        entity_type=entity_data.get("entity_type", "PRIVATE_COMPANY"),
                        industry=entity_data.get("industry", "TECHNOLOGY"),
                        employee_count=entity_data.get("employee_count"),
                        annual_revenue=entity_data.get("annual_revenue"),
                        has_personal_data=entity_data.get("has_personal_data", False),
                        is_regulated=entity_data.get("is_regulated", False),
                        previous_violations=entity_data.get("previous_violations", 0),
                        jurisdictions=entity_data.get("locations", [])
                    )
                    tool_results["entity"] = result
                    tools_used.append(tool_name)
                    self.tool_metrics["tool_success_count"][tool_name] = self.tool_metrics["tool_success_count"].get(tool_name, 0) + 1
                
                elif tool_name == "calendar_tool" and task_data.get("deadline"):
                    # Track tool call
                    self.tool_metrics["total_tool_calls"] += 1
                    self.tool_metrics["tools_called"].append(tool_name)
                    self.tool_metrics["tool_call_count"][tool_name] = self.tool_metrics["tool_call_count"].get(tool_name, 0) + 1
                    
                    result = tool.calculate_deadline(deadline_text=task_data["deadline"])
                    tool_results["calendar"] = result
                    tools_used.append(tool_name)
                    self.tool_metrics["tool_success_count"][tool_name] = self.tool_metrics["tool_success_count"].get(tool_name, 0) + 1
                
                elif tool_name == "task_tool" and task_data:
                    # Track tool call
                    self.tool_metrics["total_tool_calls"] += 1
                    self.tool_metrics["tools_called"].append(tool_name)
                    self.tool_metrics["tool_call_count"][tool_name] = self.tool_metrics["tool_call_count"].get(tool_name, 0) + 1
                    
                    result = tool.run_task_risk_analyzer(
                        task_description=task_data.get("task_description", ""),
                        task_category=task_data.get("task_category", "DATA_PROTECTION"),
                        affects_personal_data=entity_data.get("has_personal_data", False) if entity_data else False,
                        deadline=task_data.get("deadline"),
                        requires_filing=task_data.get("requires_filing", False)
                    )
                    tool_results["task"] = result
                    tools_used.append(tool_name)
                    self.tool_metrics["tool_success_count"][tool_name] = self.tool_metrics["tool_success_count"].get(tool_name, 0) + 1
                
                elif tool_name == "http_tool":
                    # HTTP tool requires explicit URL, skip for now unless URL is in step description
                    # Could be enhanced to extract URLs from step description
                    step_desc = step.get("description", "")
                    if "http://" in step_desc or "https://" in step_desc:
                        # Extract URL (simplified - would need better parsing in production)
                        import re
                        urls = re.findall(r'https?://[^\s]+', step_desc)
                        if urls:
                            # Track tool call
                            self.tool_metrics["total_tool_calls"] += 1
                            self.tool_metrics["tools_called"].append(tool_name)
                            self.tool_metrics["tool_call_count"][tool_name] = self.tool_metrics["tool_call_count"].get(tool_name, 0) + 1
                            
                            # Use sync version for now (orchestrator is not async)
                            result = tool.get_sync(urls[0])
                            tool_results["http"] = result
                            tools_used.append(tool_name)
                            self.tool_metrics["tool_success_count"][tool_name] = self.tool_metrics["tool_success_count"].get(tool_name, 0) + 1
            
            except Exception as e:
                error_msg = f"Tool {tool_name} failed: {e}"
                print(f"Warning: {error_msg}")
                tool_errors.append(error_msg)
                tool_results[f"{tool_name}_error"] = str(e)
                # Track tool error
                if tool_name in self.tool_metrics["tool_call_count"]:
                    self.tool_metrics["tool_error_count"][tool_name] = self.tool_metrics["tool_error_count"].get(tool_name, 0) + 1
        
        return {
            "tool_results": tool_results,
            "tools_used": tools_used,
            "tool_errors": tool_errors,
            "safety_checks_passed": len(tool_errors) == 0
        }
    
    def _summarize_previous_steps(self, step_outputs: List[Dict]) -> str:
        """
        Summarize previous steps for context to avoid prompt bloat.
        
        Args:
            step_outputs: List of previous step execution results
            
        Returns:
            Summarized string of previous steps
        """
        if not step_outputs:
            return "No previous steps completed."
        
        summary = "Previous steps completed:\n"
        # Only include last 3 steps to avoid prompt bloat
        for i, output in enumerate(step_outputs[-3:], 1):
            step_id = output.get('step_id', f'step_{i}')
            output_text = output.get('output', '')
            if isinstance(output_text, dict):
                output_text = json.dumps(output_text, indent=2)
            elif not isinstance(output_text, str):
                output_text = str(output_text)
            
            # Truncate to 200 chars
            output_preview = output_text[:200] + "..." if len(output_text) > 200 else output_text
            summary += f"\n{i}. {step_id}: {output_preview}\n"
            
            # Add key findings if available
            if output.get('findings'):
                findings = output['findings'][:2]  # Only first 2 findings
                summary += f"   Key findings: {', '.join(findings)}\n"
        
        return summary
    
    def plan(self, task: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Generate a strategic plan for the given compliance task.
        
        Breaks down the task into 3-7 actionable steps that follow the path
        an expert compliance analyst would take.
        
        Args:
            task: The compliance task description
            context: Optional additional context for planning
            
        Returns:
            List of plan steps, each containing step description, rationale,
            required tools, and expected outcomes
        """
        # Build planning prompt
        planner_prompt = self.prompts.get('planner', 
            'You are an AI planner. Break the compliance task into 3-7 steps.')
        
        context_str = ""
        if context:
            context_str = f"\n\nAdditional Context:\n{json.dumps(context, indent=2)}"
        
        full_prompt = f"""{planner_prompt}

Task: {task}{context_str}

Please provide a plan as a JSON array with 3-7 steps. Each step should have:
- step_id: a unique identifier (e.g., "step_1")
- description: what needs to be done
- rationale: why this step is important
- expected_outcome: what should result from this step

Respond ONLY with valid JSON array format."""
        
        try:
            # Use standardized OpenAI helper (main task - 120s timeout)
            openai_response = call_openai_sync(
                prompt=full_prompt,
                is_main_task=True,  # Planning is a main task
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Handle mock mode or extract response
            if self.mock_mode or openai_response["status"] != "completed":
                if openai_response["status"] == "error":
                    logger.error(f"OpenAI planning failed: {openai_response.get('error')}")
                # Fallback to default plan (will be handled by exception handler below)
                raise json.JSONDecodeError("Planning failed", "", 0)
            
            # Extract response content
            result_content = openai_response.get("result", {})
            if isinstance(result_content, dict):
                response_text = result_content.get("content", str(result_content))
            else:
                response_text = str(result_content)
            
            # Try to parse JSON from response
            # Handle markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            plan = json.loads(response_text)
            
            # Ensure plan has 3-7 steps
            if not isinstance(plan, list):
                plan = [plan]
            
            # Limit to 7 steps, ensure at least 3
            if len(plan) > 7:
                plan = plan[:7]
            elif len(plan) < 3:
                # If too few steps, add generic ones
                while len(plan) < 3:
                    plan.append({
                        "step_id": f"step_{len(plan) + 1}",
                        "description": f"Additional analysis step {len(plan) + 1}",
                        "rationale": "Ensure comprehensive coverage",
                        "expected_outcome": "Additional insights"
                    })
            
            # Ensure each step has required fields
            for i, step in enumerate(plan):
                if "step_id" not in step:
                    step["step_id"] = f"step_{i + 1}"
                if "description" not in step:
                    step["description"] = f"Step {i + 1}"
                if "rationale" not in step:
                    step["rationale"] = "Required for task completion"
                if "expected_outcome" not in step:
                    step["expected_outcome"] = "Progress toward task goal"
            
            return plan
            
        except json.JSONDecodeError:
            # Fallback: create a simple plan
            return [
                {
                    "step_id": "step_1",
                    "description": "Analyze the compliance task requirements",
                    "rationale": "Understand what needs to be evaluated",
                    "expected_outcome": "Clear understanding of requirements"
                },
                {
                    "step_id": "step_2",
                    "description": "Gather relevant compliance data and context",
                    "rationale": "Collect necessary information for analysis",
                    "expected_outcome": "Complete dataset for evaluation"
                },
                {
                    "step_id": "step_3",
                    "description": f"Execute compliance analysis: {task}",
                    "rationale": "Perform the core compliance evaluation",
                    "expected_outcome": "Detailed compliance assessment"
                },
                {
                    "step_id": "step_4",
                    "description": "Generate recommendations and final report",
                    "rationale": "Provide actionable guidance",
                    "expected_outcome": "Complete compliance recommendation"
                }
            ]
        except Exception as e:
            # Fallback on any error
            print(f"Error in planning: {e}")
            return [
                {
                    "step_id": "step_1",
                    "description": f"Analyze task: {task}",
                    "rationale": "Complete the requested task",
                    "expected_outcome": "Task completion"
                }
            ]
    
    def execute_step(
        self, 
        step: Dict[str, Any], 
        plan_context: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Execute a single step from the plan.
        
        Uses available tools to gather facts, analyze risks, and fill in
        missing context. Performs the specific action or analysis required
        by the step.
        
        Args:
            step: The step to execute, containing description and parameters
            plan_context: Optional context from the overall plan
            retry_count: Current retry attempt number
            max_retries: Maximum number of retries allowed
            
        Returns:
            Execution result containing step output, gathered data,
            tool usage logs, and any generated insights
        """
        # Identify and execute tools
        tool_names = self._identify_required_tools(step, plan_context)
        tool_execution_result = self._execute_tools(tool_names, step, plan_context)
        tools_used = tool_execution_result.get("tools_used", [])
        tool_results = tool_execution_result.get("tool_results", {})
        
        # Build executor prompt
        executor_prompt = self.prompts.get('executor',
            'You are an AI executor. Perform the step given.')
        
        context_str = ""
        if plan_context:
            context_str = f"\n\nPlan Context:\n{json.dumps(plan_context, indent=2)}"
        
        # Build tool context string
        tool_context_str = ""
        if tool_results:
            tool_context_str = f"\n\nAvailable Tool Results:\n{json.dumps(tool_results, indent=2)}"
        
        step_description = step.get('description', str(step))
        step_rationale = step.get('rationale', '')
        
        # Add retry context if this is a retry
        retry_note = ""
        if retry_count > 0:
            previous_error = step.get("previous_error", "Unknown error")
            retry_note = f"\n\nNOTE: Previous attempt failed with error: {previous_error}. Please try again with more detail and error handling."
        
        full_prompt = f"""{executor_prompt}

Step to Execute:
{step_description}{retry_note}

Rationale:
{step_rationale}{context_str}{tool_context_str}

Previous Steps Completed:
{self._summarize_previous_steps(self.execution_state['step_outputs'])}

Please execute this step and provide:
1. The main output/result
2. Any key findings or insights
3. Any risks or concerns identified
4. Confidence in the execution (0.0 to 1.0)

Respond in JSON format with keys: output, findings, risks, confidence"""
        
        try:
            # Use standardized OpenAI helper (main task - 120s timeout)
            openai_response = call_openai_sync(
                prompt=full_prompt,
                is_main_task=True,  # Step execution is a main task
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Handle mock mode or extract response
            if self.mock_mode or openai_response["status"] != "completed":
                if openai_response["status"] == "error":
                    logger.error(f"OpenAI step execution failed: {openai_response.get('error')}")
                # Fallback execution data
                execution_data = {
                    "output": f"Step execution failed: {openai_response.get('error', 'Unknown error')}",
                    "findings": [],
                    "risks": [],
                    "confidence": 0.5
                }
            else:
                # Extract response content
                result_content = openai_response.get("result", {})
                if isinstance(result_content, dict):
                    response_text = result_content.get("content", str(result_content))
                else:
                    response_text = str(result_content)
                
                # Try to parse JSON from response
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                try:
                    execution_data = json.loads(response_text)
                except json.JSONDecodeError:
                    # If JSON parsing fails, use the text as output
                    execution_data = {
                        "output": response_text,
                        "findings": [],
                        "risks": [],
                        "confidence": 0.7
                    }
            
            # Use agent_loop.execute_step with custom executor function
            def executor_fn(step_data, context):
                # Ensure consistent structure
                output_text = execution_data.get("output", "Step executed")
                if isinstance(output_text, dict):
                    output_text = json.dumps(output_text, indent=2)
                elif not isinstance(output_text, str):
                    output_text = str(output_text)
                
                return {
                    "step_id": step_data.get("step_id"),
                    "status": "success",
                    "output": output_text,  # Always string
                    "findings": execution_data.get("findings", []),  # Always list
                    "risks": execution_data.get("risks", []),  # Always list
                    "confidence": float(execution_data.get("confidence", 0.7)),
                    "tools_used": tools_used,  # From tool execution
                    "errors": [],
                    "metrics": {
                        "execution_time": 0.0,  # Will be set by agent_loop
                        "timestamp": datetime.utcnow().isoformat(),
                        "retry_count": retry_count
                    }
                }
            
            result = self.agent_loop.execute_step(step, executor_fn, plan_context)
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error executing step {step.get('step_id')}: {error_msg}")
            
            # Check if we should retry
            if retry_count < max_retries:
                print(f"Retrying step {step.get('step_id')} (attempt {retry_count + 1}/{max_retries})...")
                
                # Add error context to step for retry
                retry_step = step.copy()
                retry_step["retry_count"] = retry_count + 1
                retry_step["previous_error"] = error_msg
                
                # Adjust prompt to include error context
                retry_step["description"] = (
                    step.get("description", "") + 
                    f"\n\nNOTE: Previous attempt failed with error: {error_msg}. "
                    "Please try again with more detail and error handling."
                )
                
                # Recursive retry
                return self.execute_step(retry_step, plan_context, retry_count=retry_count + 1, max_retries=max_retries)
            
            # Max retries reached
            return {
                "step_id": step.get("step_id"),
                "status": "failure",
                "output": None,
                "error": error_msg,
                "confidence": 0.0,
                "tools_used": tools_used,
                "errors": [error_msg],
                "retry_count": retry_count
            }
    
    def reflect(
        self, 
        step: Dict[str, Any], 
        execution_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Critically evaluate the executed step.
        
        Assesses correctness, completeness, compliance risk, potential
        hallucinations, and missing data. Suggests improvements or corrections.
        
        Args:
            step: The original step that was executed
            execution_result: The result from executing the step
            
        Returns:
            Reflection analysis containing quality scores, identified issues,
            suggested improvements, and whether the step needs re-execution
        """
        # Build reflection prompt
        reflection_prompt = self.prompts.get('reflection',
            'You are an AI critic. Evaluate the previous step.')
        
        full_prompt = f"""{reflection_prompt}

Step That Was Executed:
{json.dumps(step, indent=2)}

Execution Result:
{json.dumps(execution_result, indent=2)}

Please evaluate this execution on the following criteria:
1. Correctness: Is the output factually correct and logically sound?
2. Completeness: Does it fully address the step requirements?
3. Compliance Risk: Are there any compliance concerns?
4. Hallucination Risk: Any signs of fabricated information?
5. Missing Data: What additional information might be needed?

Provide your evaluation in JSON format with:
- correctness_score: 0.0 to 1.0
- completeness_score: 0.0 to 1.0
- overall_quality: 0.0 to 1.0
- confidence_score: 0.0 to 1.0 (overall confidence in the result)
- issues: list of identified problems
- suggestions: list of improvement recommendations
- requires_retry: boolean (should this step be re-executed?)
- missing_data: list of missing information

Respond ONLY with valid JSON."""
        
        try:
            # Use standardized OpenAI helper (secondary task - 30s timeout)
            openai_response = call_openai_sync(
                prompt=full_prompt,
                is_main_task=False,  # Reflection is a secondary task
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Handle mock mode or extract response
            if self.mock_mode or openai_response["status"] != "completed":
                if openai_response["status"] == "error":
                    logger.error(f"OpenAI reflection failed: {openai_response.get('error')}")
                # Fallback reflection
                reflection = {
                    "correctness_score": 0.7,
                    "completeness_score": 0.7,
                    "overall_quality": 0.7,
                    "confidence_score": 0.7,
                    "issues": [],
                    "suggestions": [],
                    "requires_retry": False,
                    "missing_data": []
                }
            else:
                # Extract response content
                result_content = openai_response.get("result", {})
                if isinstance(result_content, dict):
                    response_text = result_content.get("content", str(result_content))
                else:
                    response_text = str(result_content)
                
                # Try to parse JSON from response
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                try:
                    reflection = json.loads(response_text)
                except json.JSONDecodeError:
                    # Fallback reflection
                    reflection = {
                        "correctness_score": 0.7,
                        "completeness_score": 0.7,
                        "overall_quality": 0.7,
                        "confidence_score": 0.7,
                        "issues": [],
                        "suggestions": [],
                        "requires_retry": False,
                        "missing_data": []
                    }
            
            # Ensure all required fields exist
            if "correctness_score" not in reflection:
                reflection["correctness_score"] = 0.7
            if "completeness_score" not in reflection:
                reflection["completeness_score"] = 0.7
            if "overall_quality" not in reflection:
                reflection["overall_quality"] = 0.7
            if "confidence_score" not in reflection:
                reflection["confidence_score"] = 0.7
            if "issues" not in reflection:
                reflection["issues"] = []
            if "suggestions" not in reflection:
                reflection["suggestions"] = []
            if "requires_retry" not in reflection:
                reflection["requires_retry"] = False
            if "missing_data" not in reflection:
                reflection["missing_data"] = []
            
            return reflection
            
        except Exception as e:
            # Return default reflection on error
            return {
                "correctness_score": 0.5,
                "completeness_score": 0.5,
                "overall_quality": 0.5,
                "confidence_score": 0.5,
                "issues": [f"Reflection error: {str(e)}"],
                "suggestions": ["Manual review recommended"],
                "requires_retry": False,
                "missing_data": [],
                "error": str(e)
            }
    
    def _improve_step_from_reflection(
        self, 
        step: Dict[str, Any], 
        reflection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Improve a step based on reflection feedback.
        
        Args:
            step: Original step
            reflection: Reflection containing suggestions and issues
            
        Returns:
            Improved step with enhanced description
        """
        improved_step = step.copy()
        
        # Add suggestions to step description
        suggestions = reflection.get("suggestions", [])
        issues = reflection.get("issues", [])
        missing_data = reflection.get("missing_data", [])
        
        if suggestions or issues or missing_data:
            improvement_note = "\n\nIMPROVEMENTS NEEDED:\n"
            if issues:
                improvement_note += f"Issues to address: {', '.join(issues[:3])}\n"
            if suggestions:
                improvement_note += f"Suggestions: {', '.join(suggestions[:3])}\n"
            if missing_data:
                improvement_note += f"Missing data: {', '.join(missing_data[:3])}\n"
            
            improved_step["description"] = step.get("description", "") + improvement_note
            improved_step["retry_count"] = step.get("retry_count", 0) + 1
        
        return improved_step
    
    def run(
        self, 
        task: str, 
        context: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Run the complete agentic workflow for the given task.
        
        Orchestrates the full plan-execute-reflect cycle:
        1. Generate a strategic plan
        2. Execute each step
        3. Reflect on execution quality
        4. Adapt and iterate as needed
        5. Return final analysis
        
        Args:
            task: The compliance task to analyze
            context: Optional additional context
            max_iterations: Maximum number of plan-execute-reflect iterations
            
        Returns:
            Complete analysis result containing the final plan, all execution
            results, reflections, quality scores, and actionable insights
        """
        # Reset execution state
        self.execution_state = {
            "plan": [],
            "step_outputs": [],
            "reflections": [],
            "final_recommendation": "",
            "confidence_score": 0.0
        }
        
        try:
            # Step 1: Generate plan (3-7 steps)
            print(f"Generating plan for task: {task}")
            plan = self.plan(task, context)
            self.execution_state["plan"] = plan
            
            print(f"Plan generated with {len(plan)} steps")
            
            # Step 2: Execute each step with reflection
            iteration = 0
            high_confidence_reached = False
            
            for step_idx, step in enumerate(plan):
                if iteration >= max_iterations:
                    print(f"Max iterations ({max_iterations}) reached")
                    break
                
                if high_confidence_reached:
                    print("High confidence reached, stopping early")
                    break
                
                print(f"\nExecuting step {step_idx + 1}/{len(plan)}: {step.get('description')}")
                
                # Execute the step using agent_loop.execute_step()
                execution_result = self.execute_step(step, context)
                self.execution_state["step_outputs"].append(execution_result)
                
                print(f"Step {step_idx + 1} executed with status: {execution_result.get('status')}")
                
                # Step 3: Run reflection after each step
                print(f"Reflecting on step {step_idx + 1}")
                reflection = self.reflect(step, execution_result)
                self.execution_state["reflections"].append(reflection)
                
                # Check if retry is needed based on reflection
                if reflection.get("requires_retry", False) and iteration < max_iterations:
                    print(f"Step {step_idx + 1} requires retry based on reflection (quality: {reflection.get('overall_quality', 0.0):.2f})")
                    
                    # Improve step based on reflection suggestions
                    improved_step = self._improve_step_from_reflection(step, reflection)
                    
                    # Re-execute with improved step
                    execution_result = self.execute_step(improved_step, context)
                    self.execution_state["step_outputs"][-1] = execution_result  # Replace previous result
                    
                    # Re-reflect on improved execution
                    reflection = self.reflect(improved_step, execution_result)
                    self.execution_state["reflections"][-1] = reflection  # Replace previous reflection
                    
                    print(f"Step {step_idx + 1} retry completed. New quality: {reflection.get('overall_quality', 0.0):.2f}")
                
                # Step 4: Update memory (call agent_loop.update_memory)
                self.agent_loop.update_memory(
                    step=step,
                    result=execution_result,
                    reflection=reflection,
                    memory_store=self.memory_store
                )
                
                # Check if high confidence reached (stop condition)
                reflection_confidence = reflection.get("confidence_score", 0.0)
                overall_quality = reflection.get("overall_quality", 0.0)
                
                print(f"Reflection confidence: {reflection_confidence}, quality: {overall_quality}")
                
                # Stop if reflection shows high confidence (>= 0.85) and high quality (>= 0.85)
                if reflection_confidence >= 0.85 and overall_quality >= 0.85:
                    high_confidence_reached = True
                    print("High confidence and quality achieved")
                
                iteration += 1
            
            # Step 5: Generate final recommendation
            print("\nGenerating final recommendation")
            final_recommendation = self._generate_final_recommendation(task, context)
            self.execution_state["final_recommendation"] = final_recommendation
            
            # Calculate overall confidence score
            if self.execution_state["reflections"]:
                avg_confidence = sum(
                    r.get("confidence_score", 0.0) 
                    for r in self.execution_state["reflections"]
                ) / len(self.execution_state["reflections"])
                self.execution_state["confidence_score"] = round(avg_confidence, 2)
            else:
                self.execution_state["confidence_score"] = 0.5
            
            print(f"\nWorkflow complete. Final confidence: {self.execution_state['confidence_score']}")
            
            # Return the execution state in the required format
            return {
                "plan": self.execution_state["plan"],
                "step_outputs": self.execution_state["step_outputs"],
                "reflections": self.execution_state["reflections"],
                "final_recommendation": self.execution_state["final_recommendation"],
                "confidence_score": self.execution_state["confidence_score"]
            }
            
        except Exception as e:
            print(f"Error in orchestrator run: {e}")
            return {
                "plan": self.execution_state.get("plan", []),
                "step_outputs": self.execution_state.get("step_outputs", []),
                "reflections": self.execution_state.get("reflections", []),
                "final_recommendation": f"Error occurred: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def _generate_final_recommendation(
        self, 
        task: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a final recommendation based on all step outputs and reflections.
        
        Args:
            task: The original task
            context: Optional context
            
        Returns:
            Final recommendation string
        """
        try:
            prompt = f"""Based on the following task execution, provide a final recommendation:

Original Task: {task}

Plan Executed:
{json.dumps(self.execution_state['plan'], indent=2)}

Step Outputs:
{json.dumps(self.execution_state['step_outputs'], indent=2)}

Reflections:
{json.dumps(self.execution_state['reflections'], indent=2)}

Please provide a comprehensive final recommendation that:
1. Summarizes the key findings
2. Addresses the original task
3. Provides actionable guidance
4. Highlights any risks or concerns
5. Suggests next steps if applicable

Be clear, concise, and actionable."""
            
            # Use standardized OpenAI helper (main task - 120s timeout)
            openai_response = call_openai_sync(
                prompt=prompt,
                is_main_task=True,  # Final recommendation is a main task
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Extract response content
            if openai_response["status"] == "completed":
                result_content = openai_response.get("result", {})
                if isinstance(result_content, dict):
                    return result_content.get("content", str(result_content))
                else:
                    return str(result_content) if result_content else "No recommendation generated"
            else:
                # Fallback on error or timeout
                error_msg = openai_response.get("error", "Unknown error")
                logger.error(f"OpenAI final recommendation failed: {error_msg}")
                return f"Completed analysis of task: {task}. Review step outputs for detailed findings."
            
        except Exception as e:
            # Fallback recommendation
            logger.error(f"Error generating final recommendation: {str(e)}")
            return f"Completed analysis of task: {task}. Review step outputs for detailed findings."

