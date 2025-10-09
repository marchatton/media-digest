"""Tests for summarization models and validation."""

import pytest
from pydantic import ValidationError
from src.summarize.models import SummaryResponse, RatingResponse, Company, Tool, Quote


def test_summary_response_valid():
    """Test valid summary response."""
    data = {
        "summary": "This is a test summary.",
        "key_topics": ["AI", "Technology", "Business"],
        "companies": [
            {"name": "OpenAI", "context": "Develops GPT models"}
        ],
        "tools": [
            {"name": "ChatGPT", "context": "AI chatbot"}
        ],
        "quotes": [
            {"text": "AI is the future", "timestamp": "12:34"}
        ]
    }

    summary = SummaryResponse(**data)
    assert summary.summary == "This is a test summary."
    assert len(summary.key_topics) == 3
    assert len(summary.companies) == 1
    assert summary.companies[0].name == "OpenAI"


def test_summary_response_missing_required():
    """Test summary response with missing required fields."""
    data = {
        "key_topics": ["AI"]
    }

    with pytest.raises(ValidationError):
        SummaryResponse(**data)


def test_summary_response_empty_lists():
    """Test summary response with empty lists."""
    data = {
        "summary": "Test",
        "key_topics": [],
        "quotes": []
    }

    with pytest.raises(ValidationError):
        SummaryResponse(**data)


def test_rating_response_valid():
    """Test valid rating response."""
    data = {
        "rating": 4,
        "rationale": "High quality content with actionable insights"
    }

    rating = RatingResponse(**data)
    assert rating.rating == 4
    assert "actionable" in rating.rationale


def test_rating_response_invalid_range():
    """Test rating response with invalid rating."""
    # Rating too high
    with pytest.raises(ValidationError):
        RatingResponse(rating=6, rationale="Test")

    # Rating too low
    with pytest.raises(ValidationError):
        RatingResponse(rating=0, rationale="Test")


def test_rating_response_missing_rationale():
    """Test rating response without rationale."""
    with pytest.raises(ValidationError):
        RatingResponse(rating=3)


def test_company_model():
    """Test Company model."""
    company = Company(name="Google", context="Search engine company")
    assert company.name == "Google"
    assert company.context == "Search engine company"


def test_tool_model():
    """Test Tool model."""
    tool = Tool(name="Cursor", context="AI-powered code editor")
    assert tool.name == "Cursor"
    assert "code editor" in tool.context


def test_quote_model():
    """Test Quote model."""
    quote = Quote(text="Testing is important", timestamp="5:30")
    assert quote.text == "Testing is important"
    assert quote.timestamp == "5:30"
