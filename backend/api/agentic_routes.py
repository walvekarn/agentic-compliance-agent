"""API routes for the experimental agentic AI engine"""

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
from backend.agentic_engine.testing.benchmark_runner import BenchmarkRunner
from backend.agentic_engine.testing.benchmark_cases import BenchmarkLevel
from backend.agentic_engine.testing.health_check import SystemHealthCheck
from backend.agent.audit_service import AuditService
from backend.db.base import get_db
from backend.auth.security import get_current_user

router = APIRouter(tags=["Agentic AI Engine", "Protected"], dependencies=[Depends(get_current_user)])


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
    
    return AgenticAnalyzeResponse(
        status=status,
        plan=transformed_plan,
        step_outputs=transformed_step_outputs,
        reflections=transformed_reflections,
        final_recommendation=result.get("final_recommendation", "No recommendation available"),
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
        task_description = (
            f"Analyze compliance task for {request.entity.entity_name}: "
            f"{request.task.task_description}"
        )
        
        # Run orchestrator
        result = orchestrator.run(
            task=task_description,
            context=context,
            max_iterations=request.max_iterations
        )
        
        # Get agent loop metrics
        agent_loop_metrics = orchestrator.agent_loop.get_metrics()
        
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
                    "task_category": request.task.task_category
                }
            )
        except Exception as e:
            # Don't fail the request if logging fails
            print(f"Warning: Failed to log agentic loop output: {e}")
        
        # Transform orchestrator result to API response format
        response = transform_orchestrator_result(result, agent_loop_metrics)
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agentic analysis failed: {str(e)}"
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
        print(f"[INFO] Using default version: {version}")
        
        # STEP 2: Initialize ReasoningEngine for natural language analysis
        from backend.agentic_engine.reasoning.reasoning_engine import ReasoningEngine
        
        reasoning_engine = ReasoningEngine()
        
        # STEP 3: Create comprehensive status prompt for OpenAI analysis
        status_prompt = f"""
        Analyze the current status of the agentic compliance system:
        - Version: {version}
        - Phase: PHASE 2 Complete - PHASE 3 Pending
        - Components: Orchestrator, Agent Loop, Reasoning Engine, Tools
        - OpenAI Available: {settings.OPENAI_API_KEY is not None}
        
        Provide a brief status summary (2-3 sentences) focusing on system readiness and key capabilities.
        """
        
        # STEP 4: Call OpenAI API using standardized helper
        from backend.agentic_engine.openai_helper import call_openai_async
        try:
            openai_response = await call_openai_async(
                prompt=status_prompt,
                is_main_task=True,  # Status check is a main task
                timeout=120.0
            )
            
            if openai_response["status"] == "completed":
                result_content = openai_response.get("result", {})
                if isinstance(result_content, dict):
                    status_summary = result_content.get("content", "System operational")
                else:
                    status_summary = str(result_content) if result_content else "System operational"
                print(f"[INFO] Status analysis completed at {timestamp}")
            else:
                error_msg = openai_response.get("error", "Unknown error")
                status_summary = f"Status analysis unavailable: {error_msg}"
                print(f"[ERROR] Status analysis failed: {error_msg} at {timestamp}")
            
        except Exception as e:
            status_summary = "Status analysis unavailable"
            print(f"[ERROR] Status analysis failed: {str(e)} at {timestamp}")
        
        # STEP 5: Build comprehensive status results
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
        
        # STEP 6: Return standardized response format
        return {
            "status": "completed",
            "results": status_data,
            "error": None,
            "timestamp": timestamp
        }
        
    except Exception as e:
        error_msg = f"Status check failed: {str(e)}"
        print(f"[ERROR] {error_msg} at {timestamp}")
        return {
            "status": "error",
            "results": None,
            "error": error_msg,
            "timestamp": timestamp
        }


class TestSuiteRequest(BaseModel):
    """Request model for running test suite"""
    num_random: Optional[int] = Field(default=5, description="Number of random scenarios to generate")
    complexity_distribution: Optional[Dict[str, int]] = Field(
        default=None,
        description="Distribution of complexity levels: {'low': 2, 'medium': 2, 'high': 1}"
    )
    max_iterations: Optional[int] = Field(default=10, description="Maximum iterations per scenario")
    custom_scenarios: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional custom scenarios to include"
    )


class TestResult(BaseModel):
    """Individual test result"""
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
    """Response model for test suite execution"""
    test_results: List[TestResult]
    summary: Dict[str, Any]
    timestamp: str


@router.post("/tests/run", response_model=TestSuiteResponse)
async def run_test_suite(
    request: TestSuiteRequest,
    db: Session = Depends(get_db)
):
    """
    Run a test suite through the agentic engine.
    
    Generates and executes test scenarios, collecting comprehensive metrics
    including execution time, tools used, reasoning passes, success rates,
    and error distributions.
    
    Args:
        request: Test suite configuration
        db: Database session
        
    Returns:
        Test suite results with metrics and summary
    """
    try:
        # Initialize test suite engine
        test_engine = TestSuiteEngine(db_session=db)
        
        # Convert custom scenarios if provided
        scenarios = None
        if request.custom_scenarios:
            scenarios = [TestScenario.from_dict(s) for s in request.custom_scenarios]
        
        # Convert complexity distribution if provided
        complexity_dist = None
        if request.complexity_distribution:
            complexity_dist = {
                ComplexityLevel(k): v 
                for k, v in request.complexity_distribution.items()
            }
        
        # Run test suite
        results = test_engine.run_test_suite(
            scenarios=scenarios,
            num_random=request.num_random,
            complexity_distribution=complexity_dist,
            max_iterations=request.max_iterations
        )
        
        # Transform results to response format
        test_results = []
        for result in results["test_results"]:
            test_results.append(TestResult(
                scenario=result["scenario"],
                status=result["status"],
                execution_time=result["execution_time"],
                tools_used=result["tools_used"],
                required_tools=result["required_tools"],
                missing_tools=result["missing_tools"],
                reasoning_passes=result["reasoning_passes"],
                success=result["success"],
                errors=result["errors"],
                confidence_score=result["confidence_score"],
                plan_steps=result["plan_steps"],
                executed_steps=result["executed_steps"],
                timestamp=result["timestamp"]
            ))
        
        return TestSuiteResponse(
            test_results=test_results,
            summary=results["summary"],
            timestamp=results["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test suite execution failed: {str(e)}"
        )


class FailureSimulationRequest(BaseModel):
    """Request model for failure simulation"""
    task: str = Field(..., description="Task to execute with failure injection")
    failure_type: str = Field(..., description="Type of failure to inject")
    failure_rate: Optional[float] = Field(default=1.0, description="Probability of failure (0.0 to 1.0)")
    max_iterations: Optional[int] = Field(default=10, description="Maximum iterations")
    entity_context: Optional[Dict[str, Any]] = Field(default=None, description="Optional entity context")
    task_context: Optional[Dict[str, Any]] = Field(default=None, description="Optional task context")


class FailureSimulationResponse(BaseModel):
    """Response model for failure simulation"""
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


@router.post("/failures/simulate", response_model=FailureSimulationResponse)
async def simulate_failure(
    request: FailureSimulationRequest,
    db: Session = Depends(get_db)
):
    """
    Simulate failures in the agentic engine and test recovery.
    
    Injects specified failure types during execution and tracks
    recovery attempts and outcomes.
    
    Args:
        request: Failure simulation configuration
        db: Database session
        
    Returns:
        Failure simulation results with recovery timeline
    """
    try:
        # Validate failure type
        try:
            failure_type = FailureType(request.failure_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid failure type: {request.failure_type}. "
                       f"Valid types: {[ft.value for ft in FailureType]}"
            )
        
        # Initialize failure simulator
        simulator = FailureSimulator(db_session=db)
        
        # Prepare context
        context = {}
        if request.entity_context:
            context["entity"] = request.entity_context
        if request.task_context:
            context["task"] = request.task_context
        
        # Run simulation
        results = simulator.simulate_failure(
            task=request.task,
            context=context if context else None,
            failure_type=failure_type,
            failure_rate=request.failure_rate,
            max_iterations=request.max_iterations
        )
        
        return FailureSimulationResponse(
            status=results["status"],
            execution_time=results["execution_time"],
            failures=results["failures"],
            recovery_attempts=results["recovery_attempts"],
            recovery_timeline=results["recovery_timeline"],
            failure_statistics=results["failure_statistics"],
            taxonomy_statistics=results["taxonomy_statistics"],
            injected_failure_type=results["injected_failure_type"],
            failure_rate=results["failure_rate"],
            timestamp=results["timestamp"],
            result=results.get("result"),
            error=results.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failure simulation failed: {str(e)}"
        )


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
    """Individual benchmark result"""
    case_id: str
    case: Dict[str, Any]
    status: str
    execution_time: float
    metrics: Dict[str, Any]
    timestamp: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BenchmarkResponse(BaseModel):
    """Response model for benchmark execution"""
    benchmark_results: List[BenchmarkResult]
    summary: Dict[str, Any]
    timestamp: str


@router.post("/benchmark/run", response_model=BenchmarkResponse)
async def run_benchmark(
    request: BenchmarkRequest,
    db: Session = Depends(get_db)
):
    """
    Run benchmark suite to evaluate agentic engine performance.
    
    Executes benchmark cases and calculates metrics including:
    - Accuracy
    - Reasoning depth score
    - Tool precision score
    - Reflection correction score
    - Average execution time
    
    Args:
        request: Benchmark configuration
        db: Database session
        
    Returns:
        Benchmark results with aggregated metrics
    """
    try:
        # Convert level strings to BenchmarkLevel enums
        levels = None
        if request.levels:
            try:
                levels = [BenchmarkLevel(level) for level in request.levels]
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid benchmark level. Valid levels: {[l.value for l in BenchmarkLevel]}"
                )
        
        # Initialize benchmark runner
        runner = BenchmarkRunner(db_session=db)
        
        # Run benchmark suite
        results = runner.run_benchmark_suite(
            levels=levels,
            max_cases_per_level=request.max_cases_per_level,
            max_iterations=request.max_iterations
        )
        
        # Transform results to response format
        benchmark_results = []
        for result in results["benchmark_results"]:
            benchmark_results.append(BenchmarkResult(
                case_id=result["case_id"],
                case=result["case"],
                status=result["status"],
                execution_time=result["execution_time"],
                metrics=result["metrics"],
                timestamp=result["timestamp"],
                result=result.get("result"),
                error=result.get("error")
            ))
        
        return BenchmarkResponse(
            benchmark_results=benchmark_results,
            summary=results["summary"],
            timestamp=results["timestamp"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark execution failed: {str(e)}"
        )


class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    overall_status: str
    timestamp: str
    summary: Dict[str, Any]
    checks: List[Dict[str, Any]]
    remediation_steps: List[Dict[str, Any]]


@router.get("/health/full", response_model=HealthCheckResponse)
async def full_health_check():
    """
    Perform comprehensive system health check for deployment readiness.
    
    Checks:
    - Missing imports
    - Invalid references
    - Environmental paths
    - Dependency mismatches
    - UI route validation
    - Reasoning engine health
    
    Returns:
        Comprehensive health check results with remediation steps
    """
    try:
        # Initialize health checker
        health_checker = SystemHealthCheck()
        
        # Run all checks
        results = health_checker.run_all_checks()
        
        return HealthCheckResponse(
            overall_status=results["overall_status"],
            timestamp=results["timestamp"],
            summary=results["summary"],
            checks=results["checks"],
            remediation_steps=results["remediation_steps"]
        )
        
    except Exception as e:
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
        print(f"[INFO] Test suite engine initialized at {timestamp}")
        
        # STEP 2: Convert custom scenarios if provided
        scenarios = None
        if request.custom_scenarios:
            scenarios = [TestScenario.from_dict(s) for s in request.custom_scenarios]
            print(f"[INFO] Using {len(scenarios)} custom scenarios")
        
        # STEP 3: Convert complexity distribution if provided
        complexity_dist = None
        if request.complexity_distribution:
            complexity_dist = {
                ComplexityLevel(k): v 
                for k, v in request.complexity_distribution.items()
            }
            print(f"[INFO] Complexity distribution: {request.complexity_distribution}")
        
        # STEP 4: Run test suite with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(
                    test_engine.run_test_suite,
                    scenarios=scenarios,
                    num_random=request.num_random,
                    complexity_distribution=complexity_dist,
                    max_iterations=request.max_iterations
                ),
                timeout=120.0  # 120 second timeout
            )
            
            print(f"[INFO] Test suite execution completed: {results.get('summary', {}).get('total_tests', 0)} tests at {timestamp}")
            
            # STEP 5: Enhance results with OpenAI analysis using ReasoningEngine
            try:
                from backend.agentic_engine.reasoning.reasoning_engine import ReasoningEngine
                
                reasoning_engine = ReasoningEngine()
                
                # Create comprehensive analysis prompt for OpenAI
                summary = results.get('summary', {})
                summary_prompt = f"""
                Analyze these test suite results:
                - Total tests: {summary.get('total_tests', 0)}
                - Success rate: {summary.get('success_rate', 0):.1%}
                - Average execution time: {summary.get('avg_execution_time', 0):.2f}s
                - Average reasoning passes: {summary.get('avg_reasoning_passes', 0):.1f}
                - Average confidence: {summary.get('avg_confidence', 0):.2f}
                
                Provide a brief analysis (2-3 sentences) of test suite performance, any notable patterns, 
                and recommendations for improvement.
                """
                
                try:
                    # Use standardized OpenAI helper (secondary task - 30s timeout)
                    from backend.agentic_engine.openai_helper import call_openai_async
                    openai_response = await call_openai_async(
                        prompt=summary_prompt,
                        is_main_task=False,  # Test suite analysis is a secondary task
                        timeout=30.0
                    )
                    
                    if openai_response["status"] == "completed":
                        result_content = openai_response.get("result", {})
                        if isinstance(result_content, dict):
                            ai_analysis = result_content.get("content", "")
                        else:
                            ai_analysis = str(result_content) if result_content else ""
                        results["summary"]["ai_analysis"] = ai_analysis
                        print(f"[INFO] OpenAI analysis completed for test suite at {timestamp}")
                    else:
                        error_msg = openai_response.get("error", "Unknown error")
                        print(f"[ERROR] Test suite AI analysis failed: {error_msg} at {timestamp}")
                        results["summary"]["ai_analysis"] = None
                except Exception as e:
                    print(f"[ERROR] Test suite AI analysis failed: {str(e)} at {timestamp}")
                    results["summary"]["ai_analysis"] = None
                    
            except Exception as e:
                print(f"[ERROR] Failed to initialize reasoning engine for test suite: {str(e)} at {timestamp}")
                # Continue without AI analysis - results are still valid
            
            # STEP 6: Return standardized response format
            return {
                "status": "completed",
                "results": results,
                "error": None,
                "timestamp": timestamp
            }
            
        except asyncio.TimeoutError:
            error_msg = "Test suite execution timed out after 120 seconds"
            print(f"[ERROR] {error_msg} at {timestamp}")
            return {
                "status": "timeout",
                "results": None,
                "error": error_msg,
                "timestamp": timestamp
            }
            
    except Exception as e:
        error_msg = f"Test suite execution failed: {str(e)}"
        print(f"[ERROR] {error_msg} at {timestamp}")
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
                print(f"[INFO] Benchmark levels: {request.levels} at {timestamp}")
            except ValueError as e:
                error_msg = f"Invalid benchmark level. Valid levels: {[l.value for l in BenchmarkLevel]}"
                print(f"[ERROR] {error_msg} at {timestamp}")
                return {
                    "status": "error",
                    "results": None,
                    "error": error_msg,
                    "timestamp": timestamp
                }
        
        # STEP 2: Initialize benchmark runner
        runner = BenchmarkRunner(db_session=db)
        print(f"[INFO] Benchmark runner initialized at {timestamp}")
        
        # STEP 3: Run benchmark suite with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(
                    runner.run_benchmark_suite,
                    levels=levels,
                    max_cases_per_level=request.max_cases_per_level,
                    max_iterations=request.max_iterations
                ),
                timeout=120.0  # 120 second timeout
            )
            
            summary = results.get('summary', {})
            print(f"[INFO] Benchmark execution completed: {summary.get('total_cases', 0)} cases at {timestamp}")
            
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
                    # Use standardized OpenAI helper (secondary task - 30s timeout)
                    from backend.agentic_engine.openai_helper import call_openai_async
                    openai_response = await call_openai_async(
                        prompt=analysis_prompt,
                        is_main_task=False,  # Benchmark analysis is a secondary task
                        timeout=30.0
                    )
                    
                    if openai_response["status"] == "completed":
                        result_content = openai_response.get("result", {})
                        if isinstance(result_content, dict):
                            ai_analysis = result_content.get("content", "")
                        else:
                            ai_analysis = str(result_content) if result_content else ""
                        results["summary"]["ai_analysis"] = ai_analysis
                        print(f"[INFO] OpenAI analysis completed for benchmarks at {timestamp}")
                    else:
                        error_msg = openai_response.get("error", "Unknown error")
                        print(f"[ERROR] Benchmark AI analysis failed: {error_msg} at {timestamp}")
                        results["summary"]["ai_analysis"] = None
                except Exception as e:
                    print(f"[ERROR] Benchmark AI analysis failed: {str(e)} at {timestamp}")
                    results["summary"]["ai_analysis"] = None
                    
            except Exception as e:
                print(f"[ERROR] Failed to initialize reasoning engine for benchmarks: {str(e)} at {timestamp}")
                # Continue without AI analysis - results are still valid
            
            # STEP 5: Return standardized response format
            return {
                "status": "completed",
                "results": results,
                "error": None,
                "timestamp": timestamp
            }
            
        except asyncio.TimeoutError:
            error_msg = "Benchmark execution timed out after 120 seconds"
            print(f"[ERROR] {error_msg} at {timestamp}")
            return {
                "status": "timeout",
                "results": None,
                "error": error_msg,
                "timestamp": timestamp
            }
            
    except Exception as e:
        error_msg = f"Benchmark execution failed: {str(e)}"
        print(f"[ERROR] {error_msg} at {timestamp}")
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
            print(f"[INFO] Failure type validated: {request.failure_type} at {timestamp}")
        except ValueError:
            error_msg = f"Invalid failure type: {request.failure_type}. Valid types: {[ft.value for ft in FailureType]}"
            print(f"[ERROR] {error_msg} at {timestamp}")
            return {
                "status": "error",
                "results": None,
                "error": error_msg,
                "timestamp": timestamp
            }
        
        # STEP 2: Initialize failure simulator
        simulator = FailureSimulator(db_session=db)
        print(f"[INFO] Failure simulator initialized at {timestamp}")
        
        # STEP 3: Prepare context for simulation
        context = {}
        if request.entity_context:
            context["entity"] = request.entity_context
            print(f"[INFO] Entity context provided: {request.entity_context.get('entity_name', 'unknown')}")
        if request.task_context:
            context["task"] = request.task_context
            print(f"[INFO] Task context provided")
        
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
                timeout=120.0  # 120 second timeout
            )
            
            recovery_stats = results.get("failure_statistics", {})
            print(f"[INFO] Recovery simulation completed: {len(results.get('failures', []))} failures, "
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
                    # Use standardized OpenAI helper (secondary task - 30s timeout)
                    from backend.agentic_engine.openai_helper import call_openai_async
                    openai_response = await call_openai_async(
                        prompt=analysis_prompt,
                        is_main_task=False,  # Recovery analysis is a secondary task
                        timeout=30.0
                    )
                    
                    if openai_response["status"] == "completed":
                        result_content = openai_response.get("result", {})
                        if isinstance(result_content, dict):
                            ai_analysis = result_content.get("content", "")
                        else:
                            ai_analysis = str(result_content) if result_content else ""
                        results["recovery_analysis"] = ai_analysis
                        print(f"[INFO] OpenAI analysis completed for recovery simulation at {timestamp}")
                    else:
                        error_msg = openai_response.get("error", "Unknown error")
                        print(f"[ERROR] Recovery AI analysis failed: {error_msg} at {timestamp}")
                        results["recovery_analysis"] = None
                except Exception as e:
                    print(f"[ERROR] Recovery AI analysis failed: {str(e)} at {timestamp}")
                    results["recovery_analysis"] = None
                    
            except Exception as e:
                print(f"[ERROR] Failed to initialize reasoning engine for recovery: {str(e)} at {timestamp}")
                # Continue without AI analysis - results are still valid
            
            # STEP 6: Return standardized response format
            return {
                "status": "completed",
                "results": results,
                "error": None,
                "timestamp": timestamp
            }
            
        except asyncio.TimeoutError:
            error_msg = "Recovery simulation timed out after 120 seconds"
            print(f"[ERROR] {error_msg} at {timestamp}")
            return {
                "status": "timeout",
                "results": None,
                "error": error_msg,
                "timestamp": timestamp
            }
            
    except Exception as e:
        error_msg = f"Recovery simulation failed: {str(e)}"
        print(f"[ERROR] {error_msg} at {timestamp}")
        return {
            "status": "error",
            "results": None,
            "error": error_msg,
            "timestamp": timestamp
        }

