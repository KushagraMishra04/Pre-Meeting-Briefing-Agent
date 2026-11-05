"""
Core Pipeline Orchestrator.
Connects Entity Resolution -> Retrieval -> Claim Extraction -> Verification -> Brief & PDF Generation.
"""
import os
from typing import Callable, Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from src.models import BriefData, ResolvedEntity
from src.entity_resolver import EntityResolver
from src.search_retriever import SearchRetriever
from src.claim_extractor import ClaimExtractor
from src.verifier import Verifier
from src.brief_generator import BriefGenerator
from src.pdf_exporter import PDFExporter

load_dotenv()


class PipelineResult:
    """Encapsulates all outputs from the briefing pipeline."""

    def __init__(
        self,
        brief: BriefData,
        markdown: str,
        pdf_bytes: bytes,
        raw_results: list,
        verified_claims: list
    ):
        self.brief = brief
        self.markdown = markdown
        self.pdf_bytes = pdf_bytes
        self.raw_results = raw_results
        self.verified_claims = verified_claims


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
        on_progress: Optional[Callable[[str, float], None]] = None
    ) -> PipelineResult:
        """
        Executes the 5-stage briefing pipeline.
        """
        def update_progress(msg: str, pct: float):
            if on_progress:
                on_progress(msg, pct)

        # Stage 1: Entity Resolution & Query Planning
        update_progress("Stage 1/5: Resolving entity & 30-day window...", 0.15)
        entity = EntityResolver.resolve(
            raw_entity=entity_name,
            meeting_time=meeting_time,
            role_hint=role_hint
        )
        queries = EntityResolver.generate_queries(entity)

        # Stage 2: Multi-Query Search Retrieval (Tavily with DDG fallback)
        update_progress("Stage 2/5: Retrieving news, leadership moves & launches...", 0.35)
        retriever = SearchRetriever(tavily_api_key=self.tavily_api_key)
        raw_results = retriever.retrieve_all(
            queries=queries,
            on_progress=lambda m, p: update_progress(f"Retrieving: {m}", 0.35 + p * 0.20)
        )

        # Stage 3: Claim Extraction
        update_progress("Stage 3/5: Extracting atomic factual claims with citations...", 0.60)
        extractor = ClaimExtractor(gemini_api_key=self.gemini_api_key, model=self.model)
        extracted_claims = extractor.extract_claims(entity, raw_results)

        # Stage 4: Verification & Citation Grounding
        update_progress("Stage 4/5: Verifying citations, dates & generating open questions...", 0.78)
        verifier = Verifier(gemini_api_key=self.gemini_api_key, model=self.model)
        verified_claims, sources = verifier.verify_and_ground(extracted_claims, raw_results, entity)
        open_questions = verifier.generate_open_questions(entity, verified_claims)

        # Stage 5: Brief Synthesis & PDF Export
        update_progress("Stage 5/5: Synthesizing executive brief and rendering one-page PDF...", 0.92)
        generator = BriefGenerator(gemini_api_key=self.gemini_api_key, model=self.model)
        brief = generator.generate(entity, verified_claims, sources, open_questions)
        markdown = BriefGenerator.to_markdown(brief)
        pdf_bytes = PDFExporter.render(brief)

        update_progress("Briefing complete!", 1.0)

        return PipelineResult(
            brief=brief,
            markdown=markdown,
            pdf_bytes=pdf_bytes,
            raw_results=raw_results,
            verified_claims=verified_claims
        )

