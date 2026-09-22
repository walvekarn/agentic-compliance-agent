"""Tests for the OpenAI-backed ComplianceAgent (backend.agent.openai_agent).

The agent delegates every model call to backend.utils.llm_client.LLMClient, so
these tests patch the client's call_sync / call_async methods and never reach
the network.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from backend.agent.openai_agent import ComplianceAgent


COMPLETED = {"status": "completed", "raw_text": "This is a test response", "parsed_json": None}


def make_agent(model: str = "gpt-4o-mini") -> ComplianceAgent:
    return ComplianceAgent(api_key="test_api_key", model=model)


def test_agent_initialization():
    """The agent stores the key it was given and builds an LLM client.

    The model attribute is resolved through settings.OPENAI_MODEL when that
    setting exists and otherwise falls back to None; the effective model name
    ("gpt-4o-mini") is asserted on the query results below.
    """
    agent = make_agent()
    assert agent.api_key == "test_api_key"
    assert agent.llm_client is not None
    assert agent.model in (None, "gpt-4o-mini")


def test_process_query_sync():
    """Synchronous query processing returns the client's text with success status."""
    agent = make_agent()
    agent.llm_client.call_sync = Mock(return_value=COMPLETED)

    result = agent.process_query_sync("What is GDPR?")

    assert result["status"] == "success"
    assert result["response"] == "This is a test response"
    assert result["model"] == "gpt-4o-mini"
    agent.llm_client.call_sync.assert_called_once()


@pytest.mark.asyncio
async def test_process_query_async():
    """Asynchronous query processing returns the client's text with success status."""
    agent = make_agent()
    agent.llm_client.call_async = AsyncMock(return_value=COMPLETED)

    result = await agent.process_query("What is HIPAA?")

    assert result["status"] == "success"
    assert result["response"] == "This is a test response"
    assert result["model"] == "gpt-4o-mini"
    agent.llm_client.call_async.assert_awaited_once()


def test_process_query_sync_reports_llm_error():
    """A failed client call is surfaced as an error result, not an exception."""
    agent = make_agent()
    agent.llm_client.call_sync = Mock(return_value={"status": "error", "error": "upstream failure"})

    result = agent.process_query_sync("What is SOX?")

    assert result["status"] == "error"
    assert result["error"] == "upstream failure"
    assert result["model"] == "gpt-4o-mini"


def test_estimate_confidence_thresholds():
    """Confidence is a length heuristic with four fixed bands."""
    agent = make_agent()
    assert agent._estimate_confidence("short") == 0.4
    assert agent._estimate_confidence("x" * 100) == 0.6
    assert agent._estimate_confidence("x" * 300) == 0.75
    assert agent._estimate_confidence("x" * 600) == 0.85
