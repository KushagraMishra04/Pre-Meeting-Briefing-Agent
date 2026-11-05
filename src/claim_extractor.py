"""
Claim Extraction Module.
Uses Gemini API to extract atomic, sourced factual claims from search snippets.
Includes heuristic fallback for testing/graceful degradation.
"""
import json
import logging
import re
from typing import List, Optional
from google import genai
from google.genai import types

from src.models import ExtractedClaim, SearchResult, ResolvedEntity

logger = logging.getLogger(__name__)


class ClaimExtractor:
    """Extracts factual claims tagged with source URLs and dates from search snippets."""

    def __init__(self, gemini_api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = gemini_api_key.strip() if gemini_api_key else None
        self.model = model
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini client: {e}")

    def extract_claims(
        self,
        entity: ResolvedEntity,
        search_results: List[SearchResult]
    ) -> List[ExtractedClaim]:
        """
        Extracts structured claims from search results.
        Uses Gemini if available, otherwise falls back to entity-filtered heuristic extractor.
        """
        if not search_results:
            return []

        if self.client:
            try:
                return self._extract_with_gemini(entity, search_results)
            except Exception as e:
                logger.error(f"Gemini claim extraction failed: {e}. Using heuristic fallback.")

        return self._extract_heuristic(entity, search_results)

    def _extract_with_gemini(
        self,
        entity: ResolvedEntity,
        search_results: List[SearchResult]
    ) -> List[ExtractedClaim]:
        """Calls Gemini API with structured JSON output."""
        snippets_text = []
        for i, res in enumerate(search_results):
            date_str = f" [Date: {res.published_date}]" if res.published_date else ""
            snippets_text.append(
                f"Source #{i+1}:\n"
                f"Title: {res.title}\n"
                f"URL: {res.url}\n"
                f"Category Hint: {res.query_category}{date_str}\n"
                f"Snippet: {res.snippet}\n"
            )

        prompt = f"""
You are an investigative fact-extraction engine preparing an executive one-page pre-meeting brief.
Target Entity: {entity.name} (Type: {entity.entity_type.value})
Meeting Date: {entity.meeting_time.strftime('%Y-%m-%d')}
Strict 30-Day Window: {entity.window_display}

Below are raw search snippets retrieved:
------------------------------------
{"".join(snippets_text)}
------------------------------------

TASK:
Extract concise, atomic factual claims strictly about {entity.name} from these snippets.

RULES:
1. STRICT RELEVANCE & GROUNDING: Every claim MUST be directly substantiated by the snippet and MUST be about {entity.name} (or its direct leadership/products). Discard unrelated articles (e.g. noise from partial keyword matches). Do NOT hallucinate.
2. CATEGORIZATION: Every claim MUST belong to exactly one category:
   - 'snapshot': 1-2 core factual statements defining what the company/person does, primary product, or current leadership role.
   - 'news': Material news developments, partnerships, announcements, regulatory updates from the last 30 days.
   - 'hires_departures': Executive moves, new hires, promotions, resignations, or leadership departures.
   - 'launches_funding': New product/feature releases, capital raised, valuation updates, or key business launches.
3. EXACT SOURCE ATTRIBUTION: 'source_url' MUST exactly match the URL of the snippet where the fact was found.
4. DATE TRACKING: Extract any specific date or timeframe mentioned in the snippet into 'date'.
5. DEDUPLICATION: Do not repeat identical facts across multiple sources.

Return a JSON array of objects with the schema:
[
  {{
    "category": "snapshot" | "news" | "hires_departures" | "launches_funding",
    "statement": "string",
    "date": "string or null",
    "source_url": "string (matching input)",
    "source_title": "string"
  }}
]
"""

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )

        text = response.text or ""
        text = re.sub(r"^```json\s*", "", text.strip())
        text = re.sub(r"\s*```$", "", text.strip())

        raw_data = json.loads(text)
        if isinstance(raw_data, dict):
            raw_data = raw_data.get("claims", list(raw_data.values())[0] if raw_data else [])

        claims = []
        for item in raw_data:
            url = item.get("source_url", "").strip()
            if not item.get("statement"):
                continue

            claims.append(
                ExtractedClaim(
                    category=item.get("category", "news").lower(),
                    statement=item.get("statement", "").strip(),
                    date=item.get("date"),
                    source_url=url,
                    source_title=item.get("source_title")
                )
            )

        return claims

    def _extract_heuristic(
        self,
        entity: ResolvedEntity,
        search_results: List[SearchResult]
    ) -> List[ExtractedClaim]:
        """Fallback extractor using sentence tokenization and entity-name filtering."""
        claims = []
        # Key terms to ensure relevance to entity
        entity_tokens = [tok.lower() for tok in re.findall(r"\w+", entity.name) if len(tok) > 2]

        for res in search_results:
            title_lower = res.title.lower()
            snippet_lower = res.snippet.lower()

            # Ensure snippet or title is actually about this entity
            is_relevant = any(tok in title_lower or tok in snippet_lower for tok in entity_tokens)
            if not is_relevant and entity_tokens:
                continue

            sentences = re.split(r"(?<=[.!?])\s+", res.snippet)
            for s in sentences:
                s_clean = s.strip()
                if len(s_clean) > 35 and not s_clean.startswith("..."):
                    # Check sentence relevance if possible
                    if any(tok in s_clean.lower() for tok in entity_tokens) or len(entity_tokens) == 0:
                        claims.append(
                            ExtractedClaim(
                                category=res.query_category,
                                statement=s_clean,
                                date=res.published_date,
                                source_url=res.url,
                                source_title=res.title
                            )
                        )
        return claims
