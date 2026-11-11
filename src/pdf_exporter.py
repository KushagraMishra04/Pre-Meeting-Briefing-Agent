"""
Executive PDF Exporter.
Renders BriefData across Executive Mode, Standard Mode, and Deep-Dive Mode.
Includes Attendee Profiles, Click-to-Evidence anchors, Freshness indicators,
and the Hallucination Audit Panel.
"""
from typing import Optional
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from src.models import BriefData, ToneMode


def sanitize_text(text: str) -> str:
    """Replaces non-Latin-1 unicode symbols with clean printable characters."""
    if not text:
        return ""
    replacements = {
        "•": "-",
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "\u2022": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


class ExecutiveBriefPDF(FPDF):
    """Custom FPDF layout for executive briefing sheets."""

    def __init__(self):
        super().__init__(orientation="portrait", unit="mm", format="A4")
        self.set_margins(left=12, top=10, right=12)
        self.set_auto_page_break(auto=True, margin=10)
        self.add_page()


class PDFExporter:
    """Renders BriefData into an executive PDF with light theme."""

    COLOR_PRIMARY = (15, 23, 42)       # Slate Navy #0F172A
    COLOR_ACCENT = (37, 99, 235)       # Royal Blue #2563EB
    COLOR_TEXT_MAIN = (30, 41, 59)     # Slate #1E293B
    COLOR_TEXT_MUTED = (100, 116, 139) # Gray #64748B
    COLOR_HEADER_BG = (239, 246, 255)  # Soft Sky Tint #EFF6FF
    COLOR_BORDER = (219, 234, 254)     # Soft Blue Border #DBEAFE
    COLOR_BG_BOX = (248, 250, 252)     # Off-white #F8FAFC
    COLOR_LINE = (226, 232, 240)       # Light border #E2E8F0

    @classmethod
    def render(cls, brief: BriefData) -> bytes:
        """Renders the brief into PDF bytes."""
        pdf = ExecutiveBriefPDF()
        printable_width = 186.0  # 210 - 24

        # Top Accent Stripe
        pdf.set_fill_color(*cls.COLOR_ACCENT)
        pdf.rect(12, 10, printable_width, 2.5, style="F")

        # Header Card
        pdf.set_fill_color(*cls.COLOR_HEADER_BG)
        pdf.set_draw_color(*cls.COLOR_BORDER)
        pdf.set_line_width(0.3)
        pdf.rect(12, 12.5, printable_width, 22, style="DF")

        # Top tag
        pdf.set_xy(16, 14.5)
        pdf.set_font("helvetica", "B", 7)
        pdf.set_text_color(*cls.COLOR_ACCENT)
        pdf.cell(
            0, 3,
            sanitize_text(f"EXECUTIVE PRE-MEETING BRIEF  |  {brief.tone_mode.name}  |  30-DAY INTELLIGENCE"),
            new_x=XPos.LMARGIN, new_y=YPos.NEXT
        )

        # Entity Title
        pdf.set_xy(16, 18.5)
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(*cls.COLOR_PRIMARY)
        entity_title = sanitize_text(brief.entity.name)
        if len(entity_title) > 34:
            entity_title = entity_title[:31] + "..."
        pdf.cell(100, 8, entity_title, new_x=XPos.RIGHT, new_y=YPos.TOP)

        # Right-aligned meeting info
        pdf.set_xy(110, 14.5)
        pdf.set_font("helvetica", "", 7)
        pdf.set_text_color(*cls.COLOR_TEXT_MAIN)
        mt_str = brief.entity.meeting_time.strftime("%b %d, %Y  %I:%M %p")
        pdf.cell(84, 3.8, sanitize_text(f"Meeting: {mt_str}"), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_xy(110, 18.5)
        pdf.set_font("helvetica", "B", 7)
        pdf.set_text_color(*cls.COLOR_ACCENT)
        pdf.cell(84, 3.8, sanitize_text(f"Scope: {brief.entity.window_display}"), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_xy(110, 22.5)
        pdf.set_font("helvetica", "I", 6.8)
        pdf.set_text_color(*cls.COLOR_TEXT_MUTED)
        goal_txt = f"Goal: {brief.meeting_goal[:36]}..." if brief.meeting_goal else "Goal: Executive Alignment"
        pdf.cell(84, 3.8, sanitize_text(goal_txt), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_y(37.0)

        def draw_section_header(title: str, icon_num: str):
            pdf.set_text_color(*cls.COLOR_ACCENT)
            pdf.set_font("helvetica", "B", 8)
            pdf.cell(6, 4.5, icon_num, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_text_color(*cls.COLOR_PRIMARY)
            pdf.cell(0, 4.5, sanitize_text(title.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            curr_y = pdf.get_y()
            pdf.set_draw_color(*cls.COLOR_LINE)
            pdf.set_line_width(0.3)
            pdf.line(12, curr_y, 12 + printable_width, curr_y)
            pdf.set_y(curr_y + 1.2)

        # Attendees section if available
        if brief.attendees:
            draw_section_header("Key Attendees & Participants", "00")
            pdf.set_font("helvetica", "", 7.5)
            for att in brief.attendees[:3]:
                pdf.set_text_color(*cls.COLOR_ACCENT)
                pdf.cell(4, 3.5, "-", new_x=XPos.RIGHT, new_y=YPos.TOP)
                pdf.set_text_color(*cls.COLOR_TEXT_MAIN)
                att_line = f"{att.name} ({att.role_title}, {att.organization_tenure})"
                if att.is_quiet_entity:
                    att_line += " - Nothing notable in last 30d."
                else:
                    att_line += f" - {att.recent_activity[:60]}"
                pdf.multi_cell(printable_width - 4, 3.4, sanitize_text(att_line))
            pdf.ln(1.0)

        # MODE SPECIFIC CONTENT
        if brief.tone_mode == ToneMode.EXECUTIVE:
            draw_section_header("Executive Briefing (5 Strategic Decision Bullets)", "01")
            pdf.set_font("helvetica", "", 8)
            for i, b in enumerate(brief.executive_bullets, 1):
                pdf.set_text_color(*cls.COLOR_ACCENT)
                pdf.cell(5, 4.0, f"{i}.", new_x=XPos.RIGHT, new_y=YPos.TOP)
                pdf.set_text_color(*cls.COLOR_TEXT_MAIN)
                pdf.multi_cell(printable_width - 5, 3.8, sanitize_text(b))
                pdf.ln(0.5)
            pdf.ln(1.0)

        else:
            # 1. Snapshot
            draw_section_header("1. Snapshot & Identity (2 Lines)", "01")
            pdf.set_font("helvetica", "", 7.8)
            pdf.set_text_color(*cls.COLOR_TEXT_MAIN)
            clean_snapshot = sanitize_text(brief.snapshot.replace("\n", " "))
            pdf.multi_cell(printable_width, 3.6, clean_snapshot)
            pdf.ln(1.0)

            # 2. News
            draw_section_header("2. Material News (Last 30 Days)", "02")
            pdf.set_font("helvetica", "", 7.5)
            if brief.news_items:
                for item in brief.news_items[:3]:
                    fresh_str = f" ({item.evidence.freshness})" if item.evidence else ""
                    pdf.set_text_color(*cls.COLOR_ACCENT)
                    pdf.cell(4, 3.6, "-", new_x=XPos.RIGHT, new_y=YPos.TOP)
                    pdf.set_text_color(*cls.COLOR_TEXT_MAIN)
                    pdf.multi_cell(printable_width - 4, 3.4, sanitize_text(f"{item.statement} {item.citation_tag}{fresh_str}"))
                    pdf.ln(0.3)
            else:
                pdf.cell(0, 3.6, "Nothing notable in the last 30 days.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(0.8)

            # 3. Hires & Departures
            draw_section_header("3. Leadership Moves & Departures", "03")
            pdf.set_font("helvetica", "", 7.5)
            if brief.hires_departures:
                for item in brief.hires_departures[:2]:
                    pdf.set_text_color(*cls.COLOR_ACCENT)
                    pdf.cell(4, 3.6, "-", new_x=XPos.RIGHT, new_y=YPos.TOP)
                    pdf.set_text_color(*cls.COLOR_TEXT_MAIN)
                    pdf.multi_cell(printable_width - 4, 3.4, sanitize_text(f"{item.statement} {item.citation_tag}"))
                    pdf.ln(0.3)
            else:
                pdf.cell(0, 3.6, "Nothing notable in the last 30 days.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(0.8)

            # 4. Launches & Funding
            draw_section_header("4. Launches, Capital & Partnerships", "04")
            pdf.set_font("helvetica", "", 7.5)
            if brief.launches_funding:
                for item in brief.launches_funding[:2]:
                    pdf.set_text_color(*cls.COLOR_ACCENT)
                    pdf.cell(4, 3.6, "-", new_x=XPos.RIGHT, new_y=YPos.TOP)
                    pdf.set_text_color(*cls.COLOR_TEXT_MAIN)
                    pdf.multi_cell(printable_width - 4, 3.4, sanitize_text(f"{item.statement} {item.citation_tag}"))
                    pdf.ln(0.3)
            else:
                pdf.cell(0, 3.6, "Nothing notable in the last 30 days.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(0.8)

        # GOAL-AWARE QUESTIONS
        draw_section_header("5. Goal-Aware Strategic Questions", "05")
        for i in range(min(len(brief.goal_aware_questions), 3)):
            q_text = sanitize_text(brief.goal_aware_questions[i])
            pdf.set_font("helvetica", "B", 7.5)
            pdf.set_text_color(*cls.COLOR_ACCENT)
            pdf.cell(6, 3.6, f"Q{i+1}:", new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font("helvetica", "", 7.5)
            pdf.set_text_color(*cls.COLOR_TEXT_MAIN)
            pdf.multi_cell(printable_width - 6, 3.4, q_text)
            pdf.ln(0.4)
        pdf.ln(0.8)

        # SOURCES
        draw_section_header("6. Grounded Sources (Numbered & Dated)", "06")
        pdf.set_font("helvetica", "", 6.8)
        max_sources = min(len(brief.sources), 4)
        for s in brief.sources[:max_sources]:
            txt = sanitize_text(f"[{s.id}] {s.domain} ({s.freshness}) - {s.title[:45]}")
            pdf.set_text_color(*cls.COLOR_ACCENT)
            pdf.cell(printable_width, 3.2, txt, link=s.url, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(0.8)

        # HALLUCINATION AUDIT PANEL
        draw_section_header("Hallucination Audit Panel", "07")
        pdf.set_font("helvetica", "B", 6.8)
        pdf.set_text_color(22, 163, 74)  # Green
        pdf.cell(60, 3.2, f"Total Claims Verified: {brief.audit_panel.total_claims_verified}", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_text_color(220, 38, 38)  # Red
        pdf.cell(60, 3.2, f"Dropped Claims: {brief.audit_panel.dropped_claims_count}", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_text_color(*cls.COLOR_TEXT_MUTED)
        pdf.cell(60, 3.2, f"Privacy Filters: {brief.audit_panel.privacy_filtered_count}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        if brief.audit_panel.dropped_claims:
            pdf.set_font("helvetica", "I", 6.2)
            dc = brief.audit_panel.dropped_claims[0]
            pdf.cell(printable_width, 3.0, sanitize_text(f"Drop Reason: {dc.drop_reason} - \"{dc.statement[:65]}...\""), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Footer
        curr_y = pdf.get_y()
        if curr_y < 285:
            pdf.set_xy(12, 287)
        pdf.set_font("helvetica", "I", 6.2)
        pdf.set_text_color(*cls.COLOR_TEXT_MUTED)
        pdf.cell(
            printable_width,
            3,
            sanitize_text("Briefly Agent  |  Strictly Sourced Claims  |  Trust & Safety Audited"),
            align="C"
        )

        return bytes(pdf.output())

    @classmethod
    def export_to_file(cls, brief: BriefData, filepath: str) -> str:
        data = cls.render(brief)
        with open(filepath, "wb") as f:
            f.write(data)
        return filepath
