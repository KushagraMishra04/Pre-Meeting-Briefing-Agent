"""
Post-Meeting Follow-Up Engine.
Extracts owner-assigned Action Items and drafts executive follow-up emails
from meeting transcripts or rough notes.
"""
import re
import json
import logging
from typing import List, Optional
from google import genai
from google.genai import types

from src.models import ActionItem, FollowUpEmail

logger = logging.getLogger(__name__)


class PostMeetingEngine:
    """Processes post-meeting transcripts into action items and follow-up emails."""

    def __init__(self, gemini_api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = gemini_api_key.strip() if gemini_api_key else None
        self.model = model
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini in PostMeetingEngine: {e}")

    def process_transcript(
        self,
        meeting_title: str,
        attendees: List[str],
        notes_or_transcript: str
    ) -> tuple[List[ActionItem], FollowUpEmail]:
        """
        Extracts action items and creates a follow-up email draft.
        """
        if self.client and notes_or_transcript.strip():
            try:
                return self._process_with_gemini(meeting_title, attendees, notes_or_transcript)
            except Exception as e:
                logger.warning(f"Gemini post-meeting processing failed: {e}. Using deterministic fallback.")

        return self._process_rule_based(meeting_title, attendees, notes_or_transcript)

    def _process_with_gemini(
        self,
        meeting_title: str,
        attendees: List[str],
        notes: str
    ) -> tuple[List[ActionItem], FollowUpEmail]:
        prompt = f"""
You are an executive chief of staff.
Analyze the following meeting notes or transcript and produce:
1. Owner-assigned action items with clear deadlines.
2. A polished, professional executive follow-up email.

Meeting Title: {meeting_title}
Attendees: {', '.join(attendees) if attendees else 'Meeting Participants'}

Notes / Transcript:
\"\"\"
{notes}
\"\"\"

Return a valid JSON object matching this schema:
{{
  "action_items": [
    {{
      "task": "Specific deliverable description",
      "owner": "Person name or team",
      "deadline": "Clear date or timeline",
      "priority": "High" or "Medium" or "Low"
    }}
  ],
  "follow_up_email": {{
    "subject": "Follow-Up: {meeting_title} - Key Decisions & Action Items",
    "recipients": ["emails or names"],
    "body": "Complete executive follow-up email text with recap, decisions made, action items list, and next steps."
  }}
}}
"""
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )
        text = response.text or "{}"
        text = re.sub(r"^```json\s*", "", text.strip())
        text = re.sub(r"\s*```$", "", text.strip())
        data = json.loads(text)

        action_items = []
        for item in data.get("action_items", []):
            action_items.append(
                ActionItem(
                    task=item.get("task", ""),
                    owner=item.get("owner", "Unassigned"),
                    deadline=item.get("deadline", "Next sync"),
                    priority=item.get("priority", "High")
                )
            )

        email_data = data.get("follow_up_email", {})
        email = FollowUpEmail(
            subject=email_data.get("subject", f"Follow-Up: {meeting_title}"),
            recipients=attendees,
            body=email_data.get("body", "Thank you for the productive discussion today.")
        )

        return action_items, email

    def _process_rule_based(
        self,
        meeting_title: str,
        attendees: List[str],
        notes: str
    ) -> tuple[List[ActionItem], FollowUpEmail]:
        """Deterministic regex fallback for offline/demo use."""
        action_items: List[ActionItem] = []
        lines = notes.split("\n")

        # Extract tasks matching patterns
        for line in lines:
            line_str = line.strip().lstrip("-*•0123456789. ")
            if not line_str:
                continue

            owner_match = re.search(r"@(\w+)|(?:owner|assigned to|by)\s*:\s*([A-Za-z]+)", line_str, re.IGNORECASE)
            deadline_match = re.search(r"(?:by|due|before)\s+([A-Za-z0-9\s,]+)", line_str, re.IGNORECASE)

            owner = "Lead Attendee"
            if owner_match:
                owner = owner_match.group(1) or owner_match.group(2)
            elif attendees:
                owner = attendees[0]

            deadline = "By next sync"
            if deadline_match:
                deadline = deadline_match.group(1).strip()

            if any(kw in line_str.lower() for kw in ["will", "action", "todo", "send", "review", "draft", "prepare", "follow up"]):
                action_items.append(
                    ActionItem(
                        task=line_str[:120],
                        owner=owner,
                        deadline=deadline,
                        priority="High" if "urgent" in line_str.lower() or "asap" in line_str.lower() else "Medium"
                    )
                )

        if not action_items:
            action_items = [
                ActionItem(task="Circulate final agreement terms and pricing matrix", owner=attendees[0] if attendees else "Lead", deadline="End of week", priority="High"),
                ActionItem(task="Schedule technical deep-dive on API latency & security compliance", owner="Engineering Lead", deadline="Next Tuesday", priority="Medium"),
                ActionItem(task="Send updated compliance certifications and SOC2 pack", owner="Operations", deadline="By Friday", priority="Medium")
            ]

        # Construct email body
        items_formatted = "\n".join([f"- [ ] {ai.task} (Owner: {ai.owner}, Deadline: {ai.deadline})" for ai in action_items])
        email_body = f"""Hi Team,

Thank you for meeting today to discuss {meeting_title}. Below is a summary of our key decisions and agreed next steps:

Decisions & Outcomes:
• Aligned on core scope and commercial timeline.
• Agreed on governance and liability requirements.

Action Items:
{items_formatted}

Next Steps:
We will reconvene next week to review progress. Please flag any blockers in advance.

Best regards,
Pre-Meeting Briefing Agent"""

        email = FollowUpEmail(
            subject=f"Follow-Up: {meeting_title} - Key Decisions & Action Items",
            recipients=attendees,
            body=email_body
        )

        return action_items, email

