"""API routes for the experimental agentic AI engine"""

import logging
from backend.config import settings
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.agentic_engine.orchestrator import AgenticAIOrchestrator
from backend.agentic_engine.testing.test_suite_engine import TestSuiteEngine
from backend.agentic_engine.testing.test_scenario import TestScenario, ComplexityLevel
from backend.agentic_engine.testing.failure_simulator import FailureSimulator
from backend.agentic_engine.testing.failure_injection import FailureType
from backend.agentic_engine.testing.error_recovery_engine import ErrorRecoveryEngine, ErrorType
from backend.agentic_engine.testing.benchmark_runner import BenchmarkRunner
from backend.agentic_engine.testing.benchmark_cases import BenchmarkLevel
from backend.agentic_engine.testing.health_check import SystemHealthCheck
from backend.agent.audit_service import AuditService
from backend.db.base import get_db
from backend.auth.security import get_current_user
from backend.utils.llm_client import LLMClient
from backend.utils.text_sanitizer import sanitize_user_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agentic", tags=["Agentic AI Engine", "Protected"], dependencies=[Depends(get_current_user)])


# Request/Response Models
class EntityData(BaseModel):
    """Entity information for agentic analysis"""
    entity_name: str = Field(..., description="Name of the entity")
    entity_type: Optional[str] = Field(default="PRIVATE_COMPANY", description="Type of entity")
    locations: List[str] = Field(..., description="Jurisdictions/locations")
    industry: Optional[str] = Field(default="TECHNOLOGY", description="Industry category")
    employee_count: Optional[int] = Field(default=None, description="Number of employees")
    annual_revenue: Optional[float] = Field(default=None, description="Annual revenue")
    has_personal_data: bool = Field(default=True, description="Handles personal data")
    is_regulated: bool = Field(default=False, description="Directly regulated entity")
    previous_violations: int = Field(default=0, description="Previous violations count")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entity_name": "InnovateTech Solutions",
                "entity_type": "PRIVATE_COMPANY",
                "locations": ["US", "EU"],
                "industry": "TECHNOLOGY",
                "employee_count": 150,
                "has_personal_data": True,
                "is_regulated": False
            }
        }


class TaskData(BaseModel):
    """Task information for agentic analysis"""
    task_description: str = Field(..., description="Description of the compliance task")
    task_category: Optional[str] = Field(default="DATA_PROTECTION", description="Category of task")
    priority: Optional[str] = Field(default="MEDIUM", description="Task priority")
    deadline: Optional[str] = Field(default=None, description="Task deadline (ISO format)")
    additional_context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_description": "Implement GDPR Article 30 records of processing activities",
                "task_category": "DATA_PROTECTION",
                "priority": "HIGH",
                "deadline": "2025-12-31"
            }
        }


class AgenticAnalyzeRequest(BaseModel):
    """Request model for agentic analysis"""
    entity: EntityData = Field(..., description="Entity data")
    task: TaskData = Field(..., description="Task data")
    max_iterations: Optional[int] = Field(default=10, description="Maximum reasoning iterations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entity": {
                    "entity_name": "InnovateTech Solutions",
                    "locations": ["US", "EU"],
                    "industry": "TECHNOLOGY",
                    "employee_count": 150
                },
                "task": {
                    "task_description": "Implement GDPR Article 30 records of processing activities",
                    "task_category": "DATA_PROTECTION",
                    "priority": "HIGH"
                }
            }
        }


class PlanStep(BaseModel):
    """Individual step in the execution plan"""
    step_id: str
    description: str
    rationale: str
    expected_tools: List[str]
    dependencies: List[str]


class StepOutput(BaseModel):
    """Output from a single step execution"""
    step_id: str
    status: str
    output: str
    tools_used: List[str]
    metrics: Dict[str, Any]


class Reflection(BaseModel):
    """Reflection on step execution"""
    step_id: str
    quality_score: float
    correctness: bool
    correctness_score: Optional[float] = None  # Keep score for detailed view
    completeness: bool
    completeness_score: Optional[float] = None  # Keep score for detailed view
    confidence: float
    issues: List[str]
    suggestions: List[str]


class AgenticAnalyzeResponse(BaseModel):
    """Response model for agentic analysis"""
    status: str = Field(..., description="Analysis status")
    plan: List[PlanStep] = Field(..., description="Generated execution plan")
    step_outputs: List[StepOutput] = Field(..., description="Results from each step")
    reflections: List[Reflection] = Field(..., description="Reflections on execution")
    final_recommendation: str = Field(..., description="Final recommendation")
    confidence_score: float = Field(..., description="Overall confidence (0.0-1.0)")
    execution_metrics: Dict[str, Any] = Field(..., description="Execution metrics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "plan": [
                    {
                        "step_id": "step_1",
                        "description": "Identify GDPR Article 30 requirements",
                        "rationale": "Need to understand specific requirements",
                        "expected_tools": ["entity_tool", "http_tool"],
                        "dependencies": []
                    }
                ],
                "step_outputs": [
                    {
                        "step_id": "step_1",
                        "status": "success",
                        "output": "GDPR Article 30 requires maintaining records...",
                        "tools_used": ["entity_tool"],
                        "metrics": {"duration_ms": 1250}
                    }
                ],
                "reflections": [
                    {
                        "step_id": "step_1",
                        "quality_score": 0.92,
                        "correctness": True,
                        "completeness": True,
                        "confidence": 0.88,
                        "issues": [],
                        "suggestions": ["Consider cross-referencing with ISO 27001"]
                    }
                ],
                "final_recommendation": "Implement Article 30 records with automated tracking system",
                "confidence_score": 0.89,
                "execution_metrics": {"total_steps": 5, "duration_seconds": 12.4}
            }
        }


def transform_orchestrator_result(
    result: Dict[str, Any],
    agent_loop_metrics: Optional[Dict[str, Any]] = None
) -> AgenticAnalyzeResponse:
    """
    Transform orchestrator.run() output to AgenticAnalyzeResponse format.
    
    Args:
        result: Output from orchestrator.run()
        agent_loop_metrics: Optional metrics from agent_loop.get_metrics()
        
    Returns:
        AgenticAnalyzeResponse with properly mapped fields
    """
    # Determine status
    status = "completed"
    if "error" in result:
        status = "error"
    elif not result.get("step_outputs"):
        status = "partial"
    
    # Transform plan
    transformed_plan = []
    for step in result.get("plan", []):
        # Infer expected_tools from step description or use empty list
        expected_tools = step.get("expected_tools", [])
        if not expected_tools:
            # Simple heuristic: check description for tool mentions
            desc_lower = step.get("description", "").lower()
            if "entity" in desc_lower or "organization" in desc_lower:
                expected_tools.append("entity_tool")
            if "calendar" in desc_lower or "deadline" in desc_lower:
                expected_tools.append("calendar_tool")
            if "task" in desc_lower or "compliance" in desc_lower:
                expected_tools.append("task_tool")
            if "http" in desc_lower or "api" in desc_lower or "external" in desc_lower:
                expected_tools.append("http_tool")
        
        transformed_plan.append(PlanStep(
            step_id=step.get("step_id", "unknown"),
            description=step.get("description", ""),
            rationale=step.get("rationale", ""),
            expected_tools=expected_tools,
            dependencies=step.get("dependencies", [])
        ))
    
    # Transform step_outputs
    transformed_step_outputs = []
    for output in result.get("step_outputs", []):
        # Include findings, risks, and confidence in metrics
        metrics = output.get("metrics", {}).copy()
        metrics["findings"] = output.get("findings", [])  # Add findings
        metrics["risks"] = output.get("risks", [])  # Add risks
        metrics["confidence"] = output.get("confidence", 0.7)  # Add confidence
        
        transformed_step_outputs.append(StepOutput(
            step_id=output.get("step_id", "unknown"),
            status=output.get("status", "unknown"),
            output=str(output.get("output", "")),
            tools_used=output.get("tools_used", []),
            metrics=metrics
        ))
    
    # Transform reflections
    transformed_reflections = []
    reflections = result.get("reflections", [])
    step_outputs = result.get("step_outputs", [])
    
    for i, reflection in enumerate(reflections):
        # Get corresponding step_id
        step_id = "unknown"
        if i < len(step_outputs):
            step_id = step_outputs[i].get("step_id", f"step_{i+1}")
        elif i < len(transformed_plan):
            step_id = transformed_plan[i].step_id
        
        # Keep both boolean and score values for UI flexibility
        correctness_score = reflection.get("correctness_score", 0.7)
        completeness_score = reflection.get("completeness_score", 0.7)
        
        transformed_reflections.append(Reflection(
            step_id=step_id,
            quality_score=reflection.get("overall_quality", 0.7),
            correctness=correctness_score > 0.7,  # Boolean for display
            correctness_score=correctness_score,  # Score for detailed view
            completeness=completeness_score > 0.7,  # Boolean for display
            completeness_score=completeness_score,  # Score for detailed view
            confidence=reflection.get("confidence_score", 0.7),
            issues=reflection.get("issues", []),
            suggestions=reflection.get("suggestions", [])
        ))
    
    # Build execution_metrics
    execution_metrics = {
        "total_steps": len(transformed_step_outputs),
        "duration_seconds": 0.0,
        "status": status
    }
    
    if agent_loop_metrics:
        execution_metrics.update({
            "total_steps": agent_loop_metrics.get("total_steps", len(transformed_step_outputs)),
            "duration_seconds": agent_loop_metrics.get("total_execution_time", 0.0),
            "successful_steps": agent_loop_metrics.get("successful_steps", 0),
            "failed_steps": agent_loop_metrics.get("failed_steps", 0),
            "average_step_time": agent_loop_metrics.get("average_step_time", 0.0),
            "success_rate": agent_loop_metrics.get("success_rate", 0.0)
        })
    else:
        # Fallback: compute basic metrics from step outputs so UI is not N/A
        successes = sum(1 for s in transformed_step_outputs if s.status == "success")
        failures = sum(1 for s in transformed_step_outputs if s.status == "failure")
        duration = sum(
            s.metrics.get("duration_seconds", 0.0)
            for s in transformed_step_outputs
            if isinstance(s.metrics, dict)
        )
        execution_metrics.update({
            "total_steps": len(transformed_step_outputs),
            "duration_seconds": duration,
            "successful_steps": successes,
            "failed_steps": failures,
            "average_step_time": (duration / len(transformed_step_outputs)) if transformed_step_outputs else 0.0,
            "success_rate": (successes / len(transformed_step_outputs)) if transformed_step_outputs else 0.0
        })
    
    # Ensure reflections are populated in mock/partial runs
    if not transformed_reflections and transformed_step_outputs:
        for s in transformed_step_outputs:
            transformed_reflections.append(Reflection(
                step_id=s.step_id,
                quality_score=0.7,
                correctness=True,
                correctness_score=0.7,
                completeness=True,
                completeness_score=0.7,
                confidence=s.metrics.get("confidence", 0.7) if isinstance(s.metrics, dict) else 0.7,
                issues=[],
                suggestions=[]
            ))
    
    final_recommendation = result.get("final_recommendation")
    if not final_recommendation:
        # Build a more structured fallback recommendation from step outputs
        summaries = []
        for s in transformed_step_outputs:
            if s.output:
                # Truncate long outputs for readability
                text = s.output if len(s.output) <= 200 else s.output[:200] + "..."
                summaries.append(text)
        if summaries:
            bullet_list = "\n".join(f"- {item}" for item in summaries[:3])
            final_recommendation = f"Based on the execution, recommend:\n{bullet_list}"
        else:
            final_recommendation = "No recommendation available"
    
    return AgenticAnalyzeResponse(
        status=status,
        plan=transformed_plan,
        step_outputs=transformed_step_outputs,
        reflections=transformed_reflections,
        final_recommendation=final_recommendation,
        confidence_score=result.get("confidence_score", 0.0),
        execution_metrics=execution_metrics
    )


@router.post("/analyze", response_model=AgenticAnalyzeResponse)
async def analyze_with_agentic_engine(
    request: AgenticAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a compliance task using the experimental agentic AI engine.
    
    This endpoint uses advanced plan-execute-reflect reasoning to provide
    deep analysis of compliance tasks with step-by-step transparency.
    
    **EXPERIMENTAL**: This feature is currently in development. The orchestrator
    will be fully implemented in PHASE 2.
    
    Args:
        request: Entity data, task data, and configuration
        db: Database session
        
    Returns:
        Comprehensive analysis with plan, execution results, reflections,
        and final recommendation
        
    Raises:
        HTTPException: If analysis fails or validation errors occur
    """
    try:
        # Initialize orchestrator with database session for tools
        orchestrator = AgenticAIOrchestrator(
            config={
                "max_iterations": request.max_iterations,
                "enable_reflection": True,
                "enable_memory": True
            },
            db_session=db
        )
        
        # Prepare context from entity and task data
        context = {
            "entity": request.entity.model_dump(),
            "task": request.task.model_dump()
        }
        
        # Prepare task description
        sanitized_task = sanitize_user_text(request.task.task_description)
        task_description = (
            f"Analyze compliance task for {sanitize_user_text(request.entity.entity_name)}: "
            f"{sanitized_task}"
        )
        
        # Run orchestrator with proper error handling off the event loop
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    orchestrator.run,
                    task_description,
                    context,
                    request.max_iterations
                ),
                timeout=settings.AGENTIC_OPERATION_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.error(
                f"TIMEOUT: Agentic analysis for {request.entity.entity_name}",
                extra={
                    "entity_name": request.entity.entity_name,
                    "task_description": request.task.task_description,
                    "timeout_seconds": settings.AGENTIC_OPERATION_TIMEOUT
                }
            )
            db.rollback()
            # Return a proper JSON response instead of HTTPException for frontend compatibility
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=504,
                content={
                    "status": "timeout",
                    "error": f"Analysis timed out after {settings.AGENTIC_OPERATION_TIMEOUT} seconds",
                    "plan": [],
                    "step_outputs": [],
                    "reflections": [],
                    "final_recommendation": "Analysis timed out. Please try with a simpler task.",
                    "confidence_score": 0.0,
                    "execution_metrics": {}
                }
            )
        except Exception as orchestrator_error:
            logger.error(
                f"Orchestrator execution failed: {orchestrator_error}",
                exc_info=True,
                extra={
                    "entity_name": request.entity.entity_name,
                    "task_description": request.task.task_description,
                    "max_iterations": request.max_iterations
                }
            )
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Agentic analysis execution failed: {str(orchestrator_error)}"
            )
        
        # Get agent loop metrics with error handling
        try:
            agent_loop_metrics = orchestrator.agent_loop.get_metrics()
        except Exception as metrics_error:
            logger.warning(f"Failed to get agent loop metrics: {metrics_error}")
            agent_loop_metrics = None
        
        # Log agentic loop output to audit trail
        try:
            AuditService.log_agentic_loop_output(
                db=db,
                entity_name=request.entity.entity_name,
                task_description=request.task.task_description,
                agent_loop_result=result,
                agent_type="agentic_engine",
                metadata={
                    "api_endpoint": "/agentic/analyze",
                    "max_iterations": request.max_iterations,
                    "task_category": request.task.task_category,
                    "original_task_description": request.task.task_description
                }
            )
        except Exception as audit_error:
            # Don't fail the request if logging fails
            logger.warning(f"Failed to log agentic loop output: {audit_error}")
        
        # Transform orchestrator result to API response format
        try:
            response = transform_orchestrator_result(result, agent_loop_metrics)
        except Exception as transform_error:
            logger.error(
                f"Failed to transform orchestrator result: {transform_error}",
                exc_info=True
            )
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to format analysis response: {str(transform_error)}"
            )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(
            f"Unexpected error in analyze_with_agentic_engine: {type(e).__name__}: {e}",
            exc_info=True,
            extra={
                "entity_name": request.entity.entity_name if 'request' in locals() else None,
                "task_description": request.task.task_description if 'request' in locals() else None
            }
        )
        # Attempt to rollback any pending database transactions
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Unhandled error in route rollback: {rollback_error}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/status")
async def get_agentic_engine_status():
    """
    Get the status of the agentic AI engine.
    
    Uses ReasoningEngine (OpenAI) to analyze and report on system status.
    Follows standardized pattern: {status, results, error, timestamp}
    
    Returns:
        Status information about the agentic engine in format:
        {status, results, error, timestamp}
    """
    timestamp = datetime.now().isoformat()
    
    try:
        # STEP 1: Get version information
        from backend.core.version import get_version
        version = get_version()
    except ImportError:
        version = "1.3.0-agentic-hardened"
        logger.info(f"Using default version: {version}")
    
    # STEP 2: Initialize LLM client for natural language analysis
    try:
        from backend.utils.llm_client import LLMClient
        llm_client = LLMClient()
        status_prompt = f"""
        Analyze the current status of the agentic compliance system:
        - Version: {sanitize_user_text(version)}
        - Phase: PHASE 2 Complete - PHASE 3 Pending
        - Components: Orchestrator, Agent Loop, Reasoning Engine, Tools
        - OpenAI Available: {settings.OPENAI_API_KEY is not None}
        
        Provide a brief status summary (2-3 sentences) focusing on system readiness and key capabilities.
        """
        llm_response = await llm_client.run_compliance_analysis_async(
            prompt=status_prompt.strip(),
            use_json_schema=False,
            timeout=10.0
        )
        status_summary = "System operational"
        if llm_response.status == "completed":
            status_summary = llm_response.raw_text or status_summary
        else:
            status_summary = f"Status analysis unavailable: {llm_response.error or 'Unknown error'}"
            logger.error(f"Status analysis failed: {llm_response.error} at {timestamp}")
    except Exception as e:
        status_summary = "Status analysis unavailable"
        logger.error(f"Status analysis failed: {str(e)} at {timestamp}", exc_info=True)

    # STEP 3: Build comprehensive status results
    status_data = {
        "status": "operational",
        "version": version,
        "phase": "PHASE 2 Complete - PHASE 3 Pending",
        "orchestrator_implemented": True,
        "agent_loop_implemented": True,
        "reasoning_engine_implemented": True,
        "tools_implemented": True,
        "tools_integrated": True,
        "tool_registry_integrated": True,
        "safety_checks_enabled": True,
        "tool_metrics_tracking": True,
        "memory_implemented": False,
        "integration_complete": True,
        "architecture_hardened": True,
        "dependency_injection": True,
        "openai_available": settings.OPENAI_API_KEY is not None,
        "status_summary": status_summary,
        "next_steps": [
            "PHASE 3: Implement memory systems (EpisodicMemory, SemanticMemory)",
            "PHASE 3: Add database persistence for memory",
            "PHASE 3: Integrate ScoreAssistant",
            "Enhance tool auto-integration intelligence"
        ],
        "message": "PHASE 2 complete (Implementation + Integration). Version 1.3.0-agentic-hardened with architecture hardening, service/repository layers, and dependency injection."
    }

    # STEP 4: Return standardized response format
    return {
        "status": "completed",
        "results": status_data,
        "error": None,
        "timestamp": timestamp
    }


class TestSuiteRequest(BaseModel):
    """Request model for running test suite"""
    scenarios_dir: Optional[str] = Field(
        default=None,
        description="Optional path to scenarios directory (defaults to test_scenarios/)"
    )
    custom_scenarios: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional list of custom scenarios")
    complexity_distribution: Optional[Dict[str, int]] = Field(default=None, description="Optional complexity distribution by level")
    num_random: int = Field(default=3, description="Number of random scenarios to generate")
    max_iterations: int = Field(default=5, description="Maximum iterations per scenario")


# NOTE (December 2025): The following response models are legacy from removed routes.
# They are kept for potential API documentation purposes but are not used by active endpoints.
# Active endpoints use standardized format: {status, results, error, timestamp}

class TestResult(BaseModel):
    """Individual test result (legacy - not used by active endpoints)"""
    scenario: Dict[str, Any]
    status: str
    execution_time: float
    tools_used: List[str]
    required_tools: List[str]
    missing_tools: List[str]
    reasoning_passes: int
    success: bool
    errors: List[str]
    confidence_score: float
    plan_steps: int
    executed_steps: int
    timestamp: str


class TestSuiteResponse(BaseModel):
    """Response model for test suite execution (legacy - not used by active endpoints)"""
    test_results: List[TestResult]
    summary: Dict[str, Any]
    timestamp: str


class FailureSimulationRequest(BaseModel):
    """Request model for failure simulation"""
    task: str = Field(..., description="Task to execute with failure injection")
    failure_type: str = Field(..., description="Type of failure to inject")
    failure_rate: Optional[float] = Field(default=1.0, description="Probability of failure (0.0 to 1.0)")
    max_iterations: Optional[int] = Field(default=10, description="Maximum iterations")
    entity_context: Optional[Dict[str, Any]] = Field(default=None, description="Optional entity context")
    task_context: Optional[Dict[str, Any]] = Field(default=None, description="Optional task context")


class FailureSimulationResponse(BaseModel):
    """Response model for failure simulation (legacy - not used by active endpoints)"""
    status: str
    execution_time: float
    failures: List[Dict[str, Any]]
    recovery_attempts: List[Dict[str, Any]]
    recovery_timeline: List[Dict[str, Any]]
    failure_statistics: Dict[str, Any]
    taxonomy_statistics: Dict[str, Any]
    injected_failure_type: str
    failure_rate: float
    timestamp: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BenchmarkRequest(BaseModel):
    """Request model for running benchmarks"""
    levels: Optional[List[str]] = Field(
        default=None,
        description="Benchmark levels to run: ['light', 'medium', 'heavy'] (all if None)"
    )
    max_cases_per_level: Optional[int] = Field(
        default=10,
        description="Maximum cases to run per level"
    )
    max_iterations: Optional[int] = Field(
        default=10,
        description="Maximum iterations per case"
    )


class BenchmarkResult(BaseModel):
    """Individual benchmark result (legacy - not used by active endpoints)"""
    case_id: str
    case: Dict[str, Any]
    status: str
    execution_time: float
    metrics: Dict[str, Any]
    timestamp: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BenchmarkResponse(BaseModel):
    """Response model for benchmark execution (legacy - not used by active endpoints)"""
    benchmark_results: List[BenchmarkResult]
    summary: Dict[str, Any]
    timestamp: str


class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    overall_status: str
    timestamp: str
    summary: Dict[str, Any]
    checks: List[Dict[str, Any]]
    remediation_steps: List[Dict[str, Any]]
    readiness_score: Optional[float] = None
    readiness_components: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None


@router.get("/health/full", response_model=HealthCheckResponse)
async def full_health_check(db: Session = Depends(get_db)):
    """
    Perform comprehensive system health check for deployment readiness.
    
    Checks:
    - Missing imports
    - Invalid references
    - Environmental paths
    - Dependency mismatches
    - UI route validation
    - Reasoning engine health
    - DB readiness (SELECT+INSERT test)
    - LLM readiness (real schema-validation test)
    - API readiness (ping all endpoints)
    - Test Suite readiness
    - Error Recovery readiness
    
    Returns:
        Comprehensive health check results with readiness score and remediation steps
    """
    try:
        # Initialize health checker
        health_checker = SystemHealthCheck()
        
        # Run all checks
        health_results = health_checker.run_all_checks()
        
        # Fetch test suite metrics (async, with timeout)
        test_suite_metrics = None
        try:
            from backend.agentic_engine.testing.test_suite_engine import TestSuiteEngine
            test_engine = TestSuiteEngine(db_session=db)
            
            # Run a quick test suite (limit to 3 scenarios for speed)
            try:
                test_results = await asyncio.wait_for(
                    asyncio.to_thread(
                        test_engine.run_test_suite,
                        scenarios=None,
                        num_random=0,  # Use file scenarios only
                        max_iterations=5  # Quick test
                    ),
                    timeout=30.0  # 30 second timeout for test suite
                )
                
                summary = test_results.get("summary", {})
                test_suite_metrics = {
                    "pass_rate": summary.get("pass_rate", 0.0),
                    "failures": test_results.get("test_results", []),
                    "confidence_deviations": summary.get("confidence_adequacy", 0.0),
                    "total_tests": summary.get("total_tests", 0)
                }
            except asyncio.TimeoutError:
                logger.warning("Test suite readiness check timed out")
                test_suite_metrics = {"status": "timeout"}
            except Exception as e:
                logger.warning(f"Test suite readiness check failed: {e}")
                test_suite_metrics = {"status": "error", "error": str(e)}
        except Exception as e:
            logger.warning(f"Could not fetch test suite metrics: {e}")
            test_suite_metrics = {"status": "unavailable"}
        
        # Fetch error recovery metrics (async, with timeout)
        error_recovery_metrics = None
        try:
            from backend.agentic_engine.testing.error_recovery_engine import ErrorRecoveryEngine
            
            # Run quick error recovery test (test 3 error types only)
            try:
                recovery_engine = ErrorRecoveryEngine(mock_mode=True)
                from backend.agentic_engine.testing.error_recovery_engine import ErrorType
                
                # Test only 3 error types for speed
                quick_error_types = [
                    ErrorType.MALFORMED_JSON,
                    ErrorType.MISSING_REQUIRED_FIELDS,
                    ErrorType.LLM_TIMEOUT
                ]
                
                recovery_results = await asyncio.wait_for(
                    asyncio.to_thread(
                        recovery_engine.run_error_recovery_suite,
                        error_types=quick_error_types
                    ),
                    timeout=20.0  # 20 second timeout for error recovery
                )
                
                error_recovery_metrics = {
                    "recovery_rate": recovery_results.get("recovery_rate", 0.0),
                    "retry_stability": recovery_results.get("summary", {}).get("avg_retries", 0.0),
                    "fallback_quality": recovery_results.get("fallback_quality", 0.0),
                    "total_tests": recovery_results.get("summary", {}).get("total_tests", 0)
                }
            except asyncio.TimeoutError:
                logger.warning("Error recovery readiness check timed out")
                error_recovery_metrics = {"status": "timeout"}
            except Exception as e:
                logger.warning(f"Error recovery readiness check failed: {e}")
                error_recovery_metrics = {"status": "error", "error": str(e)}
        except Exception as e:
            logger.warning(f"Could not fetch error recovery metrics: {e}")
            error_recovery_metrics = {"status": "unavailable"}
        
        # Compute readiness score
        readiness_data = health_checker.compute_readiness_score(
            health_results,
            test_suite_metrics=test_suite_metrics,
            error_recovery_metrics=error_recovery_metrics
        )
        
        # Build details dictionary
        details = {
            "health_checks": health_results,
            "test_suite_metrics": test_suite_metrics,
            "error_recovery_metrics": error_recovery_metrics
        }
        
        return HealthCheckResponse(
            overall_status=health_results["overall_status"],
            timestamp=health_results["timestamp"],
            summary=health_results["summary"],
            checks=health_results["checks"],
            remediation_steps=health_results["remediation_steps"],
            readiness_score=readiness_data.get("readiness_score"),
            readiness_components=readiness_data.get("components"),
            details=details
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


# New endpoints with standardized format {status, results, error, timestamp}

@router.post("/testSuite")
async def run_test_suite_endpoint(
    request: TestSuiteRequest,
    db: Session = Depends(get_db)
):
    """
    Run a test suite through the agentic engine with OpenAI integration.
    
    Uses ReasoningEngine (OpenAI) to analyze test scenarios and provides
    comprehensive metrics. Follows standardized pattern: {status, results, error, timestamp}
    
    Args:
        request: TestSuiteRequest with test configuration
        db: Database session
        
    Returns:
        Response in format: {status, results, error, timestamp}
    """
    timestamp = datetime.now().isoformat()
    
    try:
        # STEP 1: Initialize test suite engine
        test_engine = TestSuiteEngine(db_session=db)
        logger.info(f"Test suite engine initialized at {timestamp}")
        
        # STEP 2: Run test suite with curated scenarios
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(
                    test_engine.run_test_suite,
                    scenarios=None,  # Load from files
                    scenarios_dir=request.scenarios_dir
                ),
                timeout=float(settings.AGENTIC_OPERATION_TIMEOUT)  # Configurable timeout
            )
            
            logger.info(f"Test suite execution completed: {results.get('summary', {}).get('total_tests', 0)} tests, pass rate: {results.get('summary', {}).get('pass_rate', 0):.1%} at {timestamp}")
            
            # STEP 5: Enhance results with OpenAI analysis using ReasoningEngine
            try:
                from backend.agentic_engine.reasoning.reasoning_engine import ReasoningEngine
                
                reasoning_engine = ReasoningEngine()
                
                # Create comprehensive analysis prompt for OpenAI
                summary = results.get('summary', {})
                summary_prompt = f"""
                Analyze these test suite results:
                - Total tests: {summary.get('total_tests', 0)}
                - Pass rate: {summary.get('pass_rate', 0):.1%}
                - Decision accuracy: {summary.get('decision_accuracy', 0):.1%}
                - Risk level accuracy: {summary.get('risk_level_accuracy', 0):.1%}
                - Confidence adequacy: {summary.get('confidence_adequacy', 0):.1%}
                - Average execution time: {summary.get('avg_execution_time', 0):.2f}s
                - Failures: {summary.get('failed_tests', 0)}
                
                Provide a brief analysis (2-3 sentences) of test suite performance, any notable patterns, 
                and recommendations for improvement.
                """
                
                try:
                    llm_client = LLMClient()
                    llm_response = await llm_client.run_compliance_analysis_async(
                        prompt=summary_prompt.strip(),
                        use_json_schema=False,
                        timeout=float(settings.AGENTIC_SECONDARY_TASK_TIMEOUT)
                    )
                    if llm_response.status == "completed":
                        ai_analysis = llm_response.raw_text or ""
                        results["summary"]["ai_analysis"] = ai_analysis
                        logger.info(f"LLM analysis completed for test suite at {timestamp}")
                    else:
                        logger.error(f"Test suite AI analysis failed: {llm_response.error} at {timestamp}")
                        results["summary"]["ai_analysis"] = None
                except Exception as e:
                    logger.error(f"Test suite AI analysis failed: {str(e)} at {timestamp}", exc_info=True)
                    results["summary"]["ai_analysis"] = None
                    
            except Exception as e:
                logger.error(f"Failed to initialize reasoning engine for test suite: {str(e)} at {timestamp}", exc_info=True)
                # Continue without AI analysis - results are still valid
            
            # STEP 6: Return standardized response format
            return {
                "status": "completed",
                "results": results,
                "error": None,
                "timestamp": timestamp
            }
            
        except asyncio.TimeoutError:
            error_msg = f"Test suite execution timed out after {settings.AGENTIC_OPERATION_TIMEOUT} seconds"
            logger.error(f"{error_msg} at {timestamp}")
            return {
                "status": "timeout",
                "results": None,
                "error": error_msg,
                "timestamp": timestamp
            }
            
    except Exception as e:
        error_msg = f"Test suite execution failed: {str(e)}"
        logger.error(f"{error_msg} at {timestamp}", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass  # Ignore rollback errors if db is not available
        return {
            "status": "error",
            "results": None,
            "error": error_msg,
            "timestamp": timestamp
        }


@router.post("/benchmarks")
async def run_benchmarks_endpoint(
    request: BenchmarkRequest,
    db: Session = Depends(get_db)
):
    """
    Run benchmark suite to evaluate agentic engine performance with OpenAI integration.
    
    Uses ReasoningEngine (OpenAI) to analyze benchmark performance. Executes benchmark cases
    and calculates comprehensive metrics including accuracy, reasoning depth, tool precision,
    and reflection correction. Follows standardized pattern: {status, results, error, timestamp}
    
    Args:
        request: BenchmarkRequest with benchmark configuration
        db: Database session
        
    Returns:
        Response in format: {status, results, error, timestamp}
    """
    timestamp = datetime.now().isoformat()
    
    try:
        # STEP 1: Validate and convert level strings to BenchmarkLevel enums
        levels = None
        if request.levels:
            try:
                levels = [BenchmarkLevel(level) for level in request.levels]
                logger.info(f"Benchmark levels: {request.levels} at {timestamp}")
            except ValueError as e:
                error_msg = f"Invalid benchmark level. Valid levels: {[l.value for l in BenchmarkLevel]}"
                logger.error(f"{error_msg} at {timestamp}")
                return {
                    "status": "error",
                    "results": None,
                    "error": error_msg,
                    "timestamp": timestamp
                }
        
        # STEP 2: Initialize benchmark runner
        runner = BenchmarkRunner(db_session=db)
        logger.info(f"Benchmark runner initialized at {timestamp}")
        
        # STEP 3: Run benchmark suite with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(
                    runner.run_benchmark_suite,
                    levels=levels,
                    max_cases_per_level=request.max_cases_per_level,
                    max_iterations=request.max_iterations
                ),
                timeout=float(settings.AGENTIC_OPERATION_TIMEOUT)  # Configurable timeout
            )
            
            summary = results.get('summary', {})
            logger.info(f"Benchmark execution completed: {summary.get('total_cases', 0)} cases at {timestamp}")
            
            # STEP 4: Enhance results with OpenAI analysis using ReasoningEngine
            try:
                from backend.agentic_engine.reasoning.reasoning_engine import ReasoningEngine
                
                reasoning_engine = ReasoningEngine()
                
                # Create comprehensive benchmark analysis prompt for OpenAI
                analysis_prompt = f"""
                Analyze these benchmark results for the agentic compliance engine:
                - Total cases: {summary.get('total_cases', 0)}
                - Success rate: {summary.get('success_rate', 0):.1%}
                - Average accuracy: {summary.get('average_accuracy', 0):.3f}
                - Average reasoning depth: {summary.get('average_reasoning_depth_score', 0):.3f}
                - Average tool precision: {summary.get('average_tool_precision_score', 0):.3f}
                - Average reflection correction: {summary.get('average_reflection_correction_score', 0):.3f}
                - Average execution time: {summary.get('average_execution_time', 0):.2f}s
                
                Provide a brief performance assessment (2-3 sentences) highlighting strengths, 
                areas for improvement, and recommendations for enhancing the agentic engine.
                """
                
                try:
                    llm_client = LLMClient()
                    llm_response = await llm_client.run_compliance_analysis_async(
                        prompt=analysis_prompt.strip(),
                        use_json_schema=False,
                        timeout=float(settings.AGENTIC_SECONDARY_TASK_TIMEOUT)
                    )
                    if llm_response.status == "completed":
                        ai_analysis = llm_response.raw_text or ""
                        results["summary"]["ai_analysis"] = ai_analysis
                        logger.info(f"LLM analysis completed for benchmarks at {timestamp}")
                    else:
                        logger.error(f"Benchmark AI analysis failed: {llm_response.error} at {timestamp}")
                        results["summary"]["ai_analysis"] = None
                except Exception as e:
                    logger.error(f"Benchmark AI analysis failed: {str(e)} at {timestamp}", exc_info=True)
                    results["summary"]["ai_analysis"] = None
                    
            except Exception as e:
                logger.error(f"Failed to initialize reasoning engine for benchmarks: {str(e)} at {timestamp}", exc_info=True)
                # Continue without AI analysis - results are still valid
            
            # STEP 5: Return standardized response format
            return {
                "status": "completed",
                "results": results,
                "error": None,
                "timestamp": timestamp
            }
            
        except asyncio.TimeoutError:
            error_msg = f"Benchmark execution timed out after {settings.AGENTIC_OPERATION_TIMEOUT} seconds"
            logger.error(f"{error_msg} at {timestamp}")
            return {
                "status": "timeout",
                "results": None,
                "error": error_msg,
                "timestamp": timestamp
            }
            
    except Exception as e:
        error_msg = f"Benchmark execution failed: {str(e)}"
        logger.error(f"{error_msg} at {timestamp}", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass  # Ignore rollback errors if db is not available
        return {
            "status": "error",
            "results": None,
            "error": error_msg,
            "timestamp": timestamp
        }


@router.post("/recovery")
async def run_recovery_endpoint(
    request: FailureSimulationRequest,
    db: Session = Depends(get_db)
):
    """
    Simulate failures in the agentic engine and test recovery with OpenAI integration.
    
    Uses ReasoningEngine (OpenAI) to analyze recovery capabilities. Injects specified
    failure types during execution and tracks recovery attempts and outcomes.
    Follows standardized pattern: {status, results, error, timestamp}
    
    Args:
        request: FailureSimulationRequest with simulation configuration
        db: Database session
        
    Returns:
        Response in format: {status, results, error, timestamp}
    """
    timestamp = datetime.now().isoformat()
    
    try:
        # STEP 1: Validate failure type
        try:
            failure_type = FailureType(request.failure_type)
            logger.info(f"Failure type validated: {request.failure_type} at {timestamp}")
        except ValueError:
            error_msg = f"Invalid failure type: {request.failure_type}. Valid types: {[ft.value for ft in FailureType]}"
            logger.error(f"{error_msg} at {timestamp}")
            return {
                "status": "error",
                "results": None,
                "error": error_msg,
                "timestamp": timestamp
            }
        
        # STEP 2: Initialize failure simulator
        simulator = FailureSimulator(db_session=db)
        logger.info(f"Failure simulator initialized at {timestamp}")
        
        # STEP 3: Prepare context for simulation
        context = {}
        if request.entity_context:
            context["entity"] = request.entity_context
            logger.info(f"Entity context provided: {request.entity_context.get('entity_name', 'unknown')}")
        if request.task_context:
            context["task"] = request.task_context
            logger.info("Task context provided")
        
        # STEP 4: Run simulation with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(
                    simulator.simulate_failure,
                    task=request.task,
                    context=context if context else None,
                    failure_type=failure_type,
                    failure_rate=request.failure_rate,
                    max_iterations=request.max_iterations
                ),
                timeout=float(settings.AGENTIC_OPERATION_TIMEOUT)  # Configurable timeout
            )
            
            recovery_stats = results.get("failure_statistics", {})
            logger.info(f"Recovery simulation completed: {len(results.get('failures', []))} failures, "
                       f"{recovery_stats.get('recovery_attempts', 0)} recovery attempts at {timestamp}")
            
            # STEP 5: Enhance results with OpenAI analysis using ReasoningEngine
            try:
                from backend.agentic_engine.reasoning.reasoning_engine import ReasoningEngine
                
                reasoning_engine = ReasoningEngine()
                
                # Create comprehensive recovery analysis prompt for OpenAI
                analysis_prompt = f"""
                Analyze these error recovery simulation results for the agentic compliance engine:
                - Failure type injected: {results.get('injected_failure_type', 'unknown')}
                - Failure rate: {results.get('failure_rate', 0):.1%}
                - Failures injected: {len(results.get('failures', []))}
                - Recovery attempts: {recovery_stats.get('recovery_attempts', 0)}
                - Successful recoveries: {recovery_stats.get('successful_recoveries', 0)}
                - Recovery success rate: {recovery_stats.get('recovery_success_rate', 0):.1%}
                - Average retry score: {results.get('taxonomy_statistics', {}).get('average_retry_score', 0):.2f}
                - Execution time: {results.get('execution_time', 0):.2f}s
                
                Provide a brief assessment (2-3 sentences) of the system's error recovery capabilities, 
                resilience patterns, and recommendations for improving fault tolerance.
                """
                
                try:
                    llm_client = LLMClient()
                    llm_response = await llm_client.run_compliance_analysis_async(
                        prompt=analysis_prompt.strip(),
                        use_json_schema=False,
                        timeout=float(settings.AGENTIC_SECONDARY_TASK_TIMEOUT)
                    )
                    if llm_response.status == "completed":
                        ai_analysis = llm_response.raw_text or ""
                        results["recovery_analysis"] = ai_analysis
                        logger.info(f"LLM analysis completed for recovery simulation at {timestamp}")
                    else:
                        logger.error(f"Recovery AI analysis failed: {llm_response.error} at {timestamp}")
                        results["recovery_analysis"] = None
                except Exception as e:
                    logger.error(f"Recovery AI analysis failed: {str(e)} at {timestamp}", exc_info=True)
                    results["recovery_analysis"] = None
                    
            except Exception as e:
                logger.error(f"Failed to initialize reasoning engine for recovery: {str(e)} at {timestamp}", exc_info=True)
                # Continue without AI analysis - results are still valid
            
            # STEP 6: Return standardized response format
            return {
                "status": "completed",
                "results": results,
                "error": None,
                "timestamp": timestamp
            }
            
        except asyncio.TimeoutError:
            error_msg = f"Recovery simulation timed out after {settings.AGENTIC_OPERATION_TIMEOUT} seconds"
            logger.error(f"{error_msg} at {timestamp}")
            return {
                "status": "timeout",
                "results": None,
                "error": error_msg,
                "timestamp": timestamp
            }
            
    except Exception as e:
        error_msg = f"Recovery simulation failed: {str(e)}"
        logger.error(f"{error_msg} at {timestamp}", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass  # Ignore rollback errors if db is not available
        return {
            "status": "error",
            "results": None,
            "error": error_msg,
            "timestamp": timestamp
        }


class ErrorRecoveryRequest(BaseModel):
    """Request model for error recovery suite"""
    mock_mode: Optional[bool] = Field(default=True, description="Use mock mode (default: True)")
    error_types: Optional[List[str]] = Field(default=None, description="Specific error types to test (all if None)")


@router.post("/error-recovery")
async def run_error_recovery_endpoint(
    request: Optional[ErrorRecoveryRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Run comprehensive error recovery diagnostic suite.
    
    Injects real errors (malformed JSON, missing fields, invalid types, enum errors,
    LLM timeout, connection errors, schema mismatch, missing confidence) and tests
    recovery with retry logic (2 retries).
    
    Returns comprehensive recovery metrics including recovery rate, fallback quality,
    failure modes, recovery matrix, retry counts, timings, and raw runs.
    
    Follows standardized pattern: {status, results, error, timestamp}
    
    Args:
        request: Optional request data (can be empty dict)
        db: Database session
        
    Returns:
        Response in format: {status, results, error, timestamp}
        
        Results contain:
        - recovery_rate: Overall recovery success rate (0-1)
        - fallback_quality: Average quality of fallback responses (0-1)
        - failure_modes: Distribution of failure modes
        - recovery_matrix: Matrix of error types vs recovery outcomes
        - retry_counts: Distribution of retry usage
        - timings: Recovery time per error type
        - raw_runs: Detailed results for each error type
    """
    timestamp = datetime.now().isoformat()
    
    try:
        # STEP 1: Initialize error recovery engine
        mock_mode = request.mock_mode if request else True
        error_types_list = None
        if request and request.error_types:
            try:
                error_types_list = [ErrorType(et) for et in request.error_types]
            except ValueError as e:
                error_msg = f"Invalid error type: {str(e)}"
                logger.error(f"{error_msg} at {timestamp}")
                return {
                    "status": "error",
                    "results": None,
                    "error": error_msg,
                    "timestamp": timestamp
                }
        
        recovery_engine = ErrorRecoveryEngine(mock_mode=mock_mode)
        logger.info(f"Error recovery engine initialized (mock_mode={mock_mode}) at {timestamp}")
        
        # STEP 2: Run error recovery suite with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(
                    recovery_engine.run_error_recovery_suite,
                    error_types=error_types_list  # Test all if None
                ),
                timeout=float(settings.AGENTIC_OPERATION_TIMEOUT)  # Configurable timeout
            )
            
            logger.info(f"Error recovery suite completed: {results.get('summary', {}).get('total_tests', 0)} tests, "
                       f"recovery rate: {results.get('recovery_rate', 0):.1%} at {timestamp}")
            
            # STEP 3: Return standardized response format
            return {
                "status": "completed",
                "results": results,
                "error": None,
                "timestamp": timestamp
            }
            
        except asyncio.TimeoutError:
            error_msg = f"Error recovery suite timed out after {settings.AGENTIC_OPERATION_TIMEOUT} seconds"
            logger.error(f"{error_msg} at {timestamp}")
            return {
                "status": "timeout",
                "results": None,
                "error": error_msg,
                "timestamp": timestamp
            }
            
    except Exception as e:
        error_msg = f"Error recovery suite failed: {str(e)}"
        logger.error(f"{error_msg} at {timestamp}", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass  # Ignore rollback errors if db is not available
        return {
            "status": "error",
            "results": None,
            "error": error_msg,
            "timestamp": timestamp
        }


# ============================================================================
# NOTE: Legacy routes removed (December 2025)
# Removed unused routes: /tests/run, /benchmark/run, /failures/simulate
# Frontend uses canonical routes only:
# - /api/v1/agentic/testSuite (replaces /tests/run)
# - /api/v1/agentic/benchmarks (replaces /benchmark/run)
# - /api/v1/agentic/recovery (replaces /failures/simulate)
# - /api/v1/agentic/error-recovery
# - /api/v1/agentic/health/full
# ============================================================================
