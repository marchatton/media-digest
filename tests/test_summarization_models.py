"""Tests for summarization models and validation."""

import pytest
from pydantic import ValidationError

from src.summarize.models import (
    Company,
    EpisodeOverview,
    KeyTopic,
    MemorableMoment,
    NotableInsight,
    SummaryResponse,
    Takeaway,
    Tool,
)


@pytest.fixture()
def sample_response_payload() -> dict:
    return {
        "episode_overview": {
            "podcast_name": "AI Today",
            "episode_title": "Scaling AI Teams",
            "duration": "01:02:11",
            "theme": "How companies scale applied AI initiatives",
            "hook": "Leaders share pragmatic playbooks for scaling applied AI teams.",
        },
        "key_topics": [
            {
                "topic": "Why applied AI teams stall",
                "summary": "Leaders unpack the technical and organizational debt that builds up when pilot projects linger without buy-in.",
                "timestamp": "05:42",
            },
            {
                "topic": "Hiring the second wave of ML engineers",
                "summary": "Concrete tactics for sourcing engineers with product intuition and pairing them with domain experts.",
                "timestamp": "24:10",
            },
            {
                "topic": "Post-launch instrumentation",
                "summary": "Designing guardrails and alerting so models fail gracefully and teams can iterate quickly.",
                "timestamp": "44:55",
            },
        ],
        "notable_insights": [
            {
                "idea": "We promote product managers who can explain model trade-offs in customer language.",
                "attribution": "Emily",
                "timestamp": "11:03",
            },
            {
                "idea": "Metrics only matter when they change incentives—not when they decorate dashboards.",
                "attribution": "Grace",
                "timestamp": "33:27",
            },
        ],
        "takeaways": [
            {"text": "Pair every pilot with a business owner accountable for a hard metric."},
            {"text": "Instrument model health with the same rigor as uptime."},
        ],
        "memorable_moments": [
            {
                "description": "Live teardown of an email-and-spreadsheet workflow replaced by a retrieval-augmented agent.",
                "timestamp": "52:18",
            }
        ],
        "tools": [
            {"name": "Evidently AI", "context": "Used for continuous monitoring of distribution shift."}
        ],
        "companies": [
            {"name": "Scale.ai", "context": "Case study on vendor partnerships."}
        ],
        "summary_one_sentence": "Leaders share the gritty work of scaling applied AI teams, from hiring to monitoring production models.",
        "wildcard": "Panel kept an optimistic but realistic tone about regulation in 2026.",
    }


def test_summary_response_valid(sample_response_payload):
    response = SummaryResponse(**sample_response_payload)
    assert response.episode_overview.hook.startswith("Leaders share")
    assert len(response.key_topics) == 3
    assert response.tools[0].name == "Evidently AI"


def test_summary_response_requires_topics(sample_response_payload):
    sample_response_payload["key_topics"] = []
    with pytest.raises(ValidationError):
        SummaryResponse(**sample_response_payload)


def test_episode_overview_requires_theme():
    with pytest.raises(ValidationError):
        EpisodeOverview(
            podcast_name=None,
            episode_title="Demo",
            duration="45:00",
            hook="A hook without theme",
        )


def test_key_topic_structure():
    topic = KeyTopic(topic="Deployment", summary="How they shipped", timestamp=None)
    assert topic.timestamp is None


def test_notable_insight_requires_idea():
    with pytest.raises(ValidationError):
        NotableInsight(idea="", attribution=None)


def test_memorable_moment_optional_timestamp():
    moment = MemorableMoment(description="Audience Q&A", timestamp=None)
    assert moment.description == "Audience Q&A"


def test_takeaway_holds_text():
    takeaway = Takeaway(text="Document decision logs.")
    assert "Document" in takeaway.text


def test_company_and_tool_models():
    company = Company(name="Anthropic", context="Model provider")
    tool = Tool(name="Weights & Biases", context="Experiment tracking")
    assert company.name == "Anthropic"
    assert "tracking" in tool.context
