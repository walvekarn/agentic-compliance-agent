"""
Testing Module for Agentic Engine
===================================

This module provides comprehensive testing, benchmarking, and health checking capabilities
for the agentic compliance engine.

**Core Components:**

1. **TestSuiteEngine** - Generates and executes test scenarios
   - Creates deterministic and random test scenarios
   - Executes tests through the orchestrator
   - Collects comprehensive metrics (execution time, tool usage, reasoning passes)
   - Supports complexity distribution (LOW, MEDIUM, HIGH)

2. **BenchmarkRunner** - Performance benchmarking
   - Runs benchmark cases at different levels (light, medium, heavy)
   - Calculates accuracy, reasoning depth, tool precision scores
   - Tracks reflection correction rates
   - Generates performance reports

3. **FailureSimulator** - Error recovery testing
   - Injects various failure types (timeout, tool_error, reasoning_error, etc.)
   - Tests system recovery capabilities
   - Tracks recovery success rates
   - Generates failure taxonomy statistics

4. **SystemHealthCheck** - Deployment readiness validation
   - Checks missing imports and invalid references
   - Validates environmental paths
   - Detects dependency mismatches
   - Provides remediation steps

**Usage Examples:**

```python
# Run test suite
from backend.agentic_engine.testing import TestSuiteEngine

engine = TestSuiteEngine(db_session=db)
results = engine.run_test_suite(
    num_random=5,
    complexity_distribution={"low": 2, "medium": 2, "high": 1},
    max_iterations=10
)

# Run benchmarks
from backend.agentic_engine.testing import BenchmarkRunner

runner = BenchmarkRunner(db_session=db)
results = runner.run_benchmark_suite(
    levels=[BenchmarkLevel.LIGHT, BenchmarkLevel.MEDIUM],
    max_cases_per_level=10
)

# Simulate failures
from backend.agentic_engine.testing import FailureSimulator, FailureType

simulator = FailureSimulator(db_session=db)
results = simulator.simulate_failure(
    task="Test task",
    failure_type=FailureType.TOOL_ERROR,
    failure_rate=0.3
)
```

**API Endpoints:**
- `POST /api/v1/agentic/testSuite` - Run test suite
- `POST /api/v1/agentic/benchmarks` - Run benchmarks
- `POST /api/v1/agentic/recovery` - Error recovery simulation
- `GET /api/v1/agentic/health/full` - System health check
"""

from .test_scenario import TestScenario
from .test_suite_engine import TestSuiteEngine
from .failure_injection import FailureInjectionLayer, FailureType
from .failure_taxonomy import FailureTaxonomy, FailureCategory, RetryStrategy, FailureRecord
from .benchmark_cases import BenchmarkCases, BenchmarkCase, BenchmarkLevel
from .benchmark_runner import BenchmarkRunner
from .health_check import SystemHealthCheck, HealthCheckResult

__all__ = [
    "TestScenario",
    "TestSuiteEngine",
    "FailureInjectionLayer",
    "FailureType",
    "FailureTaxonomy",
    "FailureCategory",
    "RetryStrategy",
    "FailureRecord",
    "BenchmarkCases",
    "BenchmarkCase",
    "BenchmarkLevel",
    "BenchmarkRunner",
    "SystemHealthCheck",
    "HealthCheckResult",
]

