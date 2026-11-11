"""
Trust & Safety Engine.
Provides Privacy Guardrails, Rumor vs. Confirmed tagging, Conflict Detection,
Freshness calculation, Quiet-Entity handling, and Hallucination Auditing.
"""
import re
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from dateutil import parser as date_parser

from src.models import (
    VerificationStatus,
    EvidenceQuote,
    GroundedClaim,
    DroppedClaimRecord,
    HallucinationAuditLog,
    SearchResult,
    Source,
)


class TrustSafetyEngine:
    """Enterprise Trust, Safety, and Verification auditor."""

    PRIVATE_DATA_PATTERNS = [
        r"\b(spouse|wife|husband|children|daughter|son|home address|personal phone|salary details|medical condition|divorce|personal vacation)\b",
        r"\b(arrested|convicted|scandal|lawsuit against family|dating|relationship status)\b"
    ]

    RUMOR_INDICATORS = [
        r"\b(sources say|reportedly|unconfirmed|rumored|leaked|alleged|anonymous sources|insiders claim|according to people familiar)\b",
        r"\b(speculation|talks may fall through|could be valued at)\b"
    ]

    AUTHORITATIVE_DOMAINS = {
        "sec.gov", "bloomberg.com", "reuters.com", "wsj.com", "ft.com",
        "techcrunch.com", "forbes.com", "cnbc.com", "nytimes.com"
    }

    @classmethod
    def calculate_freshness(cls, date_str: Optional[str], meeting_time: datetime) -> str:
        """Computes human-readable relative age (e.g., '2 days ago', 'Yesterday')."""
        if not date_str or date_str.lower() == "recent":
            return "Recent (< 30 days)"
        try:
            parsed = date_parser.parse(date_str, fuzzy=True)
            if parsed.tzinfo:
                parsed = parsed.replace(tzinfo=None)
            diff = meeting_time - parsed
            days = diff.days
            if days <= 0:
                return "Today / Upcoming"
            elif days == 1:
                return "Yesterday"
            elif days < 7:
                return f"{days} days ago"
            elif days < 14:
                return "1 week ago"
            elif days < 30:
                return f"{days // 7} weeks ago"
            else:
                return f"{days} days ago (Historical)"
        except Exception:
            return "Within last 30 days"

    @classmethod
    def audit_privacy_guardrail(cls, text: str) -> Tuple[bool, Optional[str]]:
        """
        Enforces privacy guardrails for individuals.
        Blocks personal, domestic, and non-professional data.
        """
        lower = text.lower()
        for pattern in cls.PRIVATE_DATA_PATTERNS:
            match = re.search(pattern, lower)
            if match:
                return False, f"Privacy Guardrail Triggered: Sensitive personal term '{match.group(1)}' filtered."
        return True, None

    @classmethod
    def classify_rumor_vs_confirmed(cls, text: str, domain: str) -> VerificationStatus:
        """Determines if a claim is Confirmed or Reported / Unconfirmed rumor."""
        lower = text.lower()
        # Check rumor terms
        for pattern in cls.RUMOR_INDICATORS:
            if re.search(pattern, lower):
                return VerificationStatus.REPORTED_RUMOR

        # If from primary source or authoritative domain
        if any(auth in domain.lower() for auth in cls.AUTHORITATIVE_DOMAINS):
            return VerificationStatus.CONFIRMED
        
        return VerificationStatus.CONFIRMED

    @classmethod
    def detect_conflicts(cls, claims: List[GroundedClaim]) -> List[str]:
        """Scans claims for contradictory numbers or opposing claims."""
        conflicts = []
        # Check valuations / funding amounts
        val_map: Dict[str, List[Tuple[str, str]]] = {}
        for c in claims:
            matches = re.findall(r"\$(\d+(?:\.\d+)?\s*(?:billion|million|B|M))", c.statement, re.IGNORECASE)
            for m in matches:
                key = "financial_amount"
                val_map.setdefault(key, []).append((m, c.statement))

        if "financial_amount" in val_map and len(val_map["financial_amount"]) >= 2:
            amounts = list(set([v[0] for v in val_map["financial_amount"]]))
            if len(amounts) > 1:
                conflicts.append(
                    f"Discrepancy detected across sources regarding transaction amounts: {', '.join(amounts)}"
                )
        return conflicts

    @classmethod
    def evaluate_quiet_entity(cls, entity_name: str, claims_count: int) -> Optional[str]:
        """Returns standard quiet-entity statement if 0 verified claims found."""
        if claims_count == 0:
            return f"Nothing notable in the last 30 days for {entity_name}."
        return None

