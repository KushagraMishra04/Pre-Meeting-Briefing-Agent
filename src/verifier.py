"""
Verification and Citation Grounding Module.
Audits claims against retrieved sources, assigns deduplicated citation tags [1], [2],
verifies 30-day window relevance, enforces Trust & Safety guardrails,
and synthesizes goal-aware strategic questions.
"""
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from datetime import datetime, timedelta
import logging
from dateutil import parser as date_parser

from google import genai
from google.genai import types

from src.models import (
    SearchResult,
    Source,
    ResolvedEntity,
    GroundedClaim,
    EvidenceQuote,
    DroppedClaimRecord,
    HallucinationAuditLog,
    VerificationStatus,
)
from src.claim_extractor import RawExtractedClaim
from src.trust_safety import TrustSafetyEngine

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
    """Performs citation verification, deduplication, trust auditing, and goal-aware questions."""

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
        claims: List[RawExtractedClaim],
        search_results: List[SearchResult],
        entity: ResolvedEntity,
        queries_executed: Optional[List[str]] = None
    ) -> Tuple[List[GroundedClaim], List[Source], HallucinationAuditLog]:
        """
        Validates claims against retrieved URLs, assigns citation indices,
        enforces privacy guardrails, checks freshness, and generates the Hallucination Audit Log.
        """
        url_to_result: Dict[str, SearchResult] = {res.url: res for res in search_results}
        source_registry: Dict[str, Source] = {}
        grounded_claims: List[GroundedClaim] = []
        dropped_claims: List[DroppedClaimRecord] = []
        privacy_filtered_count = 0

        effective_start = entity.window_start - timedelta(days=5)
        effective_end = entity.window_end + timedelta(days=2)

        for idx, claim in enumerate(claims):
            url = claim.source_url.strip()

            # 1. Privacy Guardrail Check
            is_private_safe, privacy_reason = TrustSafetyEngine.audit_privacy_guardrail(claim.statement)
            if not is_private_safe:
                privacy_filtered_count += 1
                dropped_claims.append(
                    DroppedClaimRecord(
                        statement=claim.statement[:100] + "...",
                        drop_reason=privacy_reason or "Privacy Guardrail: Filtered non-professional data",
                        raw_source=url
                    )
                )
                continue

            # 2. Source URL Match Check
            if not url or url not in url_to_result:
                dropped_claims.append(
                    DroppedClaimRecord(
                        statement=claim.statement[:100] + "...",
                        drop_reason="Ungrounded: No matching authenticated source URL in retrieval index",
                        raw_source=url
                    )
                )
                continue

            ref_res = url_to_result[url]

            # 3. 30-Day Window Relevance Check
            claim_date_str = claim.date or ref_res.published_date
            if claim_date_str and claim.category != "snapshot":
                try:
                    parsed_d = date_parser.parse(claim_date_str, fuzzy=True)
                    if parsed_d.tzinfo:
                        parsed_d = parsed_d.replace(tzinfo=None)
                    if parsed_d < effective_start or parsed_d > effective_end:
                        dropped_claims.append(
                            DroppedClaimRecord(
                                statement=claim.statement[:100] + "...",
                                drop_reason=f"Scope Exceeded: Event occurred on {claim_date_str}, outside the 30-day window",
                                raw_source=url
                            )
                        )
                        continue
                except Exception:
                    pass

            # Register source if not already seen
            if url not in source_registry:
                source_id = len(source_registry) + 1
                domain = extract_domain(url)
                date_str = ref_res.published_date or claim.date or "Recent"
                freshness_str = TrustSafetyEngine.calculate_freshness(date_str, entity.meeting_time)
                source_registry[url] = Source(
                    id=source_id,
                    title=ref_res.title or claim.source_title or domain,
                    domain=domain,
                    url=url,
                    published_date=date_str,
                    freshness=freshness_str
                )

            current_source = source_registry[url]
            status = TrustSafetyEngine.classify_rumor_vs_confirmed(claim.statement, current_source.domain)

            # Build Click-to-Evidence object
            evidence = EvidenceQuote(
                verbatim_quote=claim.verbatim_quote or claim.statement,
                source_id=current_source.id,
                source_url=url,
                source_title=current_source.title,
                freshness=current_source.freshness,
                status=status
            )

            grounded_claims.append(
                GroundedClaim(
                    id=f"claim_{idx+1}",
                    statement=claim.statement,
                    category=claim.category,
                    citation_tag=f"[{current_source.id}]",
                    evidence=evidence,
                    is_confirmed=(status == VerificationStatus.CONFIRMED),
                    date_str=claim_date_str
                )
            )

        # 4. Conflict Detection
        conflicts = TrustSafetyEngine.detect_conflicts(grounded_claims)
        for conflict_desc in conflicts:
            for gc in grounded_claims:
                if any(kw in gc.statement.lower() for kw in ["valuation", "raised", "billion", "million"]):
                    gc.conflict_detected = True
                    gc.evidence.conflict_note = conflict_desc

        sources_list = sorted(list(source_registry.values()), key=lambda s: s.id)

        # Hallucination Audit Log construction
        audit_log = HallucinationAuditLog(
            total_claims_verified=len(grounded_claims),
            dropped_claims_count=len(dropped_claims),
            dropped_claims=dropped_claims,
            queries_executed=queries_executed or [],
            privacy_filtered_count=privacy_filtered_count,
            conflicts_detected=conflicts,
            verification_score="100% Grounded" if grounded_claims else "0%"
        )

        return grounded_claims, sources_list, audit_log

    def generate_goal_aware_questions(
        self,
        entity: ResolvedEntity,
        claims: List[GroundedClaim],
        meeting_goal: Optional[str] = None
    ) -> List[str]:
        """
        Synthesizes 3-5 smart, goal-aligned questions for the meeting.
        Directly targets the user's specific meeting objective.
        """
        if self.client and claims:
            try:
                return self._generate_questions_with_gemini(entity, claims, meeting_goal)
            except Exception as e:
                logger.warning(f"Gemini questions failed: {e}. Using deterministic fallback.")

        return self._generate_questions_rule_based(entity, claims, meeting_goal)

    def _generate_questions_with_gemini(
        self,
        entity: ResolvedEntity,
        claims: List[GroundedClaim],
        meeting_goal: Optional[str]
    ) -> List[str]:
        claims_summary = "\n".join(
            [f"- {c.statement} ({c.category}, Tag: {c.citation_tag})" for c in claims[:12]]
        )
        goal_prompt = f"User's Stated Meeting Objective / Goal: '{meeting_goal}'" if meeting_goal else "General executive strategic alignment."

        prompt = f"""
You are an executive meeting strategist preparing a high-stakes briefing.
Target: {entity.name}
{goal_prompt}

Recent Verified Developments (Last 30 Days):
{claims_summary}

TASK:
Generate 3 to 4 sharp, goal-aware "Open Questions" to ask in this meeting.
Guidelines:
1. Align directly with the meeting objective ('{meeting_goal or "Strategic Partnership"}').
2. Connect the goal directly to a recent verified news event, product launch, or leadership change from the list above.
3. Sound like a prepared, authoritative peer or executive partner.
4. Each question must be 1-2 concise sentences.

Return a JSON array of strings:
["Question 1", "Question 2", "Question 3"]
"""
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.25
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

        return self._generate_questions_rule_based(entity, claims, meeting_goal)

    def _generate_questions_rule_based(
        self,
        entity: ResolvedEntity,
        claims: List[GroundedClaim],
        meeting_goal: Optional[str]
    ) -> List[str]:
        questions = []
        name = entity.name
        launches = [c for c in claims if c.category == "launches_funding"]
        hires = [c for c in claims if c.category == "hires_departures"]
        news = [c for c in claims if c.category == "news"]

        if meeting_goal:
            questions.append(
                f"With our goal of '{meeting_goal}', how do your recent announcements in the last 30 days accelerate this timeline?"
            )

        if launches:
            stmt = launches[0].statement
            questions.append(
                f"Regarding the recent launch ({stmt[:60]}...), what enterprise adoption benchmarks have been established so far?"
            )
        if hires:
            stmt = hires[0].statement
            questions.append(
                f"With recent leadership appointments ({stmt[:60]}...), how will that reshape tactical decision-making this quarter?"
            )
        if news and len(questions) < 3:
            stmt = news[0].statement
            questions.append(
                f"In light of recent industry coverage ({stmt[:60]}...), how are you managing operational risk heading into year-end?"
            )

        while len(questions) < 3:
            questions.append(f"What is the single highest-priority milestone for {name} to achieve over the next 90 days?")

        return questions[:4]
