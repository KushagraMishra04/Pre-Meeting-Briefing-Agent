"""
Calendar Invite Parser Module.
Parses .ics files, RFC 5545 calendar data, and free-form meeting invites
to extract title, datetime, goal/agenda, and attendee lists.
"""
import re
from datetime import datetime, timedelta
from typing import List, Optional
from dateutil import parser as date_parser

from src.models import ParsedCalendarInvite


class CalendarParser:
    """Parses .ics file contents and plain-text meeting invitations."""

    @classmethod
    def parse_ics(cls, ics_content: str) -> ParsedCalendarInvite:
        """Parses standard iCalendar (.ics) RFC 5545 format text."""
        lines = ics_content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        
        # Unfold lines that start with space or tab
        unfolded_lines = []
        for line in lines:
            if line.startswith(" ") or line.startswith("\t"):
                if unfolded_lines:
                    unfolded_lines[-1] += line[1:]
            else:
                unfolded_lines.append(line)

        title = "Scheduled Meeting"
        dt_start = datetime.now() + timedelta(days=1, hours=10)
        dt_end = None
        description = "Review progress and align on next steps."
        location = None
        organizer = None
        attendees: List[str] = []

        for line in unfolded_lines:
            line_str = line.strip()
            if line_str.startswith("SUMMARY:"):
                title = line_str[8:].strip()
            elif line_str.startswith("DTSTART"):
                val = line_str.split(":")[-1].strip()
                try:
                    dt_start = date_parser.parse(val)
                except Exception:
                    pass
            elif line_str.startswith("DTEND"):
                val = line_str.split(":")[-1].strip()
                try:
                    dt_end = date_parser.parse(val)
                except Exception:
                    pass
            elif line_str.startswith("DESCRIPTION:"):
                description = line_str[12:].replace("\\n", "\n").replace("\\,", ",").strip()
            elif line_str.startswith("LOCATION:"):
                location = line_str[9:].strip()
            elif line_str.startswith("ORGANIZER"):
                organizer = line_str.split(":")[-1].strip()
            elif line_str.startswith("ATTENDEE"):
                # Extract CN parameter or email
                cn_match = re.search(r"CN=([^;:]+)", line_str)
                email_match = re.search(r"mailto:([^\s;>]+)", line_str, re.IGNORECASE)
                if cn_match:
                    attendees.append(cn_match.group(1).replace('"', '').strip())
                elif email_match:
                    attendees.append(email_match.group(1).strip())
                else:
                    attendees.append(line_str.split(":")[-1].strip())

        return ParsedCalendarInvite(
            title=title,
            meeting_time=dt_start,
            end_time=dt_end,
            goal_agenda=description,
            location_or_link=location,
            organizer=organizer,
            attendees=list(dict.fromkeys(attendees)),  # deduplicate
            raw_text=ics_content[:500]
        )

    @classmethod
    def parse_plain_text(cls, text: str) -> ParsedCalendarInvite:
        """Parses human-copied calendar invites (e.g. from Google Calendar, Outlook, Zoom)."""
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        if not lines:
            return ParsedCalendarInvite(
                title="Strategy Meeting",
                meeting_time=datetime.now() + timedelta(days=1),
                goal_agenda="Executive alignment and review."
            )

        title = lines[0]
        meeting_time = datetime.now() + timedelta(days=1)
        goal_agenda = "Strategic review and decision-making."
        attendees: List[str] = []
        location = None

        # Look for explicit keywords
        joined_text = "\n".join(lines)

        # Subject / Title
        subj_match = re.search(r"(?:subject|title|meeting):\s*(.+)", joined_text, re.IGNORECASE)
        if subj_match:
            title = subj_match.group(1).strip()

        # Date / Time
        date_match = re.search(r"(?:when|date|time):\s*(.+)", joined_text, re.IGNORECASE)
        if date_match:
            try:
                meeting_time = date_parser.parse(date_match.group(1).strip(), fuzzy=True)
            except Exception:
                pass
        else:
            # Check line 2 or 3 for date
            for l in lines[1:4]:
                try:
                    parsed = date_parser.parse(l, fuzzy=True)
                    if parsed:
                        meeting_time = parsed
                        break
                except Exception:
                    continue

        # Agenda / Goal
        agenda_match = re.search(r"(?:agenda|goal|purpose|objective):\s*(.+)", joined_text, re.IGNORECASE)
        if agenda_match:
            goal_agenda = agenda_match.group(1).strip()

        # Attendees
        att_match = re.search(r"(?:attendees|participants|who):\s*(.+)", joined_text, re.IGNORECASE)
        if att_match:
            raw_atts = att_match.group(1).split(",")
            attendees = [a.strip() for a in raw_atts if a.strip()]
        else:
            # Look for email patterns
            emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", joined_text)
            if emails:
                attendees = list(dict.fromkeys(emails))

        # Location or Link
        loc_match = re.search(r"(https?://\S+|zoom\.us/\S+|meet\.google\.com/\S+)", joined_text, re.IGNORECASE)
        if loc_match:
            location = loc_match.group(1).strip()

        return ParsedCalendarInvite(
            title=title,
            meeting_time=meeting_time,
            goal_agenda=goal_agenda,
            location_or_link=location,
            attendees=attendees,
            raw_text=text[:500]
        )

    @classmethod
    def get_sample_invites(cls) -> dict:
        """Returns rich sample calendar invites for instant 1-click testing."""
        return {
            "Stripe Enterprise Partnership": (
                "BEGIN:VCALENDAR\n"
                "VERSION:2.0\n"
                "SUMMARY:Stripe Commercial & Agentic Commerce Review\n"
                "DTSTART:20261112T150000Z\n"
                "DTEND:20261112T160000Z\n"
                "ORGANIZER:mailto:exec-assistant@enterprise.com\n"
                "ATTENDEE;CN=\"Patrick Collison\":mailto:patrick@stripe.com\n"
                "ATTENDEE;CN=\"Will Gaybrick\":mailto:will@stripe.com\n"
                "ATTENDEE;CN=\"Sarah Jenkins (VP Eng)\":mailto:sarah@enterprise.com\n"
                "LOCATION:https://meet.google.com/str-comm-agent\n"
                "DESCRIPTION:Goal: Negotiate enterprise volume tiers for stablecoin checkout and explore early beta integration for the newly announced Agentic Commerce Protocol. Discuss fraud liability guardrails.\n"
                "END:VCALENDAR"
            ),
            "Anthropic Frontier Alignment Sync": (
                "Subject: Anthropic Technical Safety & Claude Enterprise Sync\n"
                "When: Friday, November 13, 2026 at 2:00 PM EST\n"
                "Participants: Dario Amodei, Daniela Amodei, Marcus Chen (Head of Security)\n"
                "Location: Zoom (https://zoom.us/j/9841248912)\n"
                "Agenda: Evaluate deployment guardrails for Claude 3.5 Sonnet Computer Use in enterprise air-gapped environments. Review recursive self-improvement audit requirements.\n"
            ),
            "Acme Health (Quiet Entity Test)": (
                "Subject: Acme Health Tech Introduction\n"
                "When: Monday, November 16, 2026 at 11:00 AM EST\n"
                "Participants: Dr. Karen Vance (Medical Director), David Miller (COO)\n"
                "Agenda: Explore regional clinic pilot. Evaluate quiet status and confirm compliance certifications.\n"
            )
        }
