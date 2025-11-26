"""
Backend utilities
"""

from .llm_client import (
    LLMClient,
    LLMResponse,
    run_compliance_analysis,
    run_compliance_analysis_async,
    get_llm_client,
    # Legacy functions for backward compatibility
    call_llm_async,
    call_llm_sync
)

__all__ = ["LLMClient", "call_llm_async", "call_llm_sync"]

