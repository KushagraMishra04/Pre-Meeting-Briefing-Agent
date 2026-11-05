"""
CLI Test Script for Pre-Meeting Briefing Agent Pipeline.
Tests the full flow from input entity to one-page PDF generation.
"""
import sys
import os
from datetime import datetime, timedelta

from src.pipeline import BriefingPipeline


def test_cli():
    entity_name = "Stripe"
    meeting_time = datetime.now() + timedelta(days=2)

    print(f"=== Testing Pre-Meeting Briefing Agent ===")
    print(f"Entity: {entity_name}")
    print(f"Meeting Time: {meeting_time.strftime('%Y-%m-%d %H:%M')}")
    print("------------------------------------------")

    pipeline = BriefingPipeline()

    def progress_callback(msg, pct):
        print(f"[{int(pct*100)}%] {msg}")

    result = pipeline.run(
        entity_name=entity_name,
        meeting_time=meeting_time,
        on_progress=progress_callback
    )

    print("\n=== GENERATED BRIEF PREVIEW ===")
    print(result.markdown)
    print("\n=== PIPELINE STATS ===")
    print(f"Total Sources Retrieved: {len(result.brief.sources)}")
    print(f"Total Verified Claims: {len(result.verified_claims)}")
    print(f"PDF Size: {len(result.pdf_bytes)} bytes")

    pdf_filename = "test_output_brief.pdf"
    with open(pdf_filename, "wb") as f:
        f.write(result.pdf_bytes)
    print(f"Saved test PDF to: {os.path.abspath(pdf_filename)}")


if __name__ == "__main__":
    test_cli()
