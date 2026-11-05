"""
Data models for the Pre-Meeting Briefing Agent.
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


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    published_date: Optional[str] = None
    engine: str = "tavily"  # "tavily" or "duckduckgo"
    query_category: str = "news"  # "snapshot", "news", "hires_departures", "launches_funding"


class Source(BaseModel):
    id: int
    title: str
    domain: str
    url: str
    published_date: Optional[str] = "Recent"


class ExtractedClaim(BaseModel):
    category: str = Field(description="snapshot, news, hires_departures, or launches_funding")
    statement: str = Field(description="Factual statement extracted from source")
    date: Optional[str] = Field(default=None, description="Reported date or timeframe")
    source_url: str = Field(description="Exact URL this claim was retrieved from")
    source_title: Optional[str] = Field(default=None, description="Title of the source article")


class VerifiedClaim(BaseModel):
    statement: str
    category: str
    source_id: int
    source_url: str
    source_title: str
    source_domain: str
    date: Optional[str] = None
    is_grounded: bool = True
    is_within_window: bool = True
    citation_tag: str  # e.g., "[1]"


class BriefData(BaseModel):
    entity: ResolvedEntity
    snapshot: str  # 2 lines overview
    snapshot_citations: List[int] = Field(default_factory=list)
    news_items: List[str] = Field(default_factory=list)  # Formatted with [1], [2]
    hires_departures: List[str] = Field(default_factory=list)
    launches_funding: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)  # 3-5 strategic questions
    sources: List[Source] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)

