"""Tests for the Claude agent"""

import pytest
from unittest.mock import Mock, patch
from backend.agent.openai_agent import ComplianceAgent


@pytest.fixture
def mock_openai_api_key(monkeypatch):
    """Mock the OpenAI API key"""
    monkeypatch.setenv("OPENAI_API_KEY", "test_api_key")


def test_agent_initialization(mock_openai_api_key):
    """Test that the agent initializes correctly"""
    agent = ComplianceAgent()
    assert agent.api_key == "test_api_key"
    assert agent.model == "gpt-4o-mini"
    assert agent.llm is not None


def test_agent_with_custom_model(mock_openai_api_key):
    """Test agent initialization with custom model"""
    custom_model = "gpt-4"
    agent = ComplianceAgent(model=custom_model)
    assert agent.model == custom_model


@patch('src.agent.openai_agent.ChatOpenAI')
def test_process_query_sync(mock_chat, mock_openai_api_key):
    """Test synchronous query processing"""
    # Mock the response
    mock_response = Mock()
    mock_response.content = "This is a test response"
    mock_chat.return_value.invoke.return_value = mock_response
    
    agent = ComplianceAgent()
    result = agent.process_query_sync("What is GDPR?")
    
    assert result["status"] == "success"
    assert "response" in result
    assert result["model"] is not None


@pytest.mark.asyncio
@patch('src.agent.openai_agent.ChatOpenAI')
async def test_process_query_async(mock_chat, mock_openai_api_key):
    """Test asynchronous query processing"""
    # Mock the response
    mock_response = Mock()
    mock_response.content = "This is a test async response"
    
    # Create an async mock
    async def mock_ainvoke(query):
        return mock_response
    
    mock_chat.return_value.ainvoke = mock_ainvoke
    
    agent = ComplianceAgent()
    result = await agent.process_query("What is HIPAA?")
    
    assert result["status"] == "success"
    assert "response" in result
    assert result["model"] is not None


def test_llm_configuration(mock_openai_api_key):
    """Test that LLM is configured correctly"""
    agent = ComplianceAgent()
    
    assert agent.llm is not None
    assert agent.llm.model_name == "gpt-4o-mini"

