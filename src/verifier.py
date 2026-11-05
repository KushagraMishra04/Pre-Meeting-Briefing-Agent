"""
Verification and Citation Grounding Module.
Audits claims against retrieved sources, assigns deduplicated citation tags [1], [2],
verifies 30-day window relevance, and synthesizes strategic open questions.
"""
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse
from datetime import datetime, timedelta
import logging
from dateutil import parser as date_parser

from google import genai
from google.genai import types

from src.models import (
    ExtractedClaim,
    SearchResult,
    Source,
    VerifiedClaim,
    ResolvedEntity,
    BriefData,
)

logger = logging.getLogger(__name__)


def extract_domain(url: str) -> str:
    """Extracts clean domain name from URL."""
    try:
        domain = urlparse(url).netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or "source"
    except Exception:
        return "source"


class Verifier:
    """Performs citation verification, deduplication, and generates strategic open questions."""

    def __init__(self, gemini_api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = gemini_api_key.strip() if gemini_api_key else None
        self.model = model
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini client in Verifier: {e}")

    def verify_and_ground(
        self,
        claims: List[ExtractedClaim],
        search_results: List[SearchResult],
        entity: ResolvedEntity
    ) -> Tuple[List[VerifiedClaim], List[Source]]:
        """
        Validates claims against retrieved URLs, assigns citation indices,
        and constructs the deduplicated master source list.
        """
        # Map known URLs to SearchResult for title & date lookup
        url_to_result: Dict[str, SearchResult] = {res.url: res for res in search_results}

        source_registry: Dict[str, Source] = {}
        verified_claims: List[VerifiedClaim] = []

        # Buffer for dates (allow a 5-day leeway for reporting lag)
        effective_start = entity.window_start - timedelta(days=5)
        effective_end = entity.window_end + timedelta(days=2)

        for claim in claims:
            url = claim.source_url.strip()
            if not url or url not in url_to_result:
                # Discard ungrounded claim with no verified source match
                logger.info(f"Discarding claim without verified source match: {claim.statement[:50]}...")
                continue

            ref_res = url_to_result[url]

            # Register source if not already seen
            if url not in source_registry:
                source_id = len(source_registry) + 1
                domain = extract_domain(url)
                date_str = ref_res.published_date or claim.date or "Recent"
                source_registry[url] = Source(
                    id=source_id,
                    title=ref_res.title or claim.source_title or domain,
                    domain=domain,
                    url=url,
                    published_date=date_str
                )

            current_source = source_registry[url]

            # Date window check
            is_within_window = True
            claim_date_str = claim.date or ref_res.published_date
            if claim_date_str and claim.category != "snapshot":
                try:
                    parsed_d = date_parser.parse(claim_date_str, fuzzy=True)
                    # Strip timezone for comparison if needed
                    if parsed_d.tzinfo:
                        parsed_d = parsed_d.replace(tzinfo=None)
                    if parsed_d < effective_start or parsed_d > effective_end:
                        is_within_window = False
                except Exception:
                    # If date parsing fails, accept with warning
                    is_within_window = True

            verified_claims.append(
                VerifiedClaim(
                    statement=claim.statement,
                    category=claim.category,
                    source_id=current_source.id,
                    source_url=url,
                    source_title=current_source.title,
                    source_domain=current_source.domain,
                    date=claim_date_str,
                    is_grounded=True,
                    is_within_window=is_within_window,
                    citation_tag=f"[{current_source.id}]"
                )
            )

        sources_list = sorted(list(source_registry.values()), key=lambda s: s.id)
        return verified_claims, sources_list

    def generate_open_questions(
        self,
        entity: ResolvedEntity,
        verified_claims: List[VerifiedClaim]
    ) -> List[str]:
        """
        Synthesizes 3-5 smart, non-generic conversation starters for the meeting
        based on the verified claims.
        """
        if self.client and verified_claims:
            try:
                return self._generate_questions_with_gemini(entity, verified_claims)
            except Exception as e:
                logger.warning(f"Gemini open questions generation failed: {e}. Using rule-based fallback.")

        return self._generate_questions_rule_based(entity, verified_claims)

    def _generate_questions_with_gemini(
        self,
        entity: ResolvedEntity,
        claims: List[VerifiedClaim]
    ) -> List[str]:
        """Uses Gemini to craft high-impact executive conversation questions."""
        claims_summary = "\n".join(
            [f"- {c.statement} ({c.category}, Ref: {c.citation_tag})" for c in claims[:15]]
        )

        prompt = f"""
You are an executive meeting strategist preparing a high-level briefing for a meeting with:
Entity: {entity.name} ({entity.entity_type.value})
Meeting Date: {entity.meeting_time.strftime('%B %d, %Y')}

Recent verified facts from the last 30 days:
{claims_summary}

TASK:
Generate 3 to 4 sharp, strategic "Open Questions" to ask in this meeting.
Guidelines:
1. DO NOT ask generic questions like "What are your goals?" or "How is business?".
2. Tie each question directly to a recent announcement, product launch, hire, or market development from the facts above.
3. Sound like a knowledgeable, prepared partner or executive peer.
4. Keep each question to 1-2 concise sentences.

Return a JSON array of strings:
["Question 1", "Question 2", "Question 3"]
"""
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )
        import json, re
        text = response.text or "[]"
        text = re.sub(r"^```json\s*", "", text.strip())
        text = re.sub(r"\s*```$", "", text.strip())
        data = json.loads(text)
        if isinstance(data, dict):
            data = list(data.values())[0]
        if isinstance(data, list) and data:
            return [str(q).strip() for q in data[:4]]
        return self._generate_questions_rule_based(entity, claims)

    def _generate_questions_rule_based(
        self,
        entity: ResolvedEntity,
        claims: List[VerifiedClaim]
    ) -> List[str]:
        """Deterministic fallback questions based on extracted categories."""
        questions = []
        name = entity.name

        launches = [c for c in claims if c.category == "launches_funding"]
        hires = [c for c in claims if c.category == "hires_departures"]
        news = [c for c in claims if c.category == "news"]

        if launches:
            stmt = launches[0].statement
            questions.append(
                f"Following the recent announcement regarding {stmt[:70]}..., what has customer reception been like so far?"
            )
        if hires:
            stmt = hires[0].statement
            questions.append(
                f"Given the recent leadership transition ({stmt[:60]}...), how is that reshaping your tactical priorities this quarter?"
            )
        if news:
            stmt = news[0].statement
            questions.append(
                f"With recent industry developments in mind ({stmt[:60]}...), where are you focusing resource allocation over the next 6 months?"
            )

        if len(questions) < 3:
            questions.append(
                f"What is the single biggest milestone {name} is targeting to close out this fiscal cycle?"
            )

        return questions[:4]

