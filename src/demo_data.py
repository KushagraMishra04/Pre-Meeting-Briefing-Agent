"""
Pre-computed, verified executive briefs for instant 1-click demos.
Demonstrates Attendee-Aware Intelligence, Tone Modes, Click-to-Evidence Quotes,
Quiet-Entity handling, Discrepancy/Conflict flags, and the Hallucination Audit Panel.
"""
from datetime import datetime, timedelta
from src.models import (
    BriefData,
    ResolvedEntity,
    Source,
    EntityType,
    ToneMode,
    AttendeeProfile,
    GroundedClaim,
    EvidenceQuote,
    VerificationStatus,
    HallucinationAuditLog,
    DroppedClaimRecord,
    SinceLastBriefDiff,
)


def get_demo_briefs() -> dict:
    now = datetime.now()
    w_end = now
    w_start = now - timedelta(days=30)
    w_str = f"{w_start.strftime('%b %d, %Y')} – {w_end.strftime('%b %d, %Y')}"

    # ==========================================
    # 1. STRIPE DEMO BRIEF (Standard & Executive)
    # ==========================================
    stripe_entity = ResolvedEntity(
        raw_input="Stripe",
        name="Stripe",
        entity_type=EntityType.COMPANY,
        role_or_industry="Financial Infrastructure & Global Payments",
        meeting_time=now + timedelta(days=1, hours=10),
        window_start=w_start,
        window_end=w_end,
        window_display=w_str
    )

    stripe_sources = [
        Source(id=1, title="Stripe Company Overview & Scale", domain="stripe.com", url="https://stripe.com/about", published_date="Oct 2026", freshness="2 weeks ago"),
        Source(id=2, title="Stripe and FedEx Partner on SMB Working Capital Lending", domain="finance.yahoo.com", url="https://finance.yahoo.com/small-business/articles/stripe-fedex-team-smb-lending-144117456.html", published_date="Oct 06, 2026", freshness="3 weeks ago"),
        Source(id=3, title="John Collison on AI Agents and Machine-to-Machine Commerce", domain="techcrunch.com", url="https://techcrunch.com/stripe-agentic-commerce", published_date="Oct 24, 2026", freshness="5 days ago"),
        Source(id=4, title="Stripe Expands Stablecoin Pay with Paxos Integration", domain="coindesk.com", url="https://www.coindesk.com/business/stripe-stablecoin-paxos", published_date="Oct 18, 2026", freshness="1 week ago"),
        Source(id=5, title="Leadership Update: Stripe Appoints Global Head of Enterprise Banking", domain="bloomberg.com", url="https://www.bloomberg.com/news/articles/stripe-leadership-hire", published_date="Oct 29, 2026", freshness="3 days ago"),
    ]

    stripe_attendees = [
        AttendeeProfile(
            name="Patrick Collison",
            role_title="Co-Founder & CEO",
            organization_tenure="Stripe (14 yrs)",
            recent_activity="Keynoted Stripe Sessions; published essay on economic infrastructure and agentic commerce protocol.",
            shared_interests="Systems engineering, programmatic finance, fast payment settlement rails."
        ),
        AttendeeProfile(
            name="Will Gaybrick",
            role_title="President of Product & Business",
            organization_tenure="Stripe (9 yrs, ex-Thrive Capital)",
            recent_activity="Led rollout of stablecoin merchant gateway and enterprise banking treasury APIs.",
            shared_interests="Enterprise fintech architecture, SMB liquidity, venture capital."
        )
    ]

    stripe_news = [
        GroundedClaim(
            id="str_n1",
            statement="(Oct 24) Co-founder John Collison unveiled Stripe's Agentic Commerce Protocol enabling AI agents to programmatically negotiate and execute checkouts.",
            category="news",
            citation_tag="[3]",
            evidence=EvidenceQuote(
                verbatim_quote="Stripe considers autonomous machine-to-machine transactions the next major paradigm shift in global internet commerce.",
                source_id=3,
                source_url="https://techcrunch.com/stripe-agentic-commerce",
                source_title="John Collison on AI Agents and Machine-to-Machine Commerce",
                freshness="5 days ago",
                status=VerificationStatus.CONFIRMED
            ),
            is_confirmed=True
        ),
        GroundedClaim(
            id="str_n2",
            statement="(Oct 18) Re-launched and expanded global stablecoin payments across 150+ countries via partnerships with Paxos and Circle.",
            category="news",
            citation_tag="[4]",
            evidence=EvidenceQuote(
                verbatim_quote="Merchants in more than 150 countries can now accept stablecoins with instant conversion into fiat bank accounts.",
                source_id=4,
                source_url="https://www.coindesk.com/business/stripe-stablecoin-paxos",
                source_title="Stripe Expands Stablecoin Pay with Paxos Integration",
                freshness="1 week ago",
                status=VerificationStatus.CONFIRMED
            ),
            is_confirmed=True
        ),
        GroundedClaim(
            id="str_n3",
            statement="(Oct 06) Formed a joint initiative with FedEx to provide automated working capital and short-term credit to SMB e-commerce merchants.",
            category="news",
            citation_tag="[2]",
            evidence=EvidenceQuote(
                verbatim_quote="Merging operational logistics and financial data will offer insights into smaller businesses to extend capital to them.",
                source_id=2,
                source_url="https://finance.yahoo.com/small-business/articles/stripe-fedex-team-smb-lending-144117456.html",
                source_title="Stripe and FedEx Partner on SMB Working Capital Lending",
                freshness="3 weeks ago",
                status=VerificationStatus.CONFIRMED
            ),
            is_confirmed=True
        )
    ]

    stripe_hires = [
        GroundedClaim(
            id="str_h1",
            statement="(Oct 29) Appointed former Morgan Stanley tech managing director as Global Head of Enterprise Banking.",
            category="hires_departures",
            citation_tag="[5]",
            evidence=EvidenceQuote(
                verbatim_quote="The hire signals Stripe's acceleration into full-stack corporate treasury and working capital solutions.",
                source_id=5,
                source_url="https://www.bloomberg.com/news/articles/stripe-leadership-hire",
                source_title="Leadership Update: Stripe Appoints Global Head of Enterprise Banking",
                freshness="3 days ago",
                status=VerificationStatus.CONFIRMED
            ),
            is_confirmed=True
        )
    ]

    stripe_launches = [
        GroundedClaim(
            id="str_l1",
            statement="(Oct 24) Released developer preview of the 'Agentic Commerce SDK' supporting programmable tokenized spending limits.",
            category="launches_funding",
            citation_tag="[3]",
            evidence=EvidenceQuote(
                verbatim_quote="Developers can now attach automated budget caps and authentication tokens to AI agents.",
                source_id=3,
                source_url="https://techcrunch.com/stripe-agentic-commerce",
                source_title="John Collison on AI Agents and Machine-to-Machine Commerce",
                freshness="5 days ago",
                status=VerificationStatus.CONFIRMED
            ),
            is_confirmed=True
        )
    ]

    stripe_audit = HallucinationAuditLog(
        total_claims_verified=5,
        dropped_claims_count=2,
        dropped_claims=[
            DroppedClaimRecord(
                statement="Rumored acquisition of European crypto exchange for $1.2B...",
                drop_reason="Ungrounded: Anonymous blog rumor with no authenticated primary source",
                raw_source="https://unverified-crypto-leaks.xyz"
            ),
            DroppedClaimRecord(
                statement="Patrick Collison personal property purchase in Ireland...",
                drop_reason="Privacy Guardrail: Filtered non-professional personal data",
                raw_source="https://irish-realestate-tabloid.com"
            )
        ],
        queries_executed=["Stripe news", "Stripe leadership moves", "Stripe agentic commerce"],
        privacy_filtered_count=1,
        conflicts_detected=[],
        verification_score="100% Grounded"
    )

    stripe_diff = SinceLastBriefDiff(
        previous_meeting_date="Oct 10, 2026",
        new_developments=[
            "Launched Agentic Commerce Protocol on Oct 24 with programmable tokenized spending limits.",
            "Expanded stablecoin rails across 150+ countries with instant local fiat settlement on Oct 18."
        ],
        leadership_updates=[
            "Appointed Global Head of Enterprise Banking from Morgan Stanley on Oct 29."
        ],
        product_shifts=[
            "Introduced Agentic Commerce SDK for autonomous AI checkout."
        ],
        has_diff=True
    )

    stripe_brief = BriefData(
        entity=stripe_entity,
        tone_mode=ToneMode.STANDARD,
        meeting_goal="Negotiate enterprise volume pricing tiers and evaluate beta access for Agentic Commerce Protocol.",
        attendees=stripe_attendees,
        snapshot="Stripe is a dual-headquartered (South San Francisco & Dublin) financial infrastructure platform powering internet commerce, handling over $1 trillion in annual payment volume for millions of global businesses. [1]\nCo-founded by Patrick and John Collison, the company has expanded from core payment acquiring into billing, fraud prevention, issuing, and agentic machine-to-machine checkout. [1][3]",
        news_items=stripe_news,
        hires_departures=stripe_hires,
        launches_funding=stripe_launches,
        executive_bullets=[
            "Strategic Intent: Partner with Stripe to pilot Agentic Commerce Protocol while locking in tier-1 enterprise pricing. [3]",
            "Material Catalyst: Stripe's Oct 24 launch of Agentic Commerce SDK enables autonomous micro-billing without human intervention. [3]",
            "Key Commercial Risk: Clarify liability and chargeback indemnity for unauthorized automated AI transactions.",
            "Market Leverage: Leverage our enterprise transaction volume to negotiate custom basis-point fee reductions.",
            "Decision Needed: Secure executive agreement on 90-day pilot scope and sign off on rate card before concluding meeting."
        ],
        goal_aware_questions=[
            "Given our goal to pilot the Agentic Commerce Protocol, what fraud mitigation and chargeback indemnity do you provide for autonomous agent transactions?",
            "With your new FedEx SMB lending initiative, how can we leverage that telemetry data to extend credit lines to our marketplace suppliers?",
            "How do your stablecoin conversion rates compare to traditional cross-border SWIFT wire costs for multi-currency B2B payouts?"
        ],
        diff=stripe_diff,
        sources=stripe_sources,
        audit_panel=stripe_audit,
        quiet_entity_note=None,
        stats={"total_sources": 5, "total_verified_claims": 5, "dropped_claims": 2}
    )

    # ==========================================
    # 2. ANTHROPIC DEMO BRIEF (Deep-Dive & Conflict Flag)
    # ==========================================
    anthropic_entity = ResolvedEntity(
        raw_input="Anthropic",
        name="Anthropic",
        entity_type=EntityType.COMPANY,
        role_or_industry="Frontier AI Safety & Foundation Models",
        meeting_time=now + timedelta(days=2, hours=14),
        window_start=w_start,
        window_end=w_end,
        window_display=w_str
    )

    anthropic_sources = [
        Source(id=1, title="Anthropic Company Profile & Public Benefit Charter", domain="anthropic.com", url="https://www.anthropic.com/company", published_date="Oct 2026", freshness="2 weeks ago"),
        Source(id=2, title="Anthropic Unveils Computer Use Feature for Claude 3.5 Sonnet", domain="techcrunch.com", url="https://techcrunch.com/2026/10/22/anthropic-claude-computer-use", published_date="Oct 22, 2026", freshness="4 days ago"),
        Source(id=3, title="Anthropic Discloses Recursive Self-Improvement Safety Thresholds", domain="finance.yahoo.com", url="https://finance.yahoo.com/technology/ai/articles/safety-risk-anthropic-warns-ai-033013790.html", published_date="Nov 04, 2026", freshness="Yesterday"),
        Source(id=4, title="Amazon and Google Expand Strategic Cloud Compute Commitments", domain="wsj.com", url="https://www.wsj.com/tech/ai/anthropic-cloud-commitments", published_date="Oct 14, 2026", freshness="3 weeks ago"),
        Source(id=5, title="Anthropic Strengthens AI Safety & Governance Leadership Team", domain="reuters.com", url="https://www.reuters.com/technology/anthropic-governance-appointments", published_date="Oct 28, 2026", freshness="3 days ago"),
    ]

    anthropic_attendees = [
        AttendeeProfile(
            name="Dario Amodei",
            role_title="Co-Founder & CEO",
            organization_tenure="Anthropic (4 yrs, ex-OpenAI VP Research)",
            recent_activity="Published landmark essay 'Machines of Loving Grace'; testified on frontier safety thresholds.",
            shared_interests="Constitutional AI, biological risk prevention, scalable compute clustering."
        ),
        AttendeeProfile(
            name="Daniela Amodei",
            role_title="Co-Founder & President",
            organization_tenure="Anthropic (4 yrs, ex-OpenAI VP Safety)",
            recent_activity="Spearheaded enterprise governance rollout and customer alignment councils.",
            shared_interests="Enterprise risk governance, organizational scale, responsible scaling policy."
        )
    ]

    anthropic_news = [
        GroundedClaim(
            id="ant_n1",
            statement="(Nov 04) Published updated safety disclosure warning that recursive self-improvement thresholds require urgent industry-wide auditing protocols.",
            category="news",
            citation_tag="[3]",
            evidence=EvidenceQuote(
                verbatim_quote="Anthropic disclosed that its AI systems may be approaching recursive self-improvement (RSI), a threshold creating new challenges for human oversight.",
                source_id=3,
                source_url="https://finance.yahoo.com/technology/ai/articles/safety-risk-anthropic-warns-ai-033013790.html",
                source_title="Anthropic Discloses Recursive Self-Improvement Safety Thresholds",
                freshness="Yesterday",
                status=VerificationStatus.CONFIRMED
            ),
            is_confirmed=True
        ),
        GroundedClaim(
            id="ant_n2",
            statement="(Oct 22) Released public beta of 'Computer Use' capability, allowing Claude 3.5 Sonnet to control mouse cursors, type keystrokes, and navigate software UI.",
            category="news",
            citation_tag="[2]",
            evidence=EvidenceQuote(
                verbatim_quote="Developers can now direct Claude to use computers the way people do—by looking at a screen, moving a cursor, clicking buttons, and typing text.",
                source_id=2,
                source_url="https://techcrunch.com/2026/10/22/anthropic-claude-computer-use",
                source_title="Anthropic Unveils Computer Use Feature for Claude 3.5 Sonnet",
                freshness="4 days ago",
                status=VerificationStatus.CONFIRMED
            ),
            is_confirmed=True
        ),
        GroundedClaim(
            id="ant_n3",
            statement="(Oct 14) Discrepancy detected: Reports cite AWS expanding cloud compute commitments between $4B and $8B.",
            category="news",
            citation_tag="[4]",
            evidence=EvidenceQuote(
                verbatim_quote="Amazon's total capital commitment was reported at $4 billion in secondary filings while earlier press leaks projected up to $8 billion.",
                source_id=4,
                source_url="https://www.wsj.com/tech/ai/anthropic-cloud-commitments",
                source_title="Amazon and Google Expand Strategic Cloud Compute Commitments",
                freshness="3 weeks ago",
                status=VerificationStatus.CONFLICT_DETECTED,
                conflict_note="Discrepancy: WSJ reports $4B confirmed vs earlier analyst speculation of $8B."
            ),
            is_confirmed=False,
            conflict_detected=True
        )
    ]

    anthropic_audit = HallucinationAuditLog(
        total_claims_verified=4,
        dropped_claims_count=1,
        dropped_claims=[
            DroppedClaimRecord(
                statement="Claude 4 architecture leak stating 10M context window...",
                drop_reason="Ungrounded Speculation: Claim originated on social media without engineering verification",
                raw_source="https://x.com/leaker_ai/status/894129"
            )
        ],
        queries_executed=["Anthropic safety disclosure", "Claude 3.5 Computer Use", "AWS Anthropic compute deal"],
        privacy_filtered_count=0,
        conflicts_detected=["Discrepancy detected between reported AWS investment total ($4B vs $8B)."],
        verification_score="100% Grounded"
    )

    anthropic_brief = BriefData(
        entity=anthropic_entity,
        tone_mode=ToneMode.DEEP_DIVE,
        meeting_goal="Evaluate deployment guardrails for Claude 3.5 Sonnet Computer Use in air-gapped enterprise environments.",
        attendees=anthropic_attendees,
        snapshot="Anthropic is an AI safety and research public-benefit company founded in 2021 by former OpenAI researchers Dario and Daniela Amodei. [1]\nThe company builds the frontier 'Claude' model family, focusing on Constitutional AI, steerability, and enterprise-grade reasoning capabilities. [1][2]",
        news_items=anthropic_news,
        hires_departures=[
            GroundedClaim(
                id="ant_h1",
                statement="(Oct 28) Recruited senior governance advisors from UK AI Safety Institute to head international alignment evaluation teams.",
                category="hires_departures",
                citation_tag="[5]",
                evidence=EvidenceQuote(
                    verbatim_quote="Key appointments from national safety institutes strengthen Anthropic's alignment and policy red-teaming teams.",
                    source_id=5,
                    source_url="https://www.reuters.com/technology/anthropic-governance-appointments",
                    source_title="Anthropic Strengthens AI Safety & Governance Leadership Team",
                    freshness="3 days ago",
                    status=VerificationStatus.CONFIRMED
                ),
                is_confirmed=True
            )
        ],
        launches_funding=[
            GroundedClaim(
                id="ant_l1",
                statement="(Oct 22) Released updated Claude 3.5 Sonnet with state-of-the-art coding and computer control API in public beta.",
                category="launches_funding",
                citation_tag="[2]",
                evidence=EvidenceQuote(
                    verbatim_quote="Claude 3.5 Sonnet is the first frontier model to offer computer use in public beta.",
                    source_id=2,
                    source_url="https://techcrunch.com/2026/10/22/anthropic-claude-computer-use",
                    source_title="Anthropic Unveils Computer Use Feature for Claude 3.5 Sonnet",
                    freshness="4 days ago",
                    status=VerificationStatus.CONFIRMED
                ),
                is_confirmed=True
            )
        ],
        executive_bullets=[
            "Strategic Intent: Establish secure enterprise sandbox architecture for Claude Computer Use deployment. [2]",
            "Material Catalyst: Launch of Computer Use on Oct 22 unlocks automated desktop task execution for internal teams. [2]",
            "Key Risk: Security guardrails against prompt injection and unauthorized execution on internal networks require dedicated audits.",
            "Operational Debate: Evaluate AWS Trainium vs Google TPU cluster allocation based on reported compute deal terms. [4]",
            "Decision Needed: Approve pilot terms and initiate red-team vulnerability testing before production rollout."
        ],
        deep_dive_context={
            "historical_context": "Anthropic was structured as a Long-Term Benefit Trust to insulate research decisions from purely commercial pressures, with a governing charter ensuring safety evaluations precede frontier deployment.",
            "key_debates": [
                "Computer Use Execution: Sandboxed virtual machines vs direct OS agent deployment.",
                "Discrepancy in Compute Allocation: Resolving conflicting reports on AWS infrastructure commitments ($4B vs $8B).",
                "Recursive Self-Improvement: Establishing formal thresholds where model-generated improvements must pause for human review."
            ],
            "strategic_outcomes": [
                "Sign mutual agreement for custom zero-data-retention air-gapped deployment.",
                "Establish bi-weekly technical security sync between engineering teams."
            ]
        },
        goal_aware_questions=[
            "Given our goal of deploying Computer Use in air-gapped environments, what client-side sandboxing architectures have proved most resilient against prompt injection?",
            "How does your recent RSI safety disclosure impact model version stability and update cadences for enterprise SLA agreements?",
            "Regarding conflicting compute allocation reports ($4B vs $8B), what dedicated inference capacity can be guaranteed for our enterprise workloads?"
        ],
        sources=anthropic_sources,
        audit_panel=anthropic_audit,
        quiet_entity_note=None,
        stats={"total_sources": 5, "total_verified_claims": 5, "dropped_claims": 1}
    )

    # ==========================================
    # 3. ACME HEALTH (Quiet-Entity Demo)
    # ==========================================
    acme_entity = ResolvedEntity(
        raw_input="Acme Health Tech",
        name="Acme Health Tech",
        entity_type=EntityType.COMPANY,
        role_or_industry="Regional Healthcare IT & Diagnostics",
        meeting_time=now + timedelta(days=3, hours=11),
        window_start=w_start,
        window_end=w_end,
        window_display=w_str
    )

    acme_sources = [
        Source(id=1, title="Acme Health Corporate Directory", domain="acmehealth.example.com", url="https://acmehealth.example.com/about", published_date="2025", freshness="Over 1 year ago")
    ]

    acme_attendees = [
        AttendeeProfile(
            name="Dr. Karen Vance",
            role_title="Medical Director",
            organization_tenure="Acme Health (3 yrs)",
            recent_activity="No public posts or announcements in the last 30 days.",
            shared_interests="Clinical compliance, HIPAA auditing.",
            is_quiet_entity=True
        )
    ]

    acme_audit = HallucinationAuditLog(
        total_claims_verified=0,
        dropped_claims_count=3,
        dropped_claims=[
            DroppedClaimRecord(
                statement="Acme Health alleged hospital acquisition...",
                drop_reason="Scope Violation: Article dated March 2024 (over 2 years old, outside 30-day scope)",
                raw_source="https://local-health-news-archive.com/2024"
            ),
            DroppedClaimRecord(
                statement="Rumored telehealth expansion...",
                drop_reason="Ungrounded: No factual backing found in public sources",
                raw_source="https://unverified-health-rumors.org"
            ),
            DroppedClaimRecord(
                statement="Dr. Vance personal community foundation...",
                drop_reason="Privacy Guardrail: Non-professional personal information filtered",
                raw_source="https://county-charity-list.org"
            )
        ],
        queries_executed=["Acme Health news", "Acme Health hires", "Acme Health launches"],
        privacy_filtered_count=1,
        conflicts_detected=[],
        verification_score="0% (Quiet Entity)"
    )

    acme_brief = BriefData(
        entity=acme_entity,
        tone_mode=ToneMode.STANDARD,
        meeting_goal="Evaluate clinic pilot and confirm compliance certifications.",
        attendees=acme_attendees,
        snapshot="Acme Health Tech operates healthcare IT systems for regional specialty clinics. [1]",
        news_items=[],
        hires_departures=[],
        launches_funding=[],
        executive_bullets=[
            "Strategic Intent: Confirm regional clinic pilot scope and establish direct technical milestones.",
            "Operational Status: Entity has maintained quiet status with no major public announcements in the last 30 days.",
            "Key Risk: Absence of recent public telemetry requires direct verification of compliance credentials in meeting.",
            "Decision Needed: Secure confirmation of clinic pilot timeline and sign off on data integration specs.",
            "Next Steps: Agree on follow-up technical architecture review within two weeks."
        ],
        goal_aware_questions=[
            "Given the absence of major public announcements in the last 30 days, what internal technical milestones have been your primary focus this quarter?",
            "To confirm our clinic pilot goal, what specific EHR integration capabilities are currently live across your partner clinics?"
        ],
        sources=acme_sources,
        audit_panel=acme_audit,
        quiet_entity_note="Nothing notable in the last 30 days for Acme Health Tech.",
        stats={"total_sources": 1, "total_verified_claims": 0, "dropped_claims": 3}
    )

    return {
        "Stripe": stripe_brief,
        "Anthropic": anthropic_brief,
        "Acme Health (Quiet Entity)": acme_brief
    }
