"""
Brief Synthesis Module.
Assembles the verified claims into the strict 6-section blueprint:
1. Snapshot (2 lines)
2. News (30d) (top 3-5 items)
3. Hires & Departures
4. Launches & Funding
5. Open Questions
6. Sources (numbered, with dates)
"""
from typing import List, Optional
import logging
from google import genai
from google.genai import types

from src.models import (
    BriefData,
    ResolvedEntity,
    Source,
    VerifiedClaim,
)

logger = logging.getLogger(__name__)


class BriefGenerator:
    """Assembles and formats the complete executive one-page brief."""

    def __init__(self, gemini_api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = gemini_api_key.strip() if gemini_api_key else None
        self.model = model
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini client: {e}")

    def synthesize_snapshot(
        self,
        entity: ResolvedEntity,
        snapshot_claims: List[VerifiedClaim]
    ) -> str:
        """Generates a crisp 2-line executive snapshot with source citations."""
        if not snapshot_claims:
            return f"{entity.name} is a prominent entity in its industry sector. [1]"

        if self.client:
            try:
                claims_text = "\n".join(
                    [f"- {c.statement} [Source ID: {c.source_id}]" for c in snapshot_claims[:5]]
                )
                prompt = f"""
You are an executive editor.
Summarize the entity '{entity.name}' ({entity.entity_type.value}) in EXACTLY TWO concise lines.
Line 1: Core identity, what they do/build, and primary market/industry.
Line 2: Scale, headquarters, key metric/valuation, or current leadership position.

Rules:
- Append the source citation tag (e.g. [1], [2]) directly after each factual statement.
- Do NOT exceed two lines. Keep it under 50 words total.

Facts:
{claims_text}
"""
                resp = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.2)
                )
                text = resp.text.strip() if resp.text else ""
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                if len(lines) >= 2:
                    return f"{lines[0]}\n{lines[1]}"
                elif lines:
                    return lines[0]
            except Exception as e:
                logger.warning(f"LLM snapshot synthesis failed: {e}")

        # Fallback
        c1 = snapshot_claims[0]
        c2 = snapshot_claims[1] if len(snapshot_claims) > 1 else None
        res = f"{c1.statement} [{c1.source_id}]"
        if c2:
            res += f"\n{c2.statement} [{c2.source_id}]"
        return res

    def generate(
        self,
        entity: ResolvedEntity,
        verified_claims: List[VerifiedClaim],
        sources: List[Source],
        open_questions: List[str]
    ) -> BriefData:
        """Builds the complete BriefData adhering strictly to the 6 sections."""
        # 1. Filter claims by category
        snapshot_claims = [c for c in verified_claims if c.category == "snapshot"]
        news_claims = [c for c in verified_claims if c.category == "news" and c.is_within_window]
        hire_claims = [c for c in verified_claims if c.category == "hires_departures" and c.is_within_window]
        launch_claims = [c for c in verified_claims if c.category == "launches_funding" and c.is_within_window]

        # 2. Section 1: Snapshot
        snapshot_text = self.synthesize_snapshot(entity, snapshot_claims)

        # 3. Section 2: News (top 3-5 items)
        news_items = []
        for c in news_claims[:5]:
            date_prefix = f"({c.date}) " if c.date and len(c.date) <= 12 else ""
            news_items.append(f"{date_prefix}{c.statement} {c.citation_tag}")
        if not news_items:
            news_items = ["No major public news events reported within this 30-day window."]

        # 4. Section 3: Hires & departures
        hires_items = []
        for c in hire_claims[:4]:
            date_prefix = f"({c.date}) " if c.date and len(c.date) <= 12 else ""
            hires_items.append(f"{date_prefix}{c.statement} {c.citation_tag}")
        if not hires_items:
            hires_items = ["No executive departures or leadership appointments announced in the last 30 days."]

        # 5. Section 4: Launches & funding
        launches_items = []
        for c in launch_claims[:4]:
            date_prefix = f"({c.date}) " if c.date and len(c.date) <= 12 else ""
            launches_items.append(f"{date_prefix}{c.statement} {c.citation_tag}")
        if not launches_items:
            launches_items = ["No major product launches or public funding rounds disclosed in the last 30 days."]

        # 6. Section 5: Open questions (guaranteed 3-4 items)
        questions = open_questions[:4] if open_questions else [
            f"What strategic priority is top-of-mind for {entity.name} heading into next quarter?",
            f"How is the team adapting resource allocation following recent market announcements?"
        ]

        return BriefData(
            entity=entity,
            snapshot=snapshot_text,
            news_items=news_items,
            hires_departures=hires_items,
            launches_funding=launches_items,
            open_questions=questions,
            sources=sources,
            stats={
                "total_sources": len(sources),
                "total_verified_claims": len(verified_claims),
                "meeting_time": entity.meeting_time.isoformat(),
            }
        )

    @staticmethod
    def to_markdown(brief: BriefData) -> str:
        """Renders the brief into clean executive Markdown format."""
        md = []
        md.append(f"# Executive Brief: {brief.entity.name}")
        md.append(f"**Meeting Time:** {brief.entity.meeting_time.strftime('%b %d, %Y at %I:%M %p')}  ")
        md.append(f"**Scope Window (30 Days):** {brief.entity.window_display}  \n")
        md.append("---\n")

        # 1. Snapshot
        md.append("### 1. Snapshot")
        md.append(brief.snapshot)
        md.append("")

        # 2. News (30d)
        md.append("### 2. News (Last 30 Days)")
        for item in brief.news_items:
            md.append(f"- {item}")
        md.append("")

        # 3. Hires & Departures
        md.append("### 3. Hires & Departures")
        for item in brief.hires_departures:
            md.append(f"- {item}")
        md.append("")

        # 4. Launches & Funding
        md.append("### 4. Launches & Funding")
        for item in brief.launches_funding:
            md.append(f"- {item}")
        md.append("")

        # 5. Open Questions
        md.append("### 5. Open Questions for Meeting")
        for i, q in enumerate(brief.open_questions, 1):
            md.append(f"{i}. {q}")
        md.append("")

        # 6. Sources
        md.append("### 6. Sources")
        for s in brief.sources:
            date_str = f", {s.published_date}" if s.published_date else ""
            md.append(f"[{s.id}] **{s.title}** ({s.domain}{date_str}) — [{s.url}]({s.url})")

        return "\n".join(md)
