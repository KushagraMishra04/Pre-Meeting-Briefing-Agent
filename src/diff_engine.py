"""
Since-Last-Brief Diff Engine.
Calculates delta changes between consecutive meetings or past notes,
highlighting only new developments for recurring meetings.
"""
from typing import List, Optional
from src.models import SinceLastBriefDiff, GroundedClaim


class DiffEngine:
    """Computes incremental intelligence deltas since the prior meeting."""

    @classmethod
    def compute_diff(
        cls,
        current_news: List[GroundedClaim],
        current_hires: List[GroundedClaim],
        current_launches: List[GroundedClaim],
        previous_notes_or_brief: Optional[str] = None
    ) -> SinceLastBriefDiff:
        """
        Isolates only new developments not mentioned in previous meeting notes.
        """
        if not previous_notes_or_brief or not previous_notes_or_brief.strip():
            # If no previous notes provided, all recent verified items are new developments
            new_devs = [c.statement for c in current_news[:3]]
            new_hires = [c.statement for c in current_hires[:2]]
            new_launches = [c.statement for c in current_launches[:2]]
            return SinceLastBriefDiff(
                previous_meeting_date="Previous Sync (30 days ago)",
                new_developments=new_devs,
                leadership_updates=new_hires,
                product_shifts=new_launches,
                has_diff=bool(new_devs or new_hires or new_launches)
            )

        prev_lower = previous_notes_or_brief.lower()

        # Filter out anything already discussed in previous notes
        delta_news = [
            c.statement for c in current_news
            if not any(word in prev_lower for word in c.statement.lower().split()[:4])
        ]

        delta_hires = [
            c.statement for c in current_hires
            if not any(word in prev_lower for word in c.statement.lower().split()[:4])
        ]

        delta_launches = [
            c.statement for c in current_launches
            if not any(word in prev_lower for word in c.statement.lower().split()[:4])
        ]

        return SinceLastBriefDiff(
            previous_meeting_date="Last Sync",
            new_developments=delta_news[:3] if delta_news else ["No new external news since last sync."],
            leadership_updates=delta_hires[:2] if delta_hires else ["No leadership changes since last sync."],
            product_shifts=delta_launches[:2] if delta_launches else ["No new product launches since last sync."],
            has_diff=True
        )

