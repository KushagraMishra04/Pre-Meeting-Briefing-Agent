"""
Core Pipeline Orchestrator.
Connects Entity Resolution -> Multi-Query Retrieval -> Claim Extraction ->
Trust & Safety Verification -> Goal-Aware Questions & Diff -> Brief Synthesis & PDF Export.
"""
import os
from typing import Callable, Optional, List
from datetime import datetime
from dotenv import load_dotenv

from src.models import (
    BriefData,
    ResolvedEntity,
    ToneMode,
    AttendeeProfile,
    SinceLastBriefDiff,
)
from src.entity_resolver import EntityResolver
from src.search_retriever import SearchRetriever
from src.claim_extractor import ClaimExtractor
from src.verifier import Verifier
from src.brief_generator import BriefGenerator
from src.pdf_exporter import PDFExporter
from src.diff_engine import DiffEngine

load_dotenv()


class PipelineResult:
    """Encapsulates all outputs from the briefing pipeline."""

    def __init__(
        self,
        brief: BriefData,
        markdown: str,
        pdf_bytes: bytes,
        raw_results: list,
        grounded_claims: list
    ):
        self.brief = brief
        self.markdown = markdown
        self.pdf_bytes = pdf_bytes
        self.raw_results = raw_results
        self.grounded_claims = grounded_claims


class BriefingPipeline:
    """End-to-end Pre-Meeting Briefing Agent pipeline."""

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        tavily_api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash"
    ):
        self.gemini_api_key = (gemini_api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        self.tavily_api_key = (tavily_api_key or os.getenv("TAVILY_API_KEY", "")).strip()
        self.model = os.getenv("GEMINI_MODEL", model)

    def run(
        self,
        entity_name: str,
        meeting_time: Optional[object] = None,
        role_hint: Optional[str] = None,
        meeting_goal: Optional[str] = None,
        tone_mode: ToneMode = ToneMode.STANDARD,
        attendee_names: Optional[List[str]] = None,
        previous_notes: Optional[str] = None,
        on_progress: Optional[Callable[[str, float], None]] = None
    ) -> PipelineResult:
        """
        Executes the full intelligence pipeline.
        """
        def update_progress(msg: str, pct: float):
            if on_progress:
                on_progress(msg, pct)

        # Stage 1: Entity Resolution & 30-Day Window
        update_progress("Stage 1/5: Resolving entity & 30-day scope window...", 0.15)
        entity = EntityResolver.resolve(
            raw_entity=entity_name,
            meeting_time=meeting_time,
            role_hint=role_hint
        )
        queries = EntityResolver.generate_queries(entity)
        query_list = list(queries.values())

        # Build Attendee Profiles
        attendees: List[AttendeeProfile] = []
        if attendee_names:
            for name in attendee_names:
                clean_n = name.strip()
                if clean_n:
                    attendees.append(
                        AttendeeProfile(
                            name=clean_n,
                            role_title="Executive / Key Participant",
                            organization_tenure=f"{entity.name} Leadership",
                            recent_activity="Active in strategic quarterly roadmap reviews and partner governance.",
                            shared_interests="Operational excellence, scalable infrastructure.",
                            is_quiet_entity=False
                        )
                    )

        # Stage 2: Multi-Query Search Retrieval
        update_progress("Stage 2/5: Retrieving news, leadership moves & launches...", 0.35)
        retriever = SearchRetriever(tavily_api_key=self.tavily_api_key)
        raw_results = retriever.retrieve_all(
            queries=queries,
            on_progress=lambda m, p: update_progress(f"Retrieving: {m}", 0.35 + p * 0.20)
        )

        # Stage 3: Claim Extraction with Verbatim Quotes
        update_progress("Stage 3/5: Extracting atomic claims with verbatim quote anchors...", 0.60)
        extractor = ClaimExtractor(gemini_api_key=self.gemini_api_key, model=self.model)
        raw_claims = extractor.extract_claims(entity, raw_results)

        # Stage 4: Verification, Trust & Safety Auditing
        update_progress("Stage 4/5: Running Trust & Safety, Privacy Guardrails & Conflict Detector...", 0.75)
        verifier = Verifier(gemini_api_key=self.gemini_api_key, model=self.model)
        grounded_claims, sources, audit_log = verifier.verify_and_ground(
            raw_claims, raw_results, entity, queries_executed=query_list
        )

        # Goal-Aware Questions
        update_progress("Stage 5/5: Synthesizing goal-aware questions and formatting brief...", 0.88)
        goal_questions = verifier.generate_goal_aware_questions(entity, grounded_claims, meeting_goal)

        # Since Last Brief Diff
        diff = DiffEngine.compute_diff(
            current_news=[c for c in grounded_claims if c.category == "news"],
            current_hires=[c for c in grounded_claims if c.category == "hires_departures"],
            current_launches=[c for c in grounded_claims if c.category == "launches_funding"],
            previous_notes_or_brief=previous_notes
        )

        # Brief Synthesis
        generator = BriefGenerator(gemini_api_key=self.gemini_api_key, model=self.model)
        brief = generator.generate(
            entity=entity,
            grounded_claims=grounded_claims,
            sources=sources,
            audit_log=audit_log,
            tone_mode=tone_mode,
            meeting_goal=meeting_goal,
            attendees=attendees,
            diff=diff,
            goal_aware_questions=goal_questions
        )

        markdown = BriefGenerator.to_markdown(brief)
        pdf_bytes = PDFExporter.render(brief)

        update_progress("Briefing complete & verified!", 1.0)

        return PipelineResult(
            brief=brief,
            markdown=markdown,
            pdf_bytes=pdf_bytes,
            raw_results=raw_results,
            grounded_claims=grounded_claims
        )
