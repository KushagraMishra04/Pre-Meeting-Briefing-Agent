"""
Entity Resolution and Search Query Planning Module.
Determines entity type, computes the 30-day window relative to meeting time,
and generates targeted search queries.
"""
from datetime import datetime, timedelta
import re
from typing import Dict, Optional, Tuple
from dateutil import parser as date_parser

from src.models import EntityType, ResolvedEntity


class EntityResolver:
    """Resolves entity details, 30-day time window, and search queries."""

    PERSON_INDICATORS = [
        r"\b(ceo|cto|cfo|coo|cpo|cmo|founder|co-founder|director|vp|president|head of|dr|mr|ms|mrs)\b",
        r"\b(exec|executive|lead|investor|partner)\b",
    ]

    COMPANY_SUFFIXES = [
        r"\b(inc|corp|corporation|llc|ltd|limited|technologies|tech|labs|holdings|group|capital|partners|ventures|gmbh|co\b|ai\b)",
    ]

    @staticmethod
    def parse_meeting_time(time_input: Optional[object]) -> datetime:
        """Parses meeting time from string, date, or datetime. Defaults to current time."""
        if isinstance(time_input, datetime):
            return time_input
        if hasattr(time_input, "strftime") and not isinstance(time_input, str):
            return datetime.combine(time_input, datetime.min.time())
        if isinstance(time_input, str) and time_input.strip():
            try:
                return date_parser.parse(time_input)
            except Exception:
                pass
        return datetime.now()

    @classmethod
    def detect_entity_type(cls, raw_input: str) -> Tuple[EntityType, Optional[str]]:
        """Heuristically infers whether the entity is a person or company."""
        text = raw_input.strip()
        lower_text = text.lower()

        # Check for explicit person titles
        for pattern in cls.PERSON_INDICATORS:
            if re.search(pattern, lower_text):
                return EntityType.PERSON, None

        # Check for company suffixes
        for pattern in cls.COMPANY_SUFFIXES:
            if re.search(pattern, lower_text):
                return EntityType.COMPANY, None

        words = text.split()
        if len(words) in (2, 3) and all(w[0].isupper() for w in words if w):
            return EntityType.UNKNOWN, None

        return EntityType.COMPANY, None

    @classmethod
    def resolve(
        cls,
        raw_entity: str,
        meeting_time: Optional[object] = None,
        forced_type: Optional[EntityType] = None,
        role_hint: Optional[str] = None
    ) -> ResolvedEntity:
        """
        Builds a ResolvedEntity object with calculated 30-day window
        and normalized naming.
        """
        clean_name = raw_entity.strip()
        mt = cls.parse_meeting_time(meeting_time)
        window_end = mt
        window_start = mt - timedelta(days=30)
        window_display = (
            f"{window_start.strftime('%b %d, %Y')} - {window_end.strftime('%b %d, %Y')}"
        )

        if forced_type and forced_type != EntityType.UNKNOWN:
            entity_type = forced_type
            inferred_role = role_hint
        else:
            inferred_type, inferred_role = cls.detect_entity_type(clean_name)
            entity_type = inferred_type
            if role_hint:
                inferred_role = role_hint

        return ResolvedEntity(
            raw_input=raw_entity,
            name=clean_name,
            entity_type=entity_type,
            role_or_industry=inferred_role,
            meeting_time=mt,
            window_start=window_start,
            window_end=window_end,
            window_display=window_display,
        )

    @classmethod
    def generate_queries(cls, entity: ResolvedEntity) -> Dict[str, str]:
        """
        Generates 4 targeted search queries mapped to the blueprint sections.
        """
        name = entity.name
        is_person = entity.entity_type == EntityType.PERSON

        if is_person:
            queries = {
                "snapshot": f"{name} biography current role background career",
                "news": f"{name} news interview announcements latest",
                "hires_departures": f"{name} appointed joined new role leadership",
                "launches_funding": f"{name} project launch initiatives investment",
            }
        else:
            queries = {
                "snapshot": f"{name} company overview business founded headquarters",
                "news": f"{name} news announcements press release",
                "hires_departures": f"{name} leadership appointed hire executive moves",
                "launches_funding": f"{name} product launch funding valuation raised",
            }

        return queries
