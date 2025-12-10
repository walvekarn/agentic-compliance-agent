"""
Orchestrator Module - CLEAN VERSION

Simple wrapper that delegates to AgentLoop.execute() - NO DUPLICATION
All execution logic is handled by AgentLoop - orchestrator just initializes tools and transforms results.
"""

from typing import Dict, List, Any, Optional
import logging
from backend.config import settings
from backend.agentic_engine.agent_loop import AgentLoop
from backend.agentic_engine.tools.entity_tool import EntityTool
from backend.agentic_engine.tools.calendar_tool import CalendarTool
from backend.agentic_engine.tools.http_tool import HTTPTool
from backend.agentic_engine.tools.task_tool import TaskTool

logger = logging.getLogger(__name__)


class AgenticAIOrchestrator:
    """
    Main orchestrator - CLEAN VERSION
    
    Simple wrapper that:
    1. Initializes tools
    2. Passes tools to AgentLoop
    3. Delegates ALL execution to AgentLoop.execute()
    4. Transforms AgentLoop result format to API response format
    
    NO DUPLICATION - AgentLoop handles ALL execution logic (plan, execute, reflect).
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, db_session: Optional[Any] = None):
        """
        Initialize orchestrator and tools.
        
        Args:
            config: Optional configuration dictionary
            db_session: Optional database session for tools
        """
        self.config = config or {}
        
        # Initialize tools
        tools = {
            "entity_tool": EntityTool(db_session=db_session),
            "calendar_tool": CalendarTool(),
            "http_tool": HTTPTool(),
            "task_tool": TaskTool()
        }
        
        # Initialize AgentLoop with tools - it does ALL the work
        # No duplication: AgentLoop handles planning, execution, reflection, replanning
        # Use config values if provided, otherwise use defaults optimized for speed
        max_steps = self.config.get("max_steps") or self.config.get("max_iterations") or 5
        enable_reflection = self.config.get("enable_reflection", False)  # Default False for speed
        enable_memory = self.config.get("enable_memory", True)  # Default True - memory demo enabled
        
        self.agent_loop = AgentLoop(
            max_steps=max_steps,
            enable_reflection=enable_reflection,
            enable_memory=enable_memory,
            tools=tools,  # Pass tools to agent_loop so it can use them directly
            db_session=db_session  # Pass db_session for memory operations
        )
        
        self.overall_timeout = settings.AGENTIC_OPERATION_TIMEOUT
    
    def run(
        self, 
        task: str, 
        context: Optional[Dict[str, Any]] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Run agentic workflow - DELEGATES to agent_loop.execute()
        
        AgentLoop.execute() handles:
        - Planning (generates plan using LLM)
        - Execution (executes each step with tools)
        - Reflection (evaluates execution quality)
        - Replanning (if quality is low)
        - Final recommendation generation
        
        NO DUPLICATION - all logic is in AgentLoop.
        
        Args:
            task: The compliance task to analyze
            context: Optional additional context
            max_iterations: Maximum iterations (passed to AgentLoop via max_steps)
            
        Returns:
            Complete analysis result in API format:
            {
                "plan": List of plan steps,
                "step_outputs": List of step execution results,
                "reflections": List of reflection evaluations,
                "final_recommendation": Final recommendation string,
                "confidence_score": Overall confidence (0.0-1.0)
            }
        """
        import time
        start_time = time.time()
        
        try:
            logger.info(f"Starting agentic workflow for task: {task}")
            
            # Extract entity name from context for AgentLoop
            entity_name = "Unknown"
            if context and "entity" in context:
                entity_name = context["entity"].get("entity_name", "Unknown")
            
            # AgentLoop.execute() does ALL the work:
            # - Generates plan using LLM
            # - Executes each step with tools (NO DUPLICATION)
            # - Reflects on execution quality
            # - Replans if needed
            # - Generates final recommendation
            result = self.agent_loop.execute(
                entity=entity_name,
                task=task,
                context=context
            )
            
            elapsed = time.time() - start_time
            logger.info(f"AgentLoop execution completed in {elapsed:.2f}s")
            
            # Transform agent_loop result format to API response format
            reflections = result.get("reflections", [])
            
            # Calculate overall confidence score from reflections
            confidence = 0.5  # Default
            if reflections:
                confidence_scores = [
                    r.get("confidence_score", 0.5) 
                    for r in reflections 
                    if isinstance(r, dict) and "confidence_score" in r
                ]
                if confidence_scores:
                    confidence = sum(confidence_scores) / len(confidence_scores)
            
            # Return in expected API format
            return {
                "plan": result.get("plan", []),
                "step_outputs": result.get("step_outputs", []),
                "reflections": reflections,
                "final_recommendation": result.get("recommendation", ""),
                "confidence_score": round(confidence, 2)
            }
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Orchestrator run failed after {elapsed:.2f}s: {e}", exc_info=True)
            return {
                "plan": [],
                "step_outputs": [],
                "reflections": [],
                "final_recommendation": f"Error occurred: {str(e)}",
                "confidence_score": 0.0,
                "error": str(e)
            }
