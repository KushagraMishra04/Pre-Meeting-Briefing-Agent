"""
Comprehensive Unit Test Suite for Pre-Meeting Briefing Agent.
Covers:
1. Entity Resolver (Entity type detection, 30-day scope window, query planning)
2. Calendar Invite Parser (RFC 5545 .ics, plain-text invite, attendee & agenda extraction)
3. Trust & Safety Engine (Privacy guardrails, rumor vs confirmed, freshness, conflict detector, quiet entity)
4. Claim Extractor (Snippet decomposition, heuristic extraction, citation anchors)
5. Verifier & Hallucination Audit (URL grounding, citation deduplication, dropped claim logging, goal-aware questions)
6. Brief Generator (Executive 5 bullets, Standard Mode, Deep-Dive Mode, Click-to-Evidence anchors)
7. Since-Last-Brief Diff Engine (Recurring meeting delta isolation)
8. Post-Meeting Engine (Action items with owners/deadlines, follow-up email draft)
9. Ask-The-Brief Engine (Grounded Q&A with citation tags)
10. PDF Exporter (Unicode sanitization, Executive PDF rendering across all modes)
11. Demo Data Integrity (Stripe, Anthropic conflict flag, Acme Health quiet entity)
"""
import unittest
from datetime import datetime, timedelta, time
import re

from src.models import (
    ToneMode,
    EntityType,
    ResolvedEntity,
    SearchResult,
    Source,
    EvidenceQuote,
    GroundedClaim,
    AttendeeProfile,
    HallucinationAuditLog,
    DroppedClaimRecord,
    BriefData,
    ParsedCalendarInvite,
    SinceLastBriefDiff,
    ActionItem,
    FollowUpEmail,
    VerificationStatus,
)
from src.entity_resolver import EntityResolver
from src.calendar_parser import CalendarParser
from src.trust_safety import TrustSafetyEngine
from src.claim_extractor import ClaimExtractor, RawExtractedClaim
from src.verifier import Verifier
from src.brief_generator import BriefGenerator
from src.diff_engine import DiffEngine
from src.post_meeting import PostMeetingEngine
from src.ask_brief import AskBriefEngine
from src.pdf_exporter import PDFExporter, sanitize_text
from src.demo_data import get_demo_briefs


class TestEntityResolver(unittest.TestCase):
    """Unit tests for EntityResolver."""

    def test_detect_company_suffixes(self):
        self.assertEqual(EntityResolver.detect_entity_type("Stripe Inc")[0], EntityType.COMPANY)
        self.assertEqual(EntityResolver.detect_entity_type("OpenAI LLC")[0], EntityType.COMPANY)
        self.assertEqual(EntityResolver.detect_entity_type("Acme Technologies")[0], EntityType.COMPANY)

    def test_detect_person_titles(self):
        self.assertEqual(EntityResolver.detect_entity_type("CEO Patrick Collison")[0], EntityType.PERSON)
        self.assertEqual(EntityResolver.detect_entity_type("Dr. Jane Doe")[0], EntityType.PERSON)
        self.assertEqual(EntityResolver.detect_entity_type("CTO Greg Brockman")[0], EntityType.PERSON)

    def test_30_day_window_calculation(self):
        meeting_time = datetime(2026, 11, 20, 14, 0)
        resolved = EntityResolver.resolve("Stripe", meeting_time=meeting_time)
        expected_start = meeting_time - timedelta(days=30)
        self.assertEqual(resolved.meeting_time, meeting_time)
        self.assertEqual(resolved.window_start, expected_start)
        self.assertIn("Oct 21, 2026", resolved.window_display)
        self.assertIn("Nov 20, 2026", resolved.window_display)

    def test_search_queries_generated(self):
        resolved = EntityResolver.resolve("Anthropic")
        queries = EntityResolver.generate_queries(resolved)
        self.assertIn("snapshot", queries)
        self.assertIn("news", queries)
        self.assertIn("hires_departures", queries)
        self.assertIn("launches_funding", queries)
        for q in queries.values():
            self.assertIn("Anthropic", q)


class TestCalendarParser(unittest.TestCase):
    """Unit tests for CalendarParser."""

    def test_parse_ics_rfc5545(self):
        ics_data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example Corp//EN
BEGIN:VEVENT
SUMMARY:Stripe Partnership Strategy Session
DTSTART:20261118T150000Z
DTEND:20261118T160000Z
DESCRIPTION:Align on enterprise payment checkout roadmap and agentic billing protocols.
ORGANIZER;CN=Patrick Collison:mailto:patrick@stripe.com
ATTENDEE;CN=Will Gaybrick:mailto:will@stripe.com
ATTENDEE;CN=Sarah Chen:mailto:sarah@partner.com
END:VEVENT
END:VCALENDAR"""
        parsed = CalendarParser.parse_ics(ics_data)
        self.assertEqual(parsed.title, "Stripe Partnership Strategy Session")
        self.assertIn("checkout roadmap", parsed.goal_agenda)
        self.assertEqual(len(parsed.attendees), 2)
        self.assertIn("Will Gaybrick", parsed.attendees)
        self.assertIn("Sarah Chen", parsed.attendees)

    def test_parse_plain_text_invite(self):
        plain_invite = """Subject: Acme Health AI Pilot Alignment
When: Friday, November 20, 2026 at 2:00 PM
Attendees: Dr. Elena Vance (elena@acmehealth.com), Marcus Brody (marcus@acmehealth.com)
Agenda: Discuss HIPAA compliance audit results and pilot go-live schedule for Q1."""
        parsed = CalendarParser.parse_plain_text(plain_invite)
        self.assertEqual(parsed.title, "Acme Health AI Pilot Alignment")
        self.assertIn("HIPAA compliance", parsed.goal_agenda)
        self.assertEqual(len(parsed.attendees), 2)
        self.assertIn("Dr. Elena Vance", parsed.attendees)
        self.assertIn("Marcus Brody", parsed.attendees)

    def test_sample_invites_available(self):
        samples = CalendarParser.get_sample_invites()
        self.assertGreaterEqual(len(samples), 3)
        self.assertTrue(any("Stripe" in k for k in samples))
        self.assertTrue(any("Anthropic" in k for k in samples))


class TestTrustSafetyEngine(unittest.TestCase):
    """Unit tests for Trust & Safety guardrails, freshness, conflicts, and quiet entity."""

    def test_privacy_guardrail_blocks_sensitive_personal_data(self):
        sensitive_claims = [
            "Executive's spouse filed for divorce yesterday.",
            "Home address and personal vacation plans were leaked online.",
            "CEO children attend private school in California.",
            "CFO has a severe medical condition requiring hospital stay."
        ]
        for claim in sensitive_claims:
            is_safe, reason = TrustSafetyEngine.audit_privacy_guardrail(claim)
            self.assertFalse(is_safe, f"Should have blocked: {claim}")
            self.assertIsNotNone(reason)

    def test_privacy_guardrail_permits_professional_data(self):
        professional_claims = [
            "Company reported $14 billion in net revenue for fiscal year.",
            "Appointed Sarah Chen as Chief Product Officer to oversee enterprise rollout.",
            "Announced a $500 million Series D funding round at a $10 billion valuation."
        ]
        for claim in professional_claims:
            is_safe, reason = TrustSafetyEngine.audit_privacy_guardrail(claim)
            self.assertTrue(is_safe, f"Should have permitted: {claim}")
            self.assertIsNone(reason)

    def test_freshness_calculation(self):
        ref_time = datetime(2026, 11, 20, 10, 0)
        self.assertEqual(TrustSafetyEngine.calculate_freshness("2026-11-20", ref_time), "Today / Upcoming")
        self.assertEqual(TrustSafetyEngine.calculate_freshness("2026-11-19", ref_time), "Yesterday")
        self.assertEqual(TrustSafetyEngine.calculate_freshness("2026-11-16", ref_time), "4 days ago")
        self.assertEqual(TrustSafetyEngine.calculate_freshness("2026-11-10", ref_time), "1 week ago")
        self.assertEqual(TrustSafetyEngine.calculate_freshness("", ref_time), "Recent (< 30 days)")

    def test_rumor_vs_confirmed_classification(self):
        rumor_text = "According to anonymous sources, the acquisition talks may fall through."
        confirmed_text = "Company officially registered S-1 filing with the SEC."
        
        status_rumor = TrustSafetyEngine.classify_rumor_vs_confirmed(rumor_text, "randomblog.com")
        self.assertEqual(status_rumor, VerificationStatus.REPORTED_RUMOR)

        status_confirmed = TrustSafetyEngine.classify_rumor_vs_confirmed(confirmed_text, "sec.gov")
        self.assertEqual(status_confirmed, VerificationStatus.CONFIRMED)

    def test_conflict_detection(self):
        quote = EvidenceQuote(
            verbatim_quote="Funding details verified in public filing.",
            source_id=1,
            source_url="https://source.com",
            source_title="Source A",
            freshness="Recent"
        )
        claim1 = GroundedClaim(
            id="c1",
            statement="Anthropic raised $2.5 billion in strategic investment.",
            category="launches_funding",
            citation_tag="[1]",
            evidence=quote
        )
        claim2 = GroundedClaim(
            id="c2",
            statement="Anthropic completed financing round at $4.0 billion valuation.",
            category="launches_funding",
            citation_tag="[2]",
            evidence=quote
        )
        conflicts = TrustSafetyEngine.detect_conflicts([claim1, claim2])
        self.assertGreater(len(conflicts), 0)
        self.assertTrue(any("Discrepancy" in c for c in conflicts))

    def test_quiet_entity_handling(self):
        msg = TrustSafetyEngine.evaluate_quiet_entity("Acme Health Tech", claims_count=0)
        self.assertEqual(msg, "Nothing notable in the last 30 days for Acme Health Tech.")
        self.assertIsNone(TrustSafetyEngine.evaluate_quiet_entity("Stripe", claims_count=5))


class TestClaimExtractor(unittest.TestCase):
    """Unit tests for ClaimExtractor."""

    def test_heuristic_extraction(self):
        extractor = ClaimExtractor(gemini_api_key=None)
        entity = EntityResolver.resolve("Stripe")
        results = [
            SearchResult(
                title="Stripe introduces Agentic Commerce Suite",
                url="https://stripe.com/news/agentic",
                snippet="Stripe announced an autonomous checkout protocol handling agentic transactions. The service launched globally today.",
                published_date="2026-11-02",
                query_category="launches_funding"
            )
        ]
        claims = extractor._extract_heuristic(entity, results)
        self.assertGreater(len(claims), 0)
        self.assertIn("Stripe", claims[0].statement)
        self.assertEqual(claims[0].category, "launches_funding")
        self.assertIsNotNone(claims[0].verbatim_quote)


class TestVerifierAndAudit(unittest.TestCase):
    """Unit tests for Verifier and Hallucination Audit Panel."""

    def test_verification_and_citation_numbering(self):
        verifier = Verifier()
        entity = EntityResolver.resolve("Stripe")
        search_results = [
            SearchResult(
                title="Stripe Press Release",
                url="https://stripe.com/news/1",
                snippet="Stripe expands agentic billing to 45 countries worldwide.",
                published_date="2026-11-05",
                query_category="news"
            )
        ]
        raw_claims = [
            RawExtractedClaim(
                category="news",
                statement="Stripe expands agentic billing to 45 countries worldwide.",
                verbatim_quote="Stripe expands agentic billing to 45 countries worldwide.",
                date="2026-11-05",
                source_url="https://stripe.com/news/1",
                source_title="Stripe Press Release"
            ),
            # Hallucinated claim from unretrieved URL
            RawExtractedClaim(
                category="news",
                statement="Stripe acquired a bank in France.",
                verbatim_quote="Stripe acquired a bank in France.",
                date="2026-11-05",
                source_url="https://fake-news.xyz/unverified",
                source_title="Fake News"
            )
        ]

        grounded, sources, audit = verifier.verify_and_ground(raw_claims, search_results, entity)

        self.assertEqual(len(grounded), 1)
        self.assertEqual(grounded[0].citation_tag, "[1]")
        self.assertEqual(len(sources), 1)

        # Audit panel verification
        self.assertEqual(audit.total_claims_verified, 1)
        self.assertEqual(audit.dropped_claims_count, 1)
        self.assertEqual(len(audit.dropped_claims), 1)
        self.assertIn("ungrounded", audit.dropped_claims[0].drop_reason.lower())

    def test_goal_aware_questions_fallback(self):
        verifier = Verifier()
        entity = EntityResolver.resolve("Stripe")
        questions = verifier.generate_goal_aware_questions(
            entity=entity,
            claims=[],
            meeting_goal="Negotiate enterprise volume tiers for agentic checkout protocol"
        )
        self.assertGreaterEqual(len(questions), 3)
        self.assertTrue(any("Negotiate enterprise volume tiers" in q for q in questions))


class TestBriefGenerator(unittest.TestCase):
    """Unit tests for BriefGenerator across Tone Modes."""

    def setUp(self):
        self.generator = BriefGenerator()
        self.entity = EntityResolver.resolve("Stripe")
        quote = EvidenceQuote(
            verbatim_quote="Stripe powers $1 trillion in commerce annually.",
            source_id=1,
            source_url="https://stripe.com",
            source_title="Stripe Annual Review",
            freshness="2 days ago"
        )
        self.claims = [
            GroundedClaim(
                id="c1",
                statement="Stripe surpassed $1 trillion in total payment volume.",
                category="news",
                citation_tag="[1]",
                evidence=quote
            )
        ]

    def test_executive_mode_exactly_5_bullets(self):
        bullets = self.generator.synthesize_executive_bullets(
            entity=self.entity,
            claims=self.claims,
            meeting_goal="Volume negotiation"
        )
        self.assertEqual(len(bullets), 5, f"Executive mode must output EXACTLY 5 bullets, got {len(bullets)}")

    def test_click_to_evidence_bracket_anchors(self):
        brief = self.generator.generate(
            entity=self.entity,
            grounded_claims=self.claims,
            sources=[Source(id=1, title="Stripe News", url="https://stripe.com", domain="stripe.com", freshness="2 days ago")],
            audit_log=HallucinationAuditLog(total_claims_verified=1, dropped_claims_count=0),
            tone_mode=ToneMode.STANDARD
        )
        markdown = self.generator.to_markdown(brief)
        self.assertIn("[1]", markdown)
        self.assertIn("Source Quote:", markdown)
        self.assertIn("Hallucination Audit Panel", markdown)


class TestDiffEngine(unittest.TestCase):
    """Unit tests for Since-Last-Brief DiffEngine."""

    def test_compute_diff_with_previous_notes(self):
        quote = EvidenceQuote(
            verbatim_quote="Verified partnership quote.",
            source_id=1,
            source_url="https://source.com",
            source_title="Source",
            freshness="Recent"
        )
        current_news = [
            GroundedClaim(id="d1", statement="Stripe introduced autonomous checkout tokens.", category="news", citation_tag="[1]", evidence=quote),
            GroundedClaim(id="d2", statement="Stripe renewed partnership with Amazon AWS.", category="news", citation_tag="[2]", evidence=quote),
        ]
        previous_notes = "In last month's sync, we thoroughly reviewed Stripe renewed partnership with Amazon AWS."

        diff = DiffEngine.compute_diff(
            current_news=current_news,
            current_hires=[],
            current_launches=[],
            previous_notes_or_brief=previous_notes
        )
        self.assertTrue(diff.has_diff)
        self.assertTrue(any("autonomous checkout tokens" in d for d in diff.new_developments))


class TestPostMeetingEngine(unittest.TestCase):
    """Unit tests for PostMeetingEngine."""

    def test_rule_based_action_item_extraction(self):
        engine = PostMeetingEngine()
        transcript = """
        Patrick will review the enterprise tier agreement by next Friday.
        Will will follow up with legal regarding data residency by Nov 25.
        Action: Team needs to schedule architecture review by end of month.
        """
        actions, email = engine.process_transcript(
            meeting_title="Stripe & Partner Strategy Sync",
            attendees=["Patrick Collison", "Will Gaybrick"],
            notes_or_transcript=transcript
        )
        self.assertGreaterEqual(len(actions), 2)
        self.assertIsNotNone(email.subject)
        self.assertIn("Stripe", email.subject)
        self.assertIn("Hi Team", email.body)


class TestAskBriefEngine(unittest.TestCase):
    """Unit tests for AskBriefEngine."""

    def test_semantic_qna_with_citations(self):
        engine = AskBriefEngine()
        briefs = get_demo_briefs()
        stripe_brief = briefs["Stripe"]

        answer = engine.answer_question("What did Stripe announce regarding stablecoin payments?", stripe_brief)
        self.assertIn("stablecoin", answer.lower())
        self.assertIn("[4]", answer)

    def test_empty_query_handling(self):
        engine = AskBriefEngine()
        briefs = get_demo_briefs()
        answer = engine.answer_question("", briefs["Stripe"])
        self.assertIn("Please enter a question", answer)


class TestPDFExporter(unittest.TestCase):
    """Unit tests for PDFExporter."""

    def test_unicode_sanitizer(self):
        raw = "• Item with smart “quotes”, em—dash, and ellipses…"
        sanitized = sanitize_text(raw)
        self.assertNotIn("•", sanitized)
        self.assertNotIn("“", sanitized)
        self.assertNotIn("—", sanitized)

    def test_pdf_generation_valid_bytes(self):
        briefs = get_demo_briefs()
        pdf_bytes = PDFExporter.render(briefs["Stripe"])
        self.assertTrue(isinstance(pdf_bytes, bytes))
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 1000)

    def test_pdf_generation_all_tone_modes(self):
        briefs = get_demo_briefs()
        for name, brief in briefs.items():
            pdf_bytes = PDFExporter.render(brief)
            self.assertTrue(pdf_bytes.startswith(b"%PDF"))


class TestDemoDataIntegrity(unittest.TestCase):
    """Unit tests for pre-computed rich demo briefs."""

    def test_demo_briefs_coverage(self):
        briefs = get_demo_briefs()
        self.assertIn("Stripe", briefs)
        self.assertIn("Anthropic", briefs)
        self.assertIn("Acme Health (Quiet Entity)", briefs)

    def test_acme_health_quiet_entity(self):
        briefs = get_demo_briefs()
        acme = briefs["Acme Health (Quiet Entity)"]
        self.assertEqual(len(acme.news_items), 0)
        self.assertIn("Nothing notable in the last 30 days", acme.quiet_entity_note)


if __name__ == "__main__":
    unittest.main()
