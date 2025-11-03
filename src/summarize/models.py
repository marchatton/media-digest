"""Structured output models for LLM responses."""

from typing import Optional

from pydantic import BaseModel, Field


class Company(BaseModel):
    """Company mention."""

    name: str
    context: str


class Tool(BaseModel):
    """Tool/product mention."""

    name: str
    context: str


class EpisodeOverview(BaseModel):
    """High-level episode context."""

    podcast_name: Optional[str] = Field(None, description="Podcast name if mentioned")
    episode_title: Optional[str] = Field(None, description="Episode title copy if provided")
    duration: Optional[str] = Field(None, description="Episode runtime")
    theme: str = Field(..., description="General theme of the conversation")
    hook: str = Field(..., description="One-sentence hook describing listener value")


class KeyTopic(BaseModel):
    """Topic discussed in the episode."""

    topic: str = Field(..., description="Topic headline")
    summary: str = Field(..., description="2-4 sentence description for the segment")
    timestamp: Optional[str] = Field(None, description="Relevant timestamp")


class NotableInsight(BaseModel):
    """Important idea, lesson, or quote."""

    idea: str = Field(..., min_length=1, description="Insight text or quote")
    attribution: Optional[str] = Field(None, description="Speaker attribution")
    timestamp: Optional[str] = Field(None, description="Timestamp for the insight")


class Takeaway(BaseModel):
    """Actionable lesson."""

    text: str


class MemorableMoment(BaseModel):
    """Standout episode moment."""

    description: str
    timestamp: Optional[str] = None


class SummaryResponse(BaseModel):
    """Structured podcast summary response."""

    episode_overview: EpisodeOverview
    key_topics: list[KeyTopic] = Field(..., min_length=1, max_length=6)
    notable_insights: list[NotableInsight] = Field(..., min_length=1, max_length=6)
    takeaways: list[Takeaway] = Field(default_factory=list)
    memorable_moments: list[MemorableMoment] = Field(default_factory=list)
    tools: list[Tool] = Field(default_factory=list)
    companies: list[Company] = Field(default_factory=list)
    summary_one_sentence: str = Field(..., min_length=1)
    wildcard: Optional[str] = None


class RatingResponse(BaseModel):
    """LLM rating response."""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    rationale: str = Field(..., description="One sentence explaining the rating")
