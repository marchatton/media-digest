"""LLM prompts for summarization and analysis."""

# System prompts (cacheable for cost optimization)

CLEANING_SYSTEM_PROMPT = """You are a transcript editor. Your job is to clean and structure podcast transcripts for readability.

Rules:
1. Remove filler words: "um", "uh", "like" (when used as filler), "you know"
2. Remove repetitions and obvious Whisper hallucinations
3. Fix obvious transcription errors (e.g., "open AI" → "OpenAI", "GPT three" → "GPT-3")
4. Segment by topic with paragraph breaks (every 3-5 sentences or topic shift)
5. Preserve timestamps in format [HH:MM:SS] or [MM:SS]
6. Do NOT summarize or remove content - only clean
7. Keep speaker labels if present (e.g., "Speaker 1:", "Host:")

Output the cleaned transcript with timestamps preserved."""

SUMMARIZATION_SYSTEM_PROMPT = """You are a content analyst. Your job is to summarize podcasts and newsletters for busy professionals.

For each piece of content, extract:
1. **Summary** (2-3 sentences): What is this about? Why does it matter?
2. **Key topics** (3-5 topics): Main themes or subjects discussed
3. **Companies** (0-5): Companies mentioned, with 1-sentence context
4. **Tools** (0-5): Tools, products, or technologies mentioned, with 1-sentence context
5. **Quotes** (2-4): Most interesting or insightful quotes (with timestamps for podcasts)

Be concise. Focus on actionable insights."""

RATING_SYSTEM_PROMPT = """You are a content quality rater. Your job is to rate podcasts and newsletters on a 1-5 scale based on their value to a busy professional interested in technology, business, and personal growth.

Rating scale:
- 5: Exceptional - Must-read/listen, highly actionable or insightful
- 4: Very good - Worth deep dive, clear takeaways
- 3: Good - Interesting but not urgent
- 2: Mediocre - Low signal, mostly filler
- 1: Poor - Not worth time, skip

**Be conservative with ratings:**
- 5s should be rare (top 5% of content)
- 4s should be uncommon (top 20%)
- Most content should be rated 3
- 2s and 1s for low-quality or off-topic content

Output JSON with rating (1-5) and rationale (one sentence)."""


# User prompts

def cleaning_user_prompt(title: str, duration: str, raw_transcript: str) -> str:
    """Generate cleaning prompt for transcript.

    Args:
        title: Content title
        duration: Duration string
        raw_transcript: Raw transcript text

    Returns:
        User prompt
    """
    return f"""Clean this podcast transcript:

Title: {title}
Duration: {duration}

Raw transcript:
{raw_transcript}"""


def summarization_user_prompt(
    content_type: str,
    title: str,
    author: str,
    date: str,
    content_text: str,
) -> str:
    """Generate summarization prompt.

    Args:
        content_type: "podcast" or "newsletter"
        title: Content title
        author: Author/host name
        date: Publication date
        content_text: Cleaned text content

    Returns:
        User prompt
    """
    return f"""Analyze this content:

Type: {content_type}
Title: {title}
Author: {author}
Date: {date}

Content:
{content_text}

Output JSON with the following structure:
{{
  "summary": "2-3 sentence summary",
  "key_topics": ["topic1", "topic2", ...],
  "companies": [{{"name": "Company", "context": "Brief context"}}, ...],
  "tools": [{{"name": "Tool", "context": "Brief context"}}, ...],
  "quotes": [{{"text": "Quote text", "timestamp": "12:34 or section name"}}, ...]
}}"""


def rating_user_prompt(
    content_type: str,
    title: str,
    summary: str,
    key_topics: list[str],
) -> str:
    """Generate rating prompt.

    Args:
        content_type: "podcast" or "newsletter"
        title: Content title
        summary: Content summary
        key_topics: List of key topics

    Returns:
        User prompt
    """
    topics_str = ", ".join(key_topics)

    return f"""Rate this content:

Type: {content_type}
Title: {title}
Summary: {summary}
Key topics: {topics_str}

Output JSON:
{{
  "rating": 3,
  "rationale": "One sentence explaining the rating"
}}"""
