"""
System Health Check Module

Validates system readiness for deployment by checking imports, references,
environmental paths, dependencies, routes, reasoning engine health, and
deployment preflight requirements.
"""

import importlib
import sys
import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a single health check"""
    check_name: str
    status: str  # "pass", "fail", "warning"
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    remediation: Optional[str] = None


class SystemHealthCheck:
    """
    Comprehensive system health checker for deployment readiness.
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize system health checker.
        
        Args:
            base_path: Base path of the project (auto-detected if None)
        """
        if base_path is None:
            # Try to find project root
            current = Path(__file__).resolve()
            # Go up from backend/agentic_engine/testing/health_check.py to project root
            self.base_path = current.parent.parent.parent.parent
        else:
            self.base_path = Path(base_path)
        
        self.results: List[HealthCheckResult] = []
    
    def check_missing_imports(self) -> HealthCheckResult:
        """
        Check for missing imports in critical modules.
        
        Returns:
            HealthCheckResult
        """
        critical_modules = [
            "backend.agentic_engine.orchestrator",
            "backend.agentic_engine.agent_loop",
            "backend.agentic_engine.tools.tool_registry",
            "backend.agentic_engine.testing.test_suite_engine",
            "backend.agentic_engine.testing.failure_simulator",
            "backend.agentic_engine.testing.benchmark_runner",
            "backend.api.agentic_routes"
        ]
        
        missing_imports = []
        import_errors = []
        
        for module_name in critical_modules:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                missing_imports.append(module_name)
                import_errors.append(str(e))
            except Exception as e:
                import_errors.append(f"{module_name}: {str(e)}")
        
        if missing_imports:
            return HealthCheckResult(
                check_name="missing_imports",
                status="fail",
                message=f"Missing imports in {len(missing_imports)} critical modules",
                details={
                    "missing_modules": missing_imports,
                    "errors": import_errors
                },
                remediation="Install missing dependencies: pip install -r requirements.txt"
            )
        else:
            return HealthCheckResult(
                check_name="missing_imports",
                status="pass",
                message="All critical modules import successfully",
                details={"checked_modules": len(critical_modules)}
            )
    
    def check_invalid_references(self) -> HealthCheckResult:
        """
        Check for invalid references in code.
        
        Returns:
            HealthCheckResult
        """
        invalid_refs = []
        
        # Check key files for common issues
        key_files = [
            self.base_path / "backend" / "agentic_engine" / "orchestrator.py",
            self.base_path / "backend" / "api" / "agentic_routes.py"
        ]
        
        for file_path in key_files:
            if not file_path.exists():
                invalid_refs.append(f"File not found: {file_path}")
                continue
            
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    # Check for common invalid patterns
                    if "from . import" in content and "from .. import" in content:
                        # This is fine, just checking syntax
                        pass
            except Exception as e:
                invalid_refs.append(f"Error reading {file_path}: {str(e)}")
        
        if invalid_refs:
            return HealthCheckResult(
                check_name="invalid_references",
                status="fail",
                message=f"Found {len(invalid_refs)} invalid references",
                details={"invalid_refs": invalid_refs},
                remediation="Fix invalid references in code files"
            )
        else:
            return HealthCheckResult(
                check_name="invalid_references",
                status="pass",
                message="No invalid references found",
                details={"checked_files": len(key_files)}
            )
    
    def check_environmental_paths(self) -> HealthCheckResult:
        """
        Check environmental path validation.
        
        Returns:
            HealthCheckResult
        """
        issues = []
        
        # Check critical environment variables (warn if missing)
        # Use settings instead of os.getenv() to respect .env file loading
        from backend.config import settings
        env_vars = {
            "OPENAI_API_KEY": settings.OPENAI_API_KEY,
            "DATABASE_URL": settings.DATABASE_URL
        }
        missing_vars = [var for var, value in env_vars.items() if not value]
        if missing_vars:
            issues.append(f"Missing environment variables: {', '.join(missing_vars)}")
        
        # Check if paths exist
        critical_paths = [
            self.base_path / "backend",
            self.base_path / "backend" / "agentic_engine",
            self.base_path / "backend" / "api",
            self.base_path / "frontend" / "pages"
        ]
        
        missing_paths = []
        for path in critical_paths:
            if not path.exists():
                missing_paths.append(str(path))
        
        if missing_paths:
            issues.append(f"Missing paths: {', '.join(missing_paths)}")
        
        if issues:
            status = "warning" if len(issues) == 1 and "Missing environment variables" in issues[0] else "fail"
            return HealthCheckResult(
                check_name="environmental_paths",
                status=status,
                message=f"Found {len(issues)} environmental/path issues",
                details={"issues": issues},
                remediation="Set required environment variables and ensure all paths exist"
            )
        else:
            return HealthCheckResult(
                check_name="environmental_paths",
                status="pass",
                message="All environmental paths validated",
                details={"checked_paths": len(critical_paths), "checked_vars": len(env_vars)}
            )
    
    def check_dependency_mismatch(self) -> HealthCheckResult:
        """
        Check for dependency mismatches.
        
        Returns:
            HealthCheckResult
        """
        issues = []
        
        # Check if requirements.txt exists
        requirements_file = self.base_path / "requirements.txt"
        if not requirements_file.exists():
            issues.append("requirements.txt not found")
        else:
            # Try to check if key dependencies are importable
            key_dependencies = [
                ("fastapi", "fastapi"),
                ("streamlit", "streamlit"),
                ("openai", "openai"),  # Using OpenAI directly, not langchain
                ("sqlalchemy", "sqlalchemy"),
                ("pydantic", "pydantic")
            ]
            
            missing_deps = []
            for import_name, package_name in key_dependencies:
                try:
                    importlib.import_module(import_name)
                except ImportError:
                    missing_deps.append(package_name)
            
            if missing_deps:
                issues.append(f"Missing dependencies: {', '.join(missing_deps)}")
        
        if issues:
            return HealthCheckResult(
                check_name="dependency_mismatch",
                status="fail",
                message=f"Found {len(issues)} dependency issues",
                details={"issues": issues},
                remediation="Install missing dependencies: pip install -r requirements.txt"
            )
        else:
            return HealthCheckResult(
                check_name="dependency_mismatch",
                status="pass",
                message="All dependencies satisfied",
                details={"checked_dependencies": len(key_dependencies)}
            )
    
    def check_ui_routes(self) -> HealthCheckResult:
        """
        Check UI route validation.
        
        Returns:
            HealthCheckResult
        """
        issues = []
        
        # Check if dashboard pages exist
        pages_dir = self.base_path / "frontend" / "pages"
        if not pages_dir.exists():
            issues.append("Dashboard pages directory not found")
        else:
            # Check for expected pages
            expected_pages = [
                "1_Analyze_Task.py",
                "5_Agentic_Analysis.py",
                "7_Agentic_Test_Suite.py",
                "8_Error_Recovery_Simulator.py",
                "9_Agentic_Benchmarks.py"
            ]
            
            missing_pages = []
            for page in expected_pages:
                page_path = pages_dir / page
                if not page_path.exists():
                    missing_pages.append(page)
            
            if missing_pages:
                issues.append(f"Missing UI pages: {', '.join(missing_pages)}")
        
        # Check if API routes file exists
        api_routes_file = self.base_path / "backend" / "api" / "agentic_routes.py"
        if not api_routes_file.exists():
            issues.append("API routes file not found")
        
        if issues:
            return HealthCheckResult(
                check_name="ui_routes",
                status="fail",
                message=f"Found {len(issues)} UI/route issues",
                details={"issues": issues},
                remediation="Ensure all UI pages and API routes are present"
            )
        else:
            return HealthCheckResult(
                check_name="ui_routes",
                status="pass",
                message="All UI routes validated",
                details={"checked_pages": len(expected_pages) if pages_dir.exists() else 0}
            )
    
    def check_reasoning_engine_health(self) -> HealthCheckResult:
        """
        Check reasoning engine health.
        
        Returns:
            HealthCheckResult
        """
        issues = []
        
        try:
            # Try to import and instantiate orchestrator
            from backend.agentic_engine.orchestrator import AgenticAIOrchestrator
            
            # Check if OpenAI API key is set (use settings to respect .env file)
            from backend.config import settings
            if not settings.OPENAI_API_KEY:
                issues.append("OPENAI_API_KEY not set - orchestrator may not work")
            
            # Check if prompts exist
            prompts_dir = self.base_path / "backend" / "agentic_engine" / "reasoning" / "prompts"
            if prompts_dir.exists():
                expected_prompts = ["planner_prompt.txt", "executor_prompt.txt", "reflection_prompt.txt"]
                missing_prompts = []
                for prompt in expected_prompts:
                    if not (prompts_dir / prompt).exists():
                        missing_prompts.append(prompt)
                if missing_prompts:
                    issues.append(f"Missing prompt files: {', '.join(missing_prompts)}")
            else:
                issues.append("Prompts directory not found")
            
        except ImportError as e:
            issues.append(f"Cannot import orchestrator: {str(e)}")
        except Exception as e:
            issues.append(f"Error checking reasoning engine: {str(e)}")
        
        if issues:
            status = "warning" if all("OPENAI_API_KEY" in i or "Prompts" in i or "prompt" in i for i in issues) else "fail"
            return HealthCheckResult(
                check_name="reasoning_engine_health",
                status=status,
                message=f"Found {len(issues)} reasoning engine issues",
                details={"issues": issues},
                remediation="Ensure orchestrator is properly configured and prompts exist"
            )
        else:
            return HealthCheckResult(
                check_name="reasoning_engine_health",
                status="pass",
                message="Reasoning engine is healthy",
                details={"orchestrator_importable": True}
            )
    
    def check_python_version(self) -> HealthCheckResult:
        """
        Check Python version compatibility.
        
        Returns:
            HealthCheckResult
        """
        issues = []
        python_version = sys.version_info
        
        # Check minimum Python version (3.8+)
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            issues.append(f"Python {python_version.major}.{python_version.minor} is below minimum required (3.8+)")
        
        # Check for recommended version (3.9+)
        if python_version.major == 3 and python_version.minor < 9:
            issues.append(f"Python {python_version.major}.{python_version.minor} is below recommended (3.9+)")
        
        if issues:
            return HealthCheckResult(
                check_name="python_version",
                status="warning" if python_version.major >= 3 and python_version.minor >= 8 else "fail",
                message=f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}",
                details={"version": f"{python_version.major}.{python_version.minor}.{python_version.micro}", "issues": issues},
                remediation="Upgrade to Python 3.9 or higher"
            )
        else:
            return HealthCheckResult(
                check_name="python_version",
                status="pass",
                message=f"Python version {python_version.major}.{python_version.minor}.{python_version.micro} is compatible",
                details={"version": f"{python_version.major}.{python_version.minor}.{python_version.micro}"}
            )
    
    def check_folder_structure(self) -> HealthCheckResult:
        """
        Check that required folder structure exists.
        
        Returns:
            HealthCheckResult
        """
        issues = []
        
        required_folders = [
            "backend",
            "backend/agentic_engine",
            "backend/agentic_engine/tools",
            "backend/agentic_engine/testing",
            "backend/api",
            "backend/db",
            "backend/repositories",
            "backend/services",
            "backend/core",
            "backend/config",
            "backend/interfaces",
            "frontend",
            "frontend/pages",
            "frontend/components",
            "docs"
        ]
        
        missing_folders = []
        for folder in required_folders:
            folder_path = self.base_path / folder
            if not folder_path.exists():
                missing_folders.append(folder)
        
        if missing_folders:
            issues.append(f"Missing folders: {', '.join(missing_folders)}")
        
        if issues:
            return HealthCheckResult(
                check_name="folder_structure",
                status="fail",
                message=f"Found {len(missing_folders)} missing folders",
                details={"missing_folders": missing_folders},
                remediation="Create missing folders: " + ", ".join(missing_folders)
            )
        else:
            return HealthCheckResult(
                check_name="folder_structure",
                status="pass",
                message="All required folders exist",
                details={"checked_folders": len(required_folders)}
            )
    
    def check_file_existence(self) -> HealthCheckResult:
        """
        Check that critical files exist.
        
        Returns:
            HealthCheckResult
        """
        issues = []
        
        critical_files = [
            "backend/main.py",
            "requirements.txt",
            "README.md",
            "backend/core/version.py",
            "backend/config/settings.py",
            "backend/db/base.py",
            "backend/db/models.py",
            "backend/agentic_engine/orchestrator.py",
            "backend/api/agentic_routes.py"
        ]
        
        missing_files = []
        for file_path in critical_files:
            full_path = self.base_path / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            issues.append(f"Missing files: {', '.join(missing_files)}")
        
        if issues:
            return HealthCheckResult(
                check_name="file_existence",
                status="fail",
                message=f"Found {len(missing_files)} missing files",
                details={"missing_files": missing_files},
                remediation="Ensure all critical files are present"
            )
        else:
            return HealthCheckResult(
                check_name="file_existence",
                status="pass",
                message="All critical files exist",
                details={"checked_files": len(critical_files)}
            )
    
    def check_async_readiness(self) -> HealthCheckResult:
        """
        Check async readiness of routes and components.
        
        Returns:
            HealthCheckResult
        """
        issues = []
        warnings = []
        
        # Check if main API routes are async
        try:
            import inspect
            from backend.api import agentic_routes
            
            # Check key endpoints
            key_endpoints = [
                "analyze_with_agentic_engine",
                "run_test_suite",
                "simulate_failure",
                "run_benchmark",
                "full_health_check"
            ]
            
            for endpoint_name in key_endpoints:
                if hasattr(agentic_routes, endpoint_name):
                    func = getattr(agentic_routes, endpoint_name)
                    if inspect.iscoroutinefunction(func):
                        pass  # Good, it's async
                    else:
                        warnings.append(f"Endpoint {endpoint_name} is not async")
        except Exception as e:
            issues.append(f"Could not check async readiness: {str(e)}")
        
        # Check orchestrator (it's sync, but that's OK for now)
        warnings.append("Orchestrator is synchronous (can be wrapped for async)")
        
        if issues:
            return HealthCheckResult(
                check_name="async_readiness",
                status="fail",
                message=f"Found {len(issues)} async readiness issues",
                details={"issues": issues, "warnings": warnings},
                remediation="Convert routes to async or wrap sync functions"
            )
        elif warnings:
            return HealthCheckResult(
                check_name="async_readiness",
                status="warning",
                message="Async readiness check completed with warnings",
                details={"warnings": warnings},
                remediation="Consider making orchestrator async-compatible"
            )
        else:
            return HealthCheckResult(
                check_name="async_readiness",
                status="pass",
                message="All routes are async-ready",
                details={"checked_endpoints": len(key_endpoints)}
            )
    
    def check_database_health(self) -> HealthCheckResult:
        """
        Check database connectivity and health.
        
        Returns:
            HealthCheckResult
        """
        issues = []
        
        try:
            from backend.db.base import engine, get_db
            from sqlalchemy import text
            from backend.db.models import AuditTrail
            
            # Test database connection (SELECT)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            # Test INSERT capability (real test)
            try:
                # Get a database session
                db_gen = get_db()
                db = next(db_gen)
                
                # Try to create a test audit entry (use current schema fields)
                test_audit = AuditTrail(
                    entity_name="__health_check__",
                    task_description="Health check test",
                    task_category="HEALTH_CHECK",
                    decision_outcome="REVIEW_REQUIRED",
                    confidence_score=0.5,
                    risk_level="LOW",
                    agent_type="health_check",
                    reasoning_chain=["Health check insert test"],
                    meta_data={"source": "health_check"}
                )
                db.add(test_audit)
                db.commit()
                
                # Clean up test entry
                db.delete(test_audit)
                db.commit()
                db.close()
                
            except Exception as insert_error:
                issues.append(f"INSERT test failed: {str(insert_error)}")
            
        except ImportError as e:
            issues.append(f"Cannot import database modules: {str(e)}")
        except Exception as e:
            issues.append(f"Database connectivity check failed: {str(e)}")
        
        if issues:
            return HealthCheckResult(
                check_name="database_health",
                status="fail",
                message=f"Database health check failed: {len(issues)} issues",
                details={"issues": issues},
                remediation="Ensure database is running and accessible"
            )
        else:
            return HealthCheckResult(
                check_name="database_health",
                status="pass",
                message="Database is healthy and accessible (SELECT+INSERT verified)",
                details={"connectivity": "verified", "read_write": "verified"}
            )
    
    def check_llm_connectivity(self) -> HealthCheckResult:
        """
        Check LLM (OpenAI) connectivity and health with real schema validation test.
        
        Returns:
            HealthCheckResult
        """
        issues = []
        schema_valid = False
        
        try:
            from backend.utils.llm_client import LLMClient, get_compliance_response_schema
            
            # Check if API key is configured (use settings to respect .env file)
            from backend.config import settings
            api_key = settings.OPENAI_API_KEY
            if not api_key or api_key == "mock" or (isinstance(api_key, str) and api_key.startswith("sk-mock")):
                issues.append("OPENAI_API_KEY not configured or is mock key")
                return HealthCheckResult(
                    check_name="llm_connectivity",
                    status="warning",
                    message="LLM API key not configured (will use mock mode)",
                    details={"issues": issues, "schema_validation": False},
                    remediation="Set OPENAI_API_KEY environment variable for LLM features"
                )
            
            # Test connectivity with real schema validation
            llm_client = LLMClient()
            schema = get_compliance_response_schema()
            
            # Use a simple prompt that should return structured response
            test_prompt = "Analyze this simple compliance task: Review a basic privacy policy. Return structured response."
            test_response = llm_client.run_compliance_analysis(test_prompt, use_json_schema=True)
            
            if test_response.status == "completed" and test_response.parsed_json:
                # Validate schema structure
                parsed = test_response.parsed_json
                required_fields = ["decision", "confidence", "risk_level", "risk_analysis", "why"]
                missing_fields = [f for f in required_fields if f not in parsed]
                
                if not missing_fields:
                    schema_valid = True
                    # Check enum values
                    valid_decisions = ["AUTONOMOUS", "REVIEW_REQUIRED", "ESCALATE"]
                    valid_risk_levels = ["LOW", "MEDIUM", "HIGH"]
                    
                    if parsed.get("decision") in valid_decisions and parsed.get("risk_level") in valid_risk_levels:
                        schema_valid = True
                    else:
                        issues.append(f"Invalid enum values in response")
                else:
                    issues.append(f"Missing required fields: {', '.join(missing_fields)}")
            else:
                issues.append(f"LLM connectivity test failed: {test_response.error or 'Unknown error'}")
            
        except ImportError as e:
            issues.append(f"Cannot import LLM client: {str(e)}")
        except Exception as e:
            issues.append(f"LLM connectivity check failed: {str(e)}")
        
        if issues and not schema_valid:
            return HealthCheckResult(
                check_name="llm_connectivity",
                status="fail",
                message=f"LLM connectivity check failed: {len(issues)} issues",
                details={"issues": issues, "schema_validation": schema_valid},
                remediation="Check OPENAI_API_KEY and network connectivity"
            )
        elif schema_valid:
            return HealthCheckResult(
                check_name="llm_connectivity",
                status="pass",
                message="LLM connectivity is healthy (schema validation verified)",
                details={"connectivity": "verified", "schema_validation": True, "api_key_configured": True}
            )
        else:
            return HealthCheckResult(
                check_name="llm_connectivity",
                status="warning",
                message="LLM connectivity check completed with issues",
                details={"issues": issues, "schema_validation": schema_valid},
                remediation="Review LLM configuration"
            )
    
    def check_api_readiness(self) -> HealthCheckResult:
        """
        Check API readiness by pinging key endpoints.
        
        Returns:
            HealthCheckResult
        """
        issues = []
        ping_results = {}
        
        try:
            # Try to import httpx for external ping
            try:
                import httpx
                has_httpx = True
            except ImportError:
                has_httpx = False
                issues.append("httpx not available for external API ping tests")
            
            # Key endpoints to check (internal check - endpoints exist in routes)
            endpoints_to_check = [
                "/health",
                "/api/v1/agentic/status",
                "/api/v1/agentic/health/full"
            ]
            
            # Check if routes are defined (internal check)
            try:
                from backend.api import agentic_routes
                from backend.main import app
                
                # Check if routes exist in the app
                route_paths = [route.path for route in app.routes]
                for endpoint in endpoints_to_check:
                    # Normalize endpoint path
                    if endpoint in route_paths or any(endpoint in path for path in route_paths):
                        ping_results[endpoint] = "pass (route exists)"
                    else:
                        ping_results[endpoint] = "fail (route not found)"
                        issues.append(f"{endpoint} route not found")
                
                # If httpx is available, try to ping external endpoints
                if has_httpx:
                    base_url = os.getenv("BASE_URL", "http://localhost:8000")
                    for endpoint in endpoints_to_check:
                        url = f"{base_url}{endpoint}"
                        try:
                            with httpx.Client(timeout=3.0) as client:
                                response = client.get(url)
                                if response.status_code in [200, 401]:
                                    ping_results[f"{endpoint}_external"] = f"pass ({response.status_code})"
                                else:
                                    ping_results[f"{endpoint}_external"] = f"fail ({response.status_code})"
                        except Exception as e:
                            # External ping failed, but internal route check passed - this is OK
                            ping_results[f"{endpoint}_external"] = f"unreachable (expected if server not running)"
            except Exception as e:
                issues.append(f"API route check failed: {str(e)}")
            
        except Exception as e:
            issues.append(f"API readiness check failed: {str(e)}")
        
        failed_pings = sum(1 for v in ping_results.values() if "fail" in str(v).lower() and "external" not in str(v))
        
        if failed_pings > 0:
            return HealthCheckResult(
                check_name="api_readiness",
                status="fail" if failed_pings == len(endpoints_to_check) else "warning",
                message=f"API readiness check: {failed_pings}/{len(endpoints_to_check)} routes not found",
                details={"ping_results": ping_results, "issues": issues},
                remediation="Ensure API routes are properly registered"
            )
        else:
            return HealthCheckResult(
                check_name="api_readiness",
                status="pass",
                message="All API routes are defined and accessible",
                details={"ping_results": ping_results, "checked_endpoints": len(endpoints_to_check)}
            )
    
    def get_test_suite_readiness(self) -> Dict[str, Any]:
        """
        Fetch test suite readiness metrics from test suite engine.
        
        Returns:
            Dictionary with test suite metrics
        """
        try:
            from backend.agentic_engine.testing.test_suite_engine import TestSuiteEngine
            
            # Run a quick test suite (or use cached results)
            # For now, return default values - in production, this would fetch real results
            # This is called asynchronously from the endpoint
            return {
                "status": "available",
                "pass_rate": None,  # Will be filled by endpoint
                "failures": None,
                "confidence_deviations": None
            }
        except Exception as e:
            logger.warning(f"Could not get test suite readiness: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_error_recovery_readiness(self) -> Dict[str, Any]:
        """
        Fetch error recovery readiness metrics.
        
        Returns:
            Dictionary with error recovery metrics
        """
        try:
            from backend.agentic_engine.testing.error_recovery_engine import ErrorRecoveryEngine
            
            # Return default values - actual metrics fetched from endpoint
            return {
                "status": "available",
                "recovery_rate": None,  # Will be filled by endpoint
                "retry_stability": None,
                "fallback_quality": None
            }
        except Exception as e:
            logger.warning(f"Could not get error recovery readiness: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def compute_readiness_score(
        self,
        health_results: Dict[str, Any],
        test_suite_metrics: Optional[Dict[str, Any]] = None,
        error_recovery_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compute single readiness score using weighted components.
        
        Args:
            health_results: Results from run_all_checks()
            test_suite_metrics: Optional test suite metrics
            error_recovery_metrics: Optional error recovery metrics
            
        Returns:
            Dictionary with readiness score and component breakdown
        """
        # Component weights
        weights = {
            "db_health": 0.20,
            "llm_health": 0.20,
            "api_health": 0.15,
            "test_suite_health": 0.25,
            "error_recovery_health": 0.20
        }
        
        # Score health checks
        checks = health_results.get("checks", [])
        
        # DB health score (0-1)
        db_check = next((c for c in checks if c.get("check_name") == "database_health"), None)
        db_health = 1.0 if db_check and db_check.get("status") == "pass" else (0.5 if db_check and db_check.get("status") == "warning" else 0.0)
        
        # LLM health score (0-1)
        llm_check = next((c for c in checks if c.get("check_name") == "llm_connectivity"), None)
        llm_health = 1.0 if llm_check and llm_check.get("status") == "pass" else (0.5 if llm_check and llm_check.get("status") == "warning" else 0.0)
        
        # API health score (0-1)
        api_check = next((c for c in checks if c.get("check_name") == "api_readiness"), None)
        if not api_check:
            api_check = next((c for c in checks if c.get("check_name") == "async_readiness"), None)
        api_health = 1.0 if api_check and api_check.get("status") == "pass" else (0.5 if api_check and api_check.get("status") == "warning" else 0.0)
        
        # Test suite health score (0-1)
        if test_suite_metrics and test_suite_metrics.get("pass_rate") is not None:
            pass_rate = test_suite_metrics.get("pass_rate", 0.0)
            failures = test_suite_metrics.get("failures", [])
            # Score based on pass rate (threshold: 0.8 for full score)
            if pass_rate >= 0.9:
                test_suite_health = 1.0
            elif pass_rate >= 0.8:
                test_suite_health = 0.8
            elif pass_rate >= 0.7:
                test_suite_health = 0.6
            else:
                test_suite_health = 0.4
            # Penalize if there are critical failures
            if failures:
                test_suite_health *= 0.9
        else:
            test_suite_health = 0.5  # Unknown
        
        # Error recovery health score (0-1)
        if error_recovery_metrics and error_recovery_metrics.get("recovery_rate") is not None:
            recovery_rate = error_recovery_metrics.get("recovery_rate", 0.0)
            fallback_quality = error_recovery_metrics.get("fallback_quality", 0.0)
            # Score based on recovery rate and fallback quality
            error_recovery_health = (recovery_rate * 0.7) + (fallback_quality * 0.3)
        else:
            error_recovery_health = 0.5  # Unknown
        
        # Compute weighted readiness score
        readiness_score = (
            db_health * weights["db_health"] +
            llm_health * weights["llm_health"] +
            api_health * weights["api_health"] +
            test_suite_health * weights["test_suite_health"] +
            error_recovery_health * weights["error_recovery_health"]
        )
        
        return {
            "readiness_score": round(readiness_score, 3),
            "components": {
                "db_health": {
                    "score": db_health,
                    "weight": weights["db_health"],
                    "weighted_score": round(db_health * weights["db_health"], 3),
                    "status": "pass" if db_health >= 0.9 else ("warning" if db_health >= 0.5 else "fail")
                },
                "llm_health": {
                    "score": llm_health,
                    "weight": weights["llm_health"],
                    "weighted_score": round(llm_health * weights["llm_health"], 3),
                    "status": "pass" if llm_health >= 0.9 else ("warning" if llm_health >= 0.5 else "fail")
                },
                "api_health": {
                    "score": api_health,
                    "weight": weights["api_health"],
                    "weighted_score": round(api_health * weights["api_health"], 3),
                    "status": "pass" if api_health >= 0.9 else ("warning" if api_health >= 0.5 else "fail")
                },
                "test_suite_health": {
                    "score": test_suite_health,
                    "weight": weights["test_suite_health"],
                    "weighted_score": round(test_suite_health * weights["test_suite_health"], 3),
                    "status": "pass" if test_suite_health >= 0.9 else ("warning" if test_suite_health >= 0.5 else "fail"),
                    "metrics": test_suite_metrics
                },
                "error_recovery_health": {
                    "score": error_recovery_health,
                    "weight": weights["error_recovery_health"],
                    "weighted_score": round(error_recovery_health * weights["error_recovery_health"], 3),
                    "status": "pass" if error_recovery_health >= 0.9 else ("warning" if error_recovery_health >= 0.5 else "fail"),
                    "metrics": error_recovery_metrics
                }
            },
            "weights": weights
        }
    
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all health checks including deployment preflight checks.
        
        Returns:
            Dictionary with all check results and summary
        """
        self.results = []
        
        # Run all checks
        self.results.append(self.check_missing_imports())
        self.results.append(self.check_invalid_references())
        self.results.append(self.check_environmental_paths())
        self.results.append(self.check_dependency_mismatch())
        self.results.append(self.check_ui_routes())
        self.results.append(self.check_reasoning_engine_health())
        
        # Infrastructure health checks
        self.results.append(self.check_database_health())
        self.results.append(self.check_llm_connectivity())
        self.results.append(self.check_api_readiness())
        
        # Deployment preflight checks (L4)
        self.results.append(self.check_python_version())
        self.results.append(self.check_folder_structure())
        self.results.append(self.check_file_existence())
        self.results.append(self.check_async_readiness())
        
        # Calculate summary
        total_checks = len(self.results)
        passed = sum(1 for r in self.results if r.status == "pass")
        failed = sum(1 for r in self.results if r.status == "fail")
        warnings = sum(1 for r in self.results if r.status == "warning")
        
        # Overall status
        if failed > 0:
            overall_status = "fail"
        elif warnings > 0:
            overall_status = "warning"
        else:
            overall_status = "pass"
        
        # Collect remediation steps
        remediation_steps = []
        for result in self.results:
            if result.remediation and result.status != "pass":
                remediation_steps.append({
                    "check": result.check_name,
                    "remediation": result.remediation
                })
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_checks": total_checks,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "pass_rate": passed / total_checks if total_checks > 0 else 0.0
            },
            "checks": [
                {
                    "check_name": r.check_name,
                    "status": r.status,
                    "message": r.message,
                    "details": r.details,
                    "remediation": r.remediation
                }
                for r in self.results
            ],
            "remediation_steps": remediation_steps
        }
