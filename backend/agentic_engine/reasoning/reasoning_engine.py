"""
Reasoning Engine Module

Provides advanced reasoning capabilities including planning, execution, and reflection.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from backend.utils.llm_client import LLMClient, STANDARD_MODEL

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """
    Core reasoning engine for agentic decision-making.
    
    Provides three main capabilities:
    1. Planning - Break down tasks into strategic steps
    2. Execution - Run individual steps with context
    3. Reflection - Critically evaluate outputs
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        enable_multi_pass: bool = True,
        max_reasoning_passes: int = 3
    ):
        """
        Initialize the reasoning engine.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use (defaults to OPENAI_MODEL env var)
            temperature: Temperature for generation (0.0 to 1.0)
            max_tokens: Maximum tokens per response
            enable_multi_pass: Enable multi-pass reasoning for complex tasks
            max_reasoning_passes: Maximum number of reasoning passes
        """
        # Initialize OpenAI client using existing environment variables
        # Support mock mode when API key is not set
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", STANDARD_MODEL)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_multi_pass = enable_multi_pass
        self.max_reasoning_passes = max_reasoning_passes
        self.llm_client = LLMClient(api_key=api_key, model=self.model)
        self.mock_mode = not self.api_key or self.api_key == "mock" or (isinstance(self.api_key, str) and self.api_key.startswith("sk-mock"))
        
        if self.mock_mode:
            logger.warning("ReasoningEngine running in mock mode - OpenAI API key not set")
        
        # Load prompts from files
        self.prompts = self._load_prompts()
        
        # Track reasoning metrics
        self.reasoning_metrics = {
            "total_passes": 0,
            "pass_history": [],
            "confidence_evolution": []
        }
    
    def _llm_call(self, prompt: str, is_main: bool = True) -> Dict[str, Any]:
        """Call unified LLM client with standard timeout."""
        timeout = 120.0 if is_main else 30.0
        return self.llm_client.run_compliance_analysis(
            prompt=prompt,
            use_json_schema=False,
            timeout=timeout
        ).to_dict()
    
    def _load_prompts(self) -> Dict[str, str]:
        """
        Load prompt templates from the prompts directory.
        
        Returns:
            Dictionary mapping prompt names to their content
        """
        prompts = {}
        prompts_dir = Path(__file__).parent / "prompts"
        
        try:
            # Load planner prompt
            planner_path = prompts_dir / "planner_prompt.txt"
            if planner_path.exists():
                with open(planner_path, 'r') as f:
                    prompts['planner'] = f.read().strip()
            else:
                prompts['planner'] = "You are an AI planner. Break the task into 3-7 steps."
            
            # Load executor prompt
            executor_path = prompts_dir / "executor_prompt.txt"
            if executor_path.exists():
                with open(executor_path, 'r') as f:
                    prompts['executor'] = f.read().strip()
            else:
                prompts['executor'] = "You are an AI executor. Perform the step given."
            
            # Load reflection prompt
            reflection_path = prompts_dir / "reflection_prompt.txt"
            if reflection_path.exists():
                with open(reflection_path, 'r') as f:
                    prompts['reflection'] = f.read().strip()
            else:
                prompts['reflection'] = "You are an AI critic. Evaluate the step."
        
        except Exception as e:
            logger.warning(f"Could not load prompts: {e}")
        
        return prompts
    
    def _safe_json_parse(self, text: str) -> Any:
        """
        Safely parse JSON from text, handling markdown code blocks and errors.
        
        Args:
            text: Text that may contain JSON
            
        Returns:
            Parsed JSON object or None if parsing fails
        """
        # Remove markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            # Try to extract content between any code blocks
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1].strip()
        
        # Remove any leading/trailing whitespace
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Attempted to parse: {text[:200]}...")
            return None
    
    def generate_plan(
        self,
        entity: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a strategic plan for the given task.
        
        Breaks down the compliance task into 3-7 actionable steps using
        the planner prompt template.
        
        Args:
            entity: The entity or subject of the task (e.g., company name, jurisdiction)
            task: The compliance task to plan for
            context: Optional additional context for planning
            
        Returns:
            List of plan steps, each containing:
                - step_id: Unique identifier (e.g., "step_1")
                - description: What needs to be done
                - rationale: Why this step is important
                - expected_outcome: What should result
                - tools: Suggested tools or resources (optional)
        """
        # Build the planning prompt
        planner_prompt = self.prompts.get('planner', 
            'You are an AI planner. Break the task into 3-7 steps.')
        
        # Add context if provided
        context_str = ""
        if context:
            context_str = f"\n\nAdditional Context:\n{json.dumps(context, indent=2)}"
        
        # Construct the full prompt
        full_prompt = f"""{planner_prompt}

Entity/Subject: {entity}

Task: {task}{context_str}

Please generate a strategic plan with 3-7 steps. Each step should include:
- step_id: a unique identifier (e.g., "step_1", "step_2", ...)
- description: a clear description of what needs to be done
- rationale: why this step is important
- expected_outcome: what should result from this step

Respond ONLY with a valid JSON array of steps. Example format:
[
  {{
    "step_id": "step_1",
    "description": "Analyze requirements",
    "rationale": "Understand what needs to be evaluated",
    "expected_outcome": "Clear understanding of requirements"
  }},
  ...
]

Respond with JSON only, no other text."""
        
        try:
            llm_response = self._llm_call(full_prompt, is_main=True)
            # Handle mock mode or extract response
            if self.mock_mode or llm_response.get("status") != "completed":
                # Return mock plan for testing/demo or on error
                if llm_response.get("status") == "error":
                    logger.error(f"LLM planning failed: {llm_response.get('error')}")
                return [
                    {
                        "step_id": "step_1",
                        "description": f"Analyze {entity} requirements for {task}",
                        "rationale": "Initial analysis needed to understand scope",
                        "expected_outcome": "Requirements identified",
                        "tools": ["entity_tool", "task_tool"]
                    },
                    {
                        "step_id": "step_2",
                        "description": "Evaluate compliance risks",
                        "rationale": "Risk assessment is critical for decision making",
                        "expected_outcome": "Risk factors identified",
                        "tools": ["task_tool"]
                    },
                    {
                        "step_id": "step_3",
                        "description": "Generate recommendations",
                        "rationale": "Final step to provide actionable guidance",
                        "expected_outcome": "Recommendations provided",
                        "tools": []
                    }
                ]
            
            # Extract response content
            response_text = llm_response.get("raw_text") or ""
            if not response_text and llm_response.get("parsed_json"):
                response_text = json.dumps(llm_response["parsed_json"])
            
            # Safely parse JSON
            plan = self._safe_json_parse(response_text)
            
            if plan is None or not isinstance(plan, list):
                # Fallback to default plan
                return self._create_default_plan(entity, task)
            
            # Validate and normalize plan
            validated_plan = []
            for i, step in enumerate(plan):
                if isinstance(step, dict):
                    # Ensure required fields
                    validated_step = {
                        "step_id": step.get("step_id", f"step_{i + 1}"),
                        "description": step.get("description", f"Step {i + 1}"),
                        "rationale": step.get("rationale", "Required for task completion"),
                        "expected_outcome": step.get("expected_outcome", "Progress toward goal")
                    }
                    # Include optional fields if present
                    if "tools" in step:
                        validated_step["tools"] = step["tools"]
                    
                    validated_plan.append(validated_step)
            
            # Ensure plan has 3-7 steps
            if len(validated_plan) < 3:
                # Add generic steps to reach minimum
                while len(validated_plan) < 3:
                    validated_plan.append({
                        "step_id": f"step_{len(validated_plan) + 1}",
                        "description": f"Additional analysis step {len(validated_plan) + 1}",
                        "rationale": "Ensure comprehensive coverage",
                        "expected_outcome": "Additional insights"
                    })
            elif len(validated_plan) > 7:
                # Trim to maximum
                validated_plan = validated_plan[:7]
            
            return validated_plan
            
        except Exception as e:
            logger.error(f"Error in generate_plan: {e}")
            return self._create_default_plan(entity, task)
    
    def _create_default_plan(self, entity: str, task: str) -> List[Dict[str, Any]]:
        """
        Create a default plan when API call fails.
        
        Args:
            entity: The entity or subject
            task: The task description
            
        Returns:
            Default 4-step plan
        """
        return [
            {
                "step_id": "step_1",
                "description": f"Analyze {entity} compliance requirements",
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
                "description": "Generate recommendations and report",
                "rationale": "Provide actionable guidance",
                "expected_outcome": "Complete compliance recommendation"
            }
        ]
    
    def run_step(
        self,
        step: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        use_multi_pass: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Execute a single step from the plan with optional multi-pass reasoning.
        
        Uses the executor prompt template to perform the step's action,
        gathering facts, analyzing risks, and filling in missing context.
        Supports multi-pass reasoning for complex tasks.
        
        Args:
            step: The step to execute, containing at minimum:
                - step_id: Step identifier
                - description: What to do
            context: Optional execution context (e.g., previous results, available tools)
            use_multi_pass: Override multi-pass setting (defaults to self.enable_multi_pass)
            
        Returns:
            Execution result containing:
                - step_id: The executed step's ID
                - output: The main execution result
                - findings: Key findings or insights (list)
                - risks: Identified risks or concerns (list)
                - confidence: Confidence in the execution (0.0 to 1.0)
                - status: 'success' or 'failure'
                - reasoning_passes: Number of reasoning passes used (if multi-pass enabled)
        """
        use_multi_pass = use_multi_pass if use_multi_pass is not None else self.enable_multi_pass
        
        # For complex steps, use multi-pass reasoning
        if use_multi_pass and self._is_complex_step(step, context):
            return self._run_step_multi_pass(step, context)
        
        # Standard single-pass execution
        return self._run_step_single_pass(step, context)
    
    def _run_step_single_pass(
        self,
        step: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a step using single-pass reasoning.
        
        Args:
            step: The step to execute
            context: Optional execution context
            
        Returns:
            Execution result
        """
        # Build the execution prompt
        executor_prompt = self.prompts.get('executor',
            'You are an AI executor. Perform the step given.')
        
        # Extract step information
        step_id = step.get("step_id", "unknown")
        description = step.get("description", str(step))
        rationale = step.get("rationale", "")
        
        # Add context if provided
        context_str = ""
        if context:
            context_str = f"\n\nExecution Context:\n{json.dumps(context, indent=2)}"
        
        # Construct the full prompt
        full_prompt = f"""{executor_prompt}

Step to Execute:
ID: {step_id}
Description: {description}
Rationale: {rationale}{context_str}

Please execute this step and provide:
1. The main output/result of executing this step
2. Key findings or insights discovered
3. Any risks or concerns identified
4. Your confidence in this execution (0.0 to 1.0)

Respond ONLY with valid JSON in this format:
{{
  "output": "Main result of the step execution",
  "findings": ["Finding 1", "Finding 2", ...],
  "risks": ["Risk 1", "Risk 2", ...],
  "confidence": 0.85
}}

Respond with JSON only, no other text."""
        
        try:
            llm_response = self._llm_call(full_prompt, is_main=True)
            # Handle mock mode or extract response
            if self.mock_mode or llm_response.get("status") != "completed":
                if llm_response.get("status") == "error":
                    logger.error(f"LLM step execution failed: {llm_response.get('error')}")
                execution_data = {
                    "output": f"Mock execution of step {step_id}: {step.get('description', 'Unknown step')}",
                    "findings": [f"Finding from {step_id}", "Analysis completed"],
                    "risks": [],
                    "confidence": 0.75
                }
            else:
                response_text = llm_response.get("raw_text") or ""
                if not response_text and llm_response.get("parsed_json"):
                    response_text = json.dumps(llm_response["parsed_json"])
                # Safely parse JSON
                execution_data = self._safe_json_parse(response_text)
                
                if execution_data is None or not isinstance(execution_data, dict):
                    # Fallback result
                    execution_data = {
                        "output": response_text if response_text else "Step executed",
                        "findings": [],
                        "risks": [],
                        "confidence": 0.5
                    }
            
            # Build result with validated fields
            result = {
                "step_id": step_id,
                "status": "success",
                "output": execution_data.get("output", "Step executed"),
                "findings": execution_data.get("findings", []),
                "risks": execution_data.get("risks", []),
                "confidence": float(execution_data.get("confidence", 0.7))
            }
            
            # Ensure confidence is in valid range
            result["confidence"] = max(0.0, min(1.0, result["confidence"]))
            
            # Ensure findings and risks are lists
            if not isinstance(result["findings"], list):
                result["findings"] = [str(result["findings"])] if result["findings"] else []
            if not isinstance(result["risks"], list):
                result["risks"] = [str(result["risks"])] if result["risks"] else []
            
            return result
            
        except Exception as e:
            logger.error(f"Error in run_step: {e}")
            # Return error result
            return {
                "step_id": step_id,
                "status": "failure",
                "output": None,
                "findings": [],
                "risks": [f"Execution error: {str(e)}"],
                "confidence": 0.0,
                "error": str(e)
            }
    
    def reflect(
        self,
        step: Dict[str, Any],
        output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Critically evaluate a completed step and its output.
        
        Uses the reflection prompt template to assess correctness,
        completeness, compliance risks, potential hallucinations,
        and missing data.
        
        Args:
            step: The original step that was executed
            output: The execution result/output to evaluate
            
        Returns:
            Reflection analysis containing:
                - correctness_score: Rating of factual correctness (0.0 to 1.0)
                - completeness_score: Rating of completeness (0.0 to 1.0)
                - overall_quality: Overall quality rating (0.0 to 1.0)
                - confidence_score: Confidence in the result (0.0 to 1.0)
                - issues: List of identified problems or concerns
                - suggestions: List of improvement recommendations
                - requires_retry: Boolean indicating if step should be re-executed
                - missing_data: List of missing information items
        """
        # Build the reflection prompt
        reflection_prompt = self.prompts.get('reflection',
            'You are an AI critic. Evaluate the step.')
        
        # Construct the full prompt
        full_prompt = f"""{reflection_prompt}

Step That Was Executed:
{json.dumps(step, indent=2)}

Execution Output:
{json.dumps(output, indent=2)}

Please critically evaluate this execution on the following criteria:

1. Correctness: Is the output factually correct and logically sound?
2. Completeness: Does it fully address the step requirements?
3. Compliance Risk: Are there any compliance concerns or risks?
4. Hallucination Risk: Any signs of fabricated or uncertain information?
5. Missing Data: What additional information might be needed?

Provide your evaluation in JSON format with these exact fields:
{{
  "correctness_score": 0.0 to 1.0,
  "completeness_score": 0.0 to 1.0,
  "overall_quality": 0.0 to 1.0,
  "confidence_score": 0.0 to 1.0,
  "issues": ["Issue 1", "Issue 2", ...],
  "suggestions": ["Suggestion 1", "Suggestion 2", ...],
  "requires_retry": true or false,
  "missing_data": ["Missing item 1", "Missing item 2", ...]
}}

Respond with JSON only, no other text."""
        
        try:
            llm_response = self._llm_call(full_prompt, is_main=False)
            # Handle mock mode or extract response
            if self.mock_mode or llm_response.get("status") != "completed":
                if llm_response.get("status") == "error":
                    logger.error(f"LLM reflection failed: {llm_response.get('error')}")
                reflection_data = {
                    "correctness_score": 0.8,
                    "completeness_score": 0.75,
                    "overall_quality": 0.77,
                    "confidence_score": 0.75,
                    "issues": [],
                    "suggestions": ["Consider additional validation"],
                    "requires_retry": False,
                    "missing_data": []
                }
            else:
                response_text = llm_response.get("raw_text") or ""
                if not response_text and llm_response.get("parsed_json"):
                    response_text = json.dumps(llm_response["parsed_json"])
                # Safely parse JSON
                reflection_data = self._safe_json_parse(response_text)
                
                if reflection_data is None or not isinstance(reflection_data, dict):
                    # Fallback reflection
                    reflection_data = {
                        "correctness_score": 0.7,
                        "completeness_score": 0.7,
                        "overall_quality": 0.7,
                        "confidence_score": 0.7,
                        "issues": [],
                        "suggestions": [],
                        "requires_retry": False,
                        "missing_data": []
                    }
            
            # Build result with validated fields
            result = {
                "correctness_score": float(reflection_data.get("correctness_score", 0.7)),
                "completeness_score": float(reflection_data.get("completeness_score", 0.7)),
                "overall_quality": float(reflection_data.get("overall_quality", 0.7)),
                "confidence_score": float(reflection_data.get("confidence_score", 0.7)),
                "issues": reflection_data.get("issues", []),
                "suggestions": reflection_data.get("suggestions", []),
                "requires_retry": bool(reflection_data.get("requires_retry", False)),
                "missing_data": reflection_data.get("missing_data", [])
            }
            
            # Ensure all scores are in valid range [0.0, 1.0]
            for score_key in ["correctness_score", "completeness_score", "overall_quality", "confidence_score"]:
                result[score_key] = max(0.0, min(1.0, result[score_key]))
            
            # Ensure list fields are actually lists
            for list_key in ["issues", "suggestions", "missing_data"]:
                if not isinstance(result[list_key], list):
                    result[list_key] = [str(result[list_key])] if result[list_key] else []
            
            return result
            
        except Exception as e:
            logger.error(f"Error in reflect: {e}")
            # Return default reflection with error noted
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
    
    def _is_complex_step(self, step: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if a step is complex enough to warrant multi-pass reasoning.
        
        Args:
            step: The step to evaluate
            context: Optional context
            
        Returns:
            True if step should use multi-pass reasoning
        """
        description = step.get("description", "").lower()
        
        # Complex indicators
        complex_keywords = [
            "analyze", "assess", "evaluate", "comprehensive", "detailed",
            "multiple", "complex", "critical", "high-risk", "regulatory"
        ]
        
        # Check if description contains complex keywords
        if any(keyword in description for keyword in complex_keywords):
            return True
        
        # Check if step mentions multiple regulations or jurisdictions
        if context:
            entity = context.get("entity", {})
            if isinstance(entity, dict):
                locations = entity.get("locations", [])
                if len(locations) > 1:
                    return True
        
        return False
    
    def _run_step_multi_pass(
        self,
        step: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a step using multi-pass reasoning for complex tasks.
        
        Performs multiple reasoning passes, refining the result with each pass.
        
        Args:
            step: The step to execute
            context: Optional execution context
            
        Returns:
            Execution result with reasoning_passes field
        """
        step_id = step.get("step_id", "unknown")
        all_findings = []
        all_risks = []
        pass_results = []
        confidence_scores = []
        
        # Perform multiple reasoning passes
        for pass_num in range(1, self.max_reasoning_passes + 1):
            self.reasoning_metrics["total_passes"] += 1
            
            # Build prompt with previous pass context
            previous_context = ""
            if pass_num > 1:
                previous_context = f"\n\nPrevious Pass {pass_num - 1} Results:\n"
                prev_result = pass_results[-1]
                previous_context += f"Output: {prev_result.get('output', '')[:200]}...\n"
                previous_context += f"Findings: {', '.join(prev_result.get('findings', [])[:3])}\n"
                previous_context += f"Confidence: {prev_result.get('confidence', 0.0):.2f}\n"
                previous_context += "\nPlease refine and improve upon the previous pass."
            
            executor_prompt = self.prompts.get('executor',
                'You are an AI executor. Perform the step given.')
            
            step_description = step.get("description", "")
            step_rationale = step.get("rationale", "")
            
            context_str = ""
            if context:
                context_str = f"\n\nExecution Context:\n{json.dumps(context, indent=2)}"
            
            full_prompt = f"""{executor_prompt}

Step to Execute (Pass {pass_num}/{self.max_reasoning_passes}):
ID: {step_id}
Description: {step_description}
Rationale: {step_rationale}{context_str}{previous_context}

This is reasoning pass {pass_num} of {self.max_reasoning_passes}. 
Please {'refine and improve' if pass_num > 1 else 'execute'} this step and provide:
1. The main output/result
2. Key findings or insights
3. Any risks or concerns
4. Your confidence (0.0 to 1.0)

Respond ONLY with valid JSON: {{"output": "...", "findings": [...], "risks": [...], "confidence": 0.85}}"""
            
            try:
                llm_response = self._llm_call(full_prompt, is_main=True)
                
                # Handle mock mode or extract response
                if self.mock_mode or llm_response.get("status") != "completed":
                    if llm_response.get("status") == "error":
                        logger.error(f"LLM multi-pass reasoning failed: {llm_response.get('error')}")
                    execution_data = {
                        "output": f"Mock multi-pass execution result for step {step_id} (pass {pass_num})",
                        "findings": [f"Multi-pass analysis completed (pass {pass_num})"],
                        "risks": [],
                        "confidence": 0.8
                    }
                else:
                    response_text = llm_response.get("raw_text") or ""
                    if not response_text and llm_response.get("parsed_json"):
                        response_text = json.dumps(llm_response["parsed_json"])
                    execution_data = self._safe_json_parse(response_text)
                    
                    if execution_data is None or not isinstance(execution_data, dict):
                        execution_data = {
                            "output": response_text if response_text else "Step executed",
                            "findings": [],
                            "risks": [],
                            "confidence": 0.5
                        }
                
                pass_result = {
                    "pass": pass_num,
                    "output": execution_data.get("output", "Step executed"),
                    "findings": execution_data.get("findings", []),
                    "risks": execution_data.get("risks", []),
                    "confidence": float(execution_data.get("confidence", 0.7))
                }
                
                pass_result["confidence"] = max(0.0, min(1.0, pass_result["confidence"]))
                pass_results.append(pass_result)
                confidence_scores.append(pass_result["confidence"])
                all_findings.extend(pass_result.get("findings", []))
                all_risks.extend(pass_result.get("risks", []))
                
                # Track in metrics
                self.reasoning_metrics["pass_history"].append({
                    "step_id": step_id,
                    "pass": pass_num,
                    "confidence": pass_result["confidence"]
                })
                self.reasoning_metrics["confidence_evolution"].append(pass_result["confidence"])
                
                # Early stopping if confidence is high and stable
                if pass_num > 1:
                    confidence_delta = abs(confidence_scores[-1] - confidence_scores[-2])
                    if confidence_scores[-1] >= 0.85 and confidence_delta < 0.05:
                        break
                
            except Exception as e:
                logger.error(f"Error in multi-pass reasoning pass {pass_num}: {e}")
                if pass_num == 1:
                    # Fallback to single-pass on first pass error
                    return self._run_step_single_pass(step, context)
        
        # Aggregate results from all passes
        final_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.7
        
        # Deduplicate findings and risks
        unique_findings = list(dict.fromkeys(all_findings))  # Preserve order
        unique_risks = list(dict.fromkeys(all_risks))
        
        return {
            "step_id": step_id,
            "status": "success",
            "output": pass_results[-1].get("output", "Step executed") if pass_results else "Step executed",
            "findings": unique_findings[:10],  # Limit to top 10
            "risks": unique_risks[:10],  # Limit to top 10
            "confidence": final_confidence,
            "reasoning_passes": len(pass_results),
            "pass_results": pass_results  # Include all pass results for transparency
        }
