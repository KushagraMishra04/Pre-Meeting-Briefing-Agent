"""
CLI Test Script for Pre-Meeting Briefing Agent Pipeline.
Tests the full flow from input entity, tone mode, and goal to one-page PDF generation.
"""
import sys
import os
from datetime import datetime, timedelta

from src.models import ToneMode
from src.pipeline import BriefingPipeline


def test_cli():
    entity_name = "Stripe"
    meeting_time = datetime.now() + timedelta(days=2)
    meeting_goal = "Negotiate enterprise volume tiers for Agentic Commerce Protocol"

    print(f"=== Testing Pre-Meeting Briefing Agent ===")
    print(f"Entity: {entity_name}")
    print(f"Meeting Time: {meeting_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"Meeting Goal: {meeting_goal}")
    print("------------------------------------------")

    pipeline = BriefingPipeline()

    def progress_callback(msg, pct):
        print(f"[{int(pct*100)}%] {msg}")

    result = pipeline.run(
        entity_name=entity_name,
        meeting_time=meeting_time,
        meeting_goal=meeting_goal,
        tone_mode=ToneMode.STANDARD,
        attendee_names=["Patrick Collison", "Will Gaybrick"],
        on_progress=progress_callback
    )

    print("\n=== GENERATED BRIEF PREVIEW ===")
    print(result.markdown)
    print("\n=== PIPELINE STATS ===")
    print(f"Total Sources Retrieved: {len(result.brief.sources)}")
    print(f"Total Grounded Claims: {len(result.grounded_claims)}")
    print(f"Dropped Claims Count: {result.brief.audit_panel.dropped_claims_count}")
    print(f"PDF Size: {len(result.pdf_bytes)} bytes")

    pdf_filename = "test_output_brief.pdf"
    with open(pdf_filename, "wb") as f:
        f.write(result.pdf_bytes)
    print(f"Saved test PDF to: {os.path.abspath(pdf_filename)}")


if __name__ == "__main__":
    test_cli()
