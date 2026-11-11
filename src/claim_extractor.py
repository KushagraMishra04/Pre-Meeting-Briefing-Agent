"""
Claim Extraction Module with Verbatim Quote Anchors.
Uses Gemini API to extract atomic, sourced factual claims with exact supporting quotes.
Includes heuristic fallback for testing/graceful degradation.
"""
import json
import logging
import re
from typing import List, Optional
from google import genai
from google.genai import types

from src.models import SearchResult, ResolvedEntity

logger = logging.getLogger(__name__)


class RawExtractedClaim:
    def __init__(
        self,
        category: str,
        statement: str,
        verbatim_quote: str,
        date: Optional[str],
        source_url: str,
        source_title: Optional[str]
    ):
        self.category = category
        self.statement = statement
        self.verbatim_quote = verbatim_quote
        self.date = date
        self.source_url = source_url
        self.source_title = source_title


class ClaimExtractor:
    """Extracts factual claims tagged with source URLs, dates, and verbatim quotes."""

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
    ) -> List[RawExtractedClaim]:
        """
        Extracts structured claims from search results.
        Uses Gemini if available, otherwise falls back to heuristic extractor.
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
    ) -> List[RawExtractedClaim]:
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
You are an investigative fact-extraction engine preparing an executive intelligence brief.
Target Entity: {entity.name} (Type: {entity.entity_type.value})
Meeting Date: {entity.meeting_time.strftime('%Y-%m-%d')}
Strict 30-Day Window: {entity.window_display}

Raw Search Snippets:
------------------------------------
{"".join(snippets_text)}
------------------------------------

TASK:
Extract concise, atomic factual claims strictly about {entity.name} from these snippets.

RULES:
1. STRICT GROUNDING: Every claim MUST be directly substantiated by the snippet and MUST include the EXACT 'verbatim_quote' copied from the snippet.
2. CATEGORIZATION:
   - 'snapshot': Core business, product, or leadership role.
   - 'news': Material news developments, announcements, partnerships, earnings.
   - 'hires_departures': Executive moves, promotions, departures.
   - 'launches_funding': New products, capital raised, valuations, deals.
3. SOURCE ATTRIBUTION: 'source_url' MUST match the source URL.
4. DATE TRACKING: Extract any specific date or timeframe into 'date'.

Return a JSON array of objects:
[
  {{
    "category": "snapshot" | "news" | "hires_departures" | "launches_funding",
    "statement": "Concise factual statement",
    "verbatim_quote": "Exact excerpt from snippet backing this statement",
    "date": "Date string or null",
    "source_url": "Matching URL",
    "source_title": "Article title"
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
        text = response.text or "[]"
        text = re.sub(r"^```json\s*", "", text.strip())
        text = re.sub(r"\s*```$", "", text.strip())

        raw_data = json.loads(text)
        if isinstance(raw_data, dict):
            raw_data = raw_data.get("claims", list(raw_data.values())[0] if raw_data else [])

        claims = []
        for item in raw_data:
            if not item.get("statement"):
                continue
            claims.append(
                RawExtractedClaim(
                    category=item.get("category", "news").lower(),
                    statement=item.get("statement", "").strip(),
                    verbatim_quote=item.get("verbatim_quote", item.get("statement", "")),
                    date=item.get("date"),
                    source_url=item.get("source_url", "").strip(),
                    source_title=item.get("source_title", "Verified Source")
                )
            )
        return claims

    def _extract_heuristic(
        self,
        entity: ResolvedEntity,
        search_results: List[SearchResult]
    ) -> List[RawExtractedClaim]:
        claims = []
        entity_tokens = [tok.lower() for tok in re.findall(r"\w+", entity.name) if len(tok) > 2]

        for res in search_results:
            title_lower = res.title.lower()
            snippet_lower = res.snippet.lower()

            is_relevant = any(tok in title_lower or tok in snippet_lower for tok in entity_tokens)
            if not is_relevant and entity_tokens:
                continue

            sentences = re.split(r"(?<=[.!?])\s+", res.snippet)
            for s in sentences:
                s_clean = s.strip()
                if len(s_clean) > 35 and not s_clean.startswith("..."):
                    claims.append(
                        RawExtractedClaim(
                            category=res.query_category,
                            statement=s_clean,
                            verbatim_quote=s_clean,
                            date=res.published_date,
                            source_url=res.url,
                            source_title=res.title
                        )
                    )
        return claims
