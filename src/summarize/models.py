"""Structured output models for LLM responses."""

from pydantic import BaseModel, Field


class Company(BaseModel):
    """Company mention."""

    name: str
    context: str


class Tool(BaseModel):
    """Tool/product mention."""

    name: str
    context: str


class Quote(BaseModel):
    """Noteworthy quote."""

    text: str
    timestamp: str  # "12:34" or "section name"


class SummaryResponse(BaseModel):
    """LLM summary response."""

    summary: str = Field(..., min_length=1, description="2-3 sentence summary")
    key_topics: list[str] = Field(..., min_length=1, description="3-5 key topics")
    companies: list[Company] = Field(default_factory=list, description="Companies mentioned")
    tools: list[Tool] = Field(default_factory=list, description="Tools/products mentioned")
    quotes: list[Quote] = Field(..., min_length=1, description="2-4 noteworthy quotes")


class RatingResponse(BaseModel):
    """LLM rating response."""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    rationale: str = Field(..., description="One sentence explaining the rating")
