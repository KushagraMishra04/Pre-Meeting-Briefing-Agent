"""
Comprehensive Data Models for the Pre-Meeting Briefing Agent.
Includes Attendee-Aware Intelligence, Tone Modes, Click-to-Evidence Quotes,
Trust & Safety Guardrails, Hallucination Audit, and Post-Meeting Follow-up.
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    COMPANY = "company"
    PERSON = "person"
    UNKNOWN = "unknown"


class ToneMode(str, Enum):
    EXECUTIVE = "Executive Mode (5 Key Bullets)"
    STANDARD = "Standard Mode (Balanced Overview)"
    DEEP_DIVE = "Deep-Dive Mode (Comprehensive Dossier)"


class VerificationStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    REPORTED_RUMOR = "REPORTED / UNCONFIRMED"
    CONFLICT_DETECTED = "CONFLICT DETECTED"
    UNVERIFIED = "UNVERIFIED"


class ResolvedEntity(BaseModel):
    raw_input: str
    name: str
    entity_type: EntityType = EntityType.UNKNOWN
    role_or_industry: Optional[str] = None
    company_affiliation: Optional[str] = None
    meeting_time: datetime
    window_start: datetime
    window_end: datetime
    window_display: str


class AttendeeProfile(BaseModel):
    name: str
    email: Optional[str] = None
    role_title: str
    organization_tenure: str
    recent_activity: str
    shared_interests: str
    is_quiet_entity: bool = False
    privacy_compliant: bool = True  # Enforces public professional data only


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    published_date: Optional[str] = None
    engine: str = "duckduckgo"
    query_category: str = "news"


class Source(BaseModel):
    id: int
    title: str
    domain: str
    url: str
    published_date: Optional[str] = "Recent"
    freshness: str = "Recent"  # e.g., "2 days ago", "Yesterday"
    is_authoritative: bool = True


class EvidenceQuote(BaseModel):
    verbatim_quote: str
    source_id: int
    source_url: str
    source_title: str
    freshness: str = "Recent"
    status: VerificationStatus = VerificationStatus.CONFIRMED
    conflict_note: Optional[str] = None


class GroundedClaim(BaseModel):
    id: str
    statement: str
    category: str  # snapshot, news, hires_departures, launches_funding, strategic_risk
    citation_tag: str  # e.g., "[1]"
    evidence: EvidenceQuote
    is_confirmed: bool = True
    conflict_detected: bool = False
    date_str: Optional[str] = None


class DroppedClaimRecord(BaseModel):
    statement: str
    drop_reason: str
    raw_source: Optional[str] = None


class HallucinationAuditLog(BaseModel):
    total_claims_verified: int
    dropped_claims_count: int
    dropped_claims: List[DroppedClaimRecord] = Field(default_factory=list)
    queries_executed: List[str] = Field(default_factory=list)
    privacy_filtered_count: int = 0
    conflicts_detected: List[str] = Field(default_factory=list)
    verification_score: str = "100%"


class SinceLastBriefDiff(BaseModel):
    previous_meeting_date: Optional[str] = None
    new_developments: List[str] = Field(default_factory=list)
    leadership_updates: List[str] = Field(default_factory=list)
    product_shifts: List[str] = Field(default_factory=list)
    has_diff: bool = False


class ActionItem(BaseModel):
    task: str
    owner: str
    deadline: Optional[str] = "Next sync"
    priority: str = "High"


class FollowUpEmail(BaseModel):
    subject: str
    recipients: List[str] = Field(default_factory=list)
    body: str


class ParsedCalendarInvite(BaseModel):
    title: str
    meeting_time: datetime
    end_time: Optional[datetime] = None
    goal_agenda: str
    location_or_link: Optional[str] = None
    organizer: Optional[str] = None
    attendees: List[str] = Field(default_factory=list)
    raw_text: Optional[str] = None


class BriefData(BaseModel):
    entity: ResolvedEntity
    tone_mode: ToneMode = ToneMode.STANDARD
    meeting_goal: Optional[str] = None
    attendees: List[AttendeeProfile] = Field(default_factory=list)
    snapshot: str
    news_items: List[GroundedClaim] = Field(default_factory=list)
    hires_departures: List[GroundedClaim] = Field(default_factory=list)
    launches_funding: List[GroundedClaim] = Field(default_factory=list)
    executive_bullets: List[str] = Field(default_factory=list)  # Exactly 5 bullets for Executive Mode
    deep_dive_context: Optional[Dict[str, Any]] = None  # Historical context & debates for Deep-Dive Mode
    goal_aware_questions: List[str] = Field(default_factory=list)
    diff: Optional[SinceLastBriefDiff] = None
    sources: List[Source] = Field(default_factory=list)
    audit_panel: HallucinationAuditLog
    quiet_entity_note: Optional[str] = None
    stats: Dict[str, Any] = Field(default_factory=dict)
