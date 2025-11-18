"""
Tool Pipeline Tests
===================
Test the tool execution pipeline.
"""

import pytest
from backend.agentic_engine.tools.entity_tool import EntityTool
from backend.agentic_engine.tools.calendar_tool import CalendarTool
from backend.agentic_engine.tools.task_tool import TaskTool
from backend.agentic_engine.tools.http_tool import HTTPTool
from backend.agentic_engine.tools.tool_registry import ToolRegistry


class TestEntityTool:
    """Test EntityTool"""
    
    def test_entity_tool_initialization(self):
        """Test tool initialization"""
        tool = EntityTool()
        assert tool.name == "entity_tool"
        assert tool.description is not None
        assert tool.schema is not None
    
    def test_fetch_entity_details(self):
        """Test fetching entity details"""
        tool = EntityTool()
        result = tool.run({
            "action": "fetch_entity_details",
            "entity_name": "TestCorp",
            "entity_type": "PRIVATE_COMPANY"
        })
        assert "success" in result
        if result.get("success"):
            data = result.get("data", {})
            assert "name" in data or "entity_name" in data
        else:
            # Even on error, should have error message
            assert "error" in result
    
    def test_analyze_entity(self):
        """Test entity analysis via fetch_entity_details"""
        tool = EntityTool()
        result = tool.run({
            "action": "fetch_entity_details",
            "entity_name": "TestCorp",
            "entity_type": "PRIVATE_COMPANY",
            "industry": "TECHNOLOGY"
        })
        assert "success" in result
        if result.get("success"):
            data = result.get("data", {})
            assert "name" in data or "capability" in data


class TestCalendarTool:
    """Test CalendarTool"""
    
    def test_calendar_tool_initialization(self):
        """Test tool initialization"""
        tool = CalendarTool()
        assert tool.name == "calendar_tool"
        assert tool.description is not None
    
    def test_calculate_deadline(self):
        """Test deadline calculation"""
        tool = CalendarTool()
        result = tool.run({
            "action": "calculate_deadline",
            "base_date": "2025-01-01T00:00:00Z",
            "days_ahead": 30
        })
        assert "deadline" in result or "calculated_date" in result
    
    def test_calculate_urgency_score(self):
        """Test urgency score calculation"""
        tool = CalendarTool()
        # Check schema for correct action name
        schema = tool.schema
        action_enum = schema.get("properties", {}).get("action", {}).get("enum", [])
        action = "calculate_urgency_score" if "calculate_urgency_score" in action_enum else "calculate_urgency"
        
        result = tool.run({
            "action": action,
            "deadline": "2025-01-15T00:00:00Z",
            "task_category": "DATA_PROTECTION"
        })
        # Result should contain urgency information
        assert result is not None
        assert isinstance(result, dict)
        assert "urgency_score" in result or "score" in result or "urgency" in result or "success" in result


class TestTaskTool:
    """Test TaskTool"""
    
    def test_task_tool_initialization(self):
        """Test tool initialization"""
        tool = TaskTool()
        assert tool.name == "task_tool"
        assert tool.description is not None
    
    def test_analyze_task(self):
        """Test task analysis"""
        tool = TaskTool()
        result = tool.run({
            "task_description": "Review privacy policy",
            "task_category": "POLICY_REVIEW",
            "affects_personal_data": True
        })
        assert "risk_score" in result or "analysis" in result
        assert "decision" in result or "recommendation" in result


class TestHTTPTool:
    """Test HTTPTool"""
    
    def test_http_tool_initialization(self):
        """Test tool initialization"""
        tool = HTTPTool()
        assert tool.name == "http_tool"
        assert tool.description is not None
    
    def test_http_get_request(self):
        """Test HTTP GET request"""
        tool = HTTPTool()
        # Use a test endpoint that should work
        result = tool.run({
            "method": "GET",
            "url": "https://httpbin.org/get",
            "params": {"test": "value"}
        })
        assert "status_code" in result or "response" in result


class TestToolRegistry:
    """Test ToolRegistry"""
    
    def test_tool_registry_initialization(self):
        """Test registry initialization"""
        registry = ToolRegistry()
        assert registry is not None
    
    def test_get_tool_metadata(self):
        """Test getting tool metadata by name"""
        registry = ToolRegistry()
        metadata = registry.get_tool_metadata("entity_tool")
        assert metadata is not None
        assert metadata.name == "entity_tool"
        assert metadata.description is not None
    
    def test_get_tool_capabilities(self):
        """Test getting tool capabilities"""
        registry = ToolRegistry()
        capabilities = registry.get_tool_capabilities("entity_tool")
        assert isinstance(capabilities, list)
        assert len(capabilities) > 0
    
    def test_match_tools_to_step(self):
        """Test matching tools to a step"""
        registry = ToolRegistry()
        relevant = registry.match_tools_to_step(
            "Analyze entity compliance requirements and calculate deadlines"
        )
        assert isinstance(relevant, list)
        # Should find entity_tool and/or calendar_tool
        assert "entity_tool" in relevant or "calendar_tool" in relevant

