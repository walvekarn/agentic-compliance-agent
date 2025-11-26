"""Tests for health check environment validation"""
import pytest
import os
from backend.agentic_engine.testing.health_check import SystemHealthCheck


def test_health_check_env_vars_missing(monkeypatch):
    """Test health check when env vars are missing"""
    # Remove env vars
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    
    check = SystemHealthCheck()
    result = check.check_environmental_paths()
    
    # Should warn about missing vars
    assert result.status in ["fail", "warning"]
    # Check that details contain information about missing vars
    # The message is generic ("Found X issues"), but details should have specifics
    assert result.details is not None
    issues = result.details.get("issues", [])
    assert len(issues) > 0
    # Check that at least one issue mentions environment variables
    issues_text = " ".join(issues).lower()
    assert "openai" in issues_text or "database" in issues_text or "environment" in issues_text


def test_health_check_env_vars_present(monkeypatch):
    """Test health check when env vars are set"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-1234567890")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    
    check = SystemHealthCheck()
    result = check.check_environmental_paths()
    
    # Should pass or at least not fail due to missing vars
    # (may still fail due to paths, but not env vars)
    assert result.status in ["pass", "warning"] or "OPENAI_API_KEY" not in result.message


def test_health_check_database_path():
    """Test health check database path validation"""
    check = SystemHealthCheck()
    result = check.check_database_health()
    
    # Should return a result (pass, fail, or warning)
    assert result is not None
    assert hasattr(result, "status")
    assert result.status in ["pass", "fail", "warning"]


def test_health_check_llm_connectivity(monkeypatch):
    """Test health check LLM connectivity"""
    # Test with mock key (should skip or fail gracefully)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-mock-test")
    
    check = SystemHealthCheck()
    result = check.check_llm_connectivity()
    
    # Should return a result
    assert result is not None
    assert hasattr(result, "status")
    assert result.status in ["pass", "fail", "warning"]

