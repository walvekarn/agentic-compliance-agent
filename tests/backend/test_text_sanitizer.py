"""Tests for text sanitization utility"""
import pytest
from backend.utils.text_sanitizer import sanitize_user_text


def test_sanitize_user_text_basic():
    """Test basic sanitization"""
    assert sanitize_user_text("Hello World") == "Hello World"
    assert sanitize_user_text("") == ""
    assert sanitize_user_text(None) == ""


def test_sanitize_user_text_control_chars():
    """Test control character removal"""
    text_with_control = "Hello\x00World\x08Test"
    result = sanitize_user_text(text_with_control)
    assert "\x00" not in result
    assert "\x08" not in result
    assert "Hello" in result
    assert "World" in result
    assert "Test" in result


def test_sanitize_user_text_length_limit():
    """Test length truncation"""
    long_text = "A" * 3000
    result = sanitize_user_text(long_text, max_length=2000)
    assert len(result) == 2000
    assert result == "A" * 2000


def test_sanitize_user_text_whitespace():
    """Test whitespace handling"""
    assert sanitize_user_text("  Hello  World  ") == "Hello  World"
    assert sanitize_user_text("\t\nHello\n\t") == "Hello"


def test_sanitize_user_text_special_chars():
    """Test that normal special characters are preserved"""
    text = "Hello! How are you? (I'm fine.)"
    result = sanitize_user_text(text)
    assert result == text


def test_sanitize_user_text_empty_after_sanitization():
    """Test that empty strings after sanitization return empty"""
    # String with only control chars
    result = sanitize_user_text("\x00\x01\x02")
    assert result == "" or result.strip() == ""

