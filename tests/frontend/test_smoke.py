"""
Dashboard Smoke Tests
====================
Basic smoke tests to verify dashboard pages load without errors.
"""

import pytest
import sys
from pathlib import Path

# Add frontend to path
frontend_dir = Path(__file__).parent.parent.parent / "frontend"
sys.path.insert(0, str(frontend_dir))


class TestDashboardImports:
    """Test that dashboard modules can be imported"""
    
    def test_import_home(self):
        """Test Home page import"""
        try:
            import Home  # noqa: F401
            assert True
        except Exception as e:
            pytest.fail(f"Failed to import Home: {e}")
    
    def test_import_analyze_task(self):
        """Test Analyze Task page import"""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "analyze_task",
                frontend_dir / "pages" / "1_Analyze_Task.py"
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                assert True
            else:
                pytest.fail("Could not load Analyze Task module")
        except Exception as e:
            pytest.fail(f"Failed to import Analyze Task: {e}")
    
    def test_import_compliance_calendar(self):
        """Test Compliance Calendar page import"""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "compliance_calendar",
                frontend_dir / "pages" / "2_Compliance_Calendar.py"
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                assert True
            else:
                pytest.fail("Could not load Compliance Calendar module")
        except Exception as e:
            pytest.fail(f"Failed to import Compliance Calendar: {e}")
    
    def test_import_audit_trail(self):
        """Test Audit Trail page import"""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "audit_trail",
                frontend_dir / "pages" / "3_Audit_Trail.py"
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                assert True
            else:
                pytest.fail("Could not load Audit Trail module")
        except Exception as e:
            pytest.fail(f"Failed to import Audit Trail: {e}")
    
    def test_import_agent_insights(self):
        """Test Agent Insights page import"""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "agent_insights",
                frontend_dir / "pages" / "4_Agent_Insights.py"
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                assert True
            else:
                pytest.fail("Could not load Agent Insights module")
        except Exception as e:
            pytest.fail(f"Failed to import Agent Insights: {e}")
    
    def test_import_agentic_analysis(self):
        """Test Agentic Analysis page import"""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "agentic_analysis",
                frontend_dir / "pages" / "5_Agentic_Analysis.py"
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                assert True
            else:
                pytest.fail("Could not load Agentic Analysis module")
        except Exception as e:
            pytest.fail(f"Failed to import Agentic Analysis: {e}")


class TestDashboardComponents:
    """Test dashboard component imports"""
    
    def test_import_api_client(self):
        """Test API client import"""
        try:
            from components.api_client import APIClient  # noqa: F401
            assert True
        except Exception as e:
            pytest.fail(f"Failed to import APIClient: {e}")
    
    def test_import_auth_utils(self):
        """Test auth utils import"""
        try:
            from components.auth_utils import require_auth  # noqa: F401
            assert True
        except Exception as e:
            pytest.fail(f"Failed to import auth_utils: {e}")
    
    def test_import_constants(self):
        """Test constants import"""
        try:
            from components.constants import API_BASE_URL  # noqa: F401
            assert True
        except Exception as e:
            pytest.fail(f"Failed to import constants: {e}")


class TestAPIClient:
    """Test API client basic functionality"""
    
    def test_api_client_initialization(self):
        """Test API client can be initialized"""
        try:
            from components.api_client import APIClient
            client = APIClient()
            assert client is not None
            assert hasattr(client, 'base_url')
        except Exception as e:
            pytest.fail(f"Failed to initialize APIClient: {e}")
    
    def test_health_check_method(self):
        """Test health check method exists"""
        try:
            from components.api_client import APIClient
            client = APIClient()
            assert hasattr(client, 'health_check')
        except Exception as e:
            pytest.fail(f"Failed to check health_check method: {e}")

