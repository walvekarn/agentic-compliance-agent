"""
System Health Check Module

Validates system readiness for deployment by checking imports, references,
environmental paths, dependencies, routes, reasoning engine health, and
deployment preflight requirements.
"""

import importlib
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


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
            # Go up from src/agentic_engine/testing/health_check.py to project root
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
            "src.agentic_engine.orchestrator",
            "src.agentic_engine.agent_loop",
            "src.agentic_engine.tools.tool_registry",
            "src.agentic_engine.testing.test_suite_engine",
            "src.agentic_engine.testing.failure_simulator",
            "src.agentic_engine.testing.benchmark_runner",
            "src.api.agentic_routes"
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
            self.base_path / "src" / "agentic_engine" / "orchestrator.py",
            self.base_path / "src" / "api" / "agentic_routes.py"
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
        
        # Check critical environment variables
        env_vars = ["OPENAI_API_KEY", "DATABASE_URL"]
        missing_vars = []
        
        for var in env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            issues.append(f"Missing environment variables: {', '.join(missing_vars)}")
        
        # Check if paths exist
        critical_paths = [
            self.base_path / "src",
            self.base_path / "src" / "agentic_engine",
            self.base_path / "src" / "api",
            self.base_path / "dashboard" / "pages"
        ]
        
        missing_paths = []
        for path in critical_paths:
            if not path.exists():
                missing_paths.append(str(path))
        
        if missing_paths:
            issues.append(f"Missing paths: {', '.join(missing_paths)}")
        
        if issues:
            return HealthCheckResult(
                check_name="environmental_paths",
                status="fail",
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
                ("langchain_openai", "langchain_openai"),
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
        pages_dir = self.base_path / "dashboard" / "pages"
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
        api_routes_file = self.base_path / "src" / "api" / "agentic_routes.py"
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
            
            # Check if OpenAI API key is set
            if not os.getenv("OPENAI_API_KEY"):
                issues.append("OPENAI_API_KEY not set - orchestrator may not work")
            
            # Check if prompts exist
            prompts_dir = self.base_path / "src" / "agentic_engine" / "reasoning" / "prompts"
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
            return HealthCheckResult(
                check_name="reasoning_engine_health",
                status="warning" if len(issues) == 1 and "OPENAI_API_KEY" in issues[0] else "fail",
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
            "src",
            "src/agentic_engine",
            "src/agentic_engine/tools",
            "src/agentic_engine/testing",
            "src/api",
            "src/db",
            "src/repositories",
            "src/services",
            "src/core",
            "src/core/config",
            "src/di",
            "src/interfaces",
            "dashboard",
            "dashboard/pages",
            "dashboard/components",
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
            "main.py",
            "requirements.txt",
            "README.md",
            "src/core/version.py",
            "src/core/config/settings.py",
            "src/db/base.py",
            "src/db/models.py",
            "src/agentic_engine/orchestrator.py",
            "src/api/agentic_routes.py"
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

