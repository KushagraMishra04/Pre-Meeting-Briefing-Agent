"""
Ask-The-Brief Q&A Engine.
Provides grounded conversational question answering against the generated brief,
attendee context, and retrieved sources with numbered citations.
"""
import re
import logging
from typing import List, Optional
from google import genai
from google.genai import types

from src.models import BriefData

logger = logging.getLogger(__name__)


class AskBriefEngine:
    """Answers user queries grounded strictly in the generated brief and sources."""

    def __init__(self, gemini_api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = gemini_api_key.strip() if gemini_api_key else None
        self.model = model
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini in AskBriefEngine: {e}")

    def answer_question(self, question: str, brief: BriefData) -> str:
        """Generates an answer strictly grounded in the brief's facts and citations."""
        if not question.strip():
            return "Please enter a question about this meeting or company."

        if self.client:
            try:
                return self._answer_with_gemini(question, brief)
            except Exception as e:
                logger.warning(f"Gemini AskBrief failed: {e}. Falling back to semantic search.")

        return self._answer_semantic_fallback(question, brief)

    def _answer_with_gemini(self, question: str, brief: BriefData) -> str:
        # Build grounding context
        attendees_txt = "\n".join([f"- {a.name} ({a.role_title}, {a.organization_tenure})" for a in brief.attendees])
        news_txt = "\n".join([f"- {item.statement} {item.citation_tag}" for item in brief.news_items])
        hires_txt = "\n".join([f"- {item.statement} {item.citation_tag}" for item in brief.hires_departures])
        launches_txt = "\n".join([f"- {item.statement} {item.citation_tag}" for item in brief.launches_funding])
        sources_txt = "\n".join([f"[{s.id}] {s.title} ({s.domain}) - {s.url}" for s in brief.sources])

        context = f"""
TARGET ENTITY: {brief.entity.name}
MEETING TIME: {brief.entity.meeting_time.strftime('%Y-%m-%d %H:%M')}
STRICT 30-DAY WINDOW: {brief.entity.window_display}
MEETING GOAL: {brief.meeting_goal or 'Not specified'}

ATTENDEES:
{attendees_txt or 'None listed'}

SNAPSHOT:
{brief.snapshot}

MATERIAL NEWS (LAST 30 DAYS):
{news_txt}

LEADERSHIP & HIRES:
{hires_txt}

LAUNCHES & FUNDING:
{launches_txt}

NUMBERED SOURCES:
{sources_txt}
"""

        prompt = f"""
You are an executive intelligence assistant answering questions about an upcoming meeting.
Answer the user's question using ONLY the provided verified context.

RULES:
1. Ground every single claim in the citations [1], [2], etc. from the context.
2. If the answer is NOT present in the context, explicitly say:
   "Based on the verified 30-day brief, there is no verified public record of this."
3. Keep the answer direct, executive-ready, and concise (2-4 sentences).

QUESTION: {question}

CONTEXT:
{context}
"""
        config = types.GenerateContentConfig(temperature=0.1)
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )
        return response.text.strip() if response.text else "No response generated."

    def _answer_semantic_fallback(self, question: str, brief: BriefData) -> str:
        """Deterministic keyword search over brief claims."""
        tokens = [t.lower() for t in re.findall(r"\w+", question) if len(t) > 2]
        all_claims = brief.news_items + brief.hires_departures + brief.launches_funding

        scored = []
        for c in all_claims:
            score = sum(1 for tok in tokens if tok in c.statement.lower())
            if score > 0:
                scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)

        if scored:
            top_claim = scored[0][1]
            return f"{top_claim.statement} {top_claim.citation_tag}\n\n*Verified Quote: \"{top_claim.evidence.verbatim_quote[:120]}...\" (Source: {top_claim.evidence.source_title})*"

        # Check snapshot
        if any(tok in brief.snapshot.lower() for tok in tokens):
            return f"{brief.snapshot}\n\n*(Sourced from Primary Entity Profile)*"

        return f"Based on the verified 30-day brief for {brief.entity.name}, there is no specific record regarding '{question}' in the retrieved sources."

