"""
One-Page Executive PDF Exporter.
Builds a crisp, professional, single-page executive brief using fpdf2.
Features a modern light executive theme, clickable hyperlinks, and strict 1-page layout.
"""
from typing import Optional
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from src.models import BriefData


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
        # 210mm wide x 297mm high
        self.set_margins(left=12, top=10, right=12)
        self.set_auto_page_break(auto=False)
        self.add_page()


class PDFExporter:
    """Renders BriefData into a single-page PDF with a clean, modern light theme."""

    # Light executive color palette
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

        # Top Accent Stripe (Royal Blue)
        pdf.set_fill_color(*cls.COLOR_ACCENT)
        pdf.rect(12, 10, printable_width, 2.5, style="F")

        # Header Card (Light & Crisp)
        pdf.set_fill_color(*cls.COLOR_HEADER_BG)
        pdf.set_draw_color(*cls.COLOR_BORDER)
        pdf.set_line_width(0.3)
        pdf.rect(12, 12.5, printable_width, 20, style="DF")

        # Top tag
        pdf.set_xy(16, 14.5)
        pdf.set_font("helvetica", "B", 7)
        pdf.set_text_color(*cls.COLOR_ACCENT)
        pdf.cell(
            0, 3,
            sanitize_text("EXECUTIVE PRE-MEETING BRIEF  |  30-DAY INTELLIGENCE"),
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
        pdf.set_xy(110, 15)
        pdf.set_font("helvetica", "", 7)
        pdf.set_text_color(*cls.COLOR_TEXT_MAIN)
        mt_str = brief.entity.meeting_time.strftime("%b %d, %Y  %I:%M %p")
        pdf.cell(84, 4, sanitize_text(f"Meeting: {mt_str}"), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_xy(110, 20)
        pdf.set_font("helvetica", "B", 7)
        pdf.set_text_color(*cls.COLOR_ACCENT)
        pdf.cell(84, 4, sanitize_text(f"Window: {brief.entity.window_display}"), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_y(35.5)

        # Helper: Render Section Header
        def draw_section_header(title: str, icon_num: str):
            pdf.set_text_color(*cls.COLOR_ACCENT)
            pdf.set_font("helvetica", "B", 8)
            pdf.cell(6, 4.5, icon_num, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_text_color(*cls.COLOR_PRIMARY)
            pdf.cell(0, 4.5, sanitize_text(title.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

            # Thin accent line under header
            curr_y = pdf.get_y()
            pdf.set_draw_color(*cls.COLOR_LINE)
            pdf.set_line_width(0.3)
            pdf.line(12, curr_y, 12 + printable_width, curr_y)
            pdf.set_y(curr_y + 1.2)

        # ==========================================
        # SECTION 1: SNAPSHOT (2 lines)
        # ==========================================
        draw_section_header("1. Snapshot & Identity (2 Lines)", "01")
        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(*cls.COLOR_TEXT_MAIN)
        clean_snapshot = sanitize_text(brief.snapshot.replace("\n", " "))
        pdf.multi_cell(printable_width, 3.8, clean_snapshot)
        pdf.ln(1.5)

        # ==========================================
        # SECTION 2: NEWS (LAST 30 DAYS)
        # ==========================================
        draw_section_header("2. Material News (Last 30 Days)", "02")
        pdf.set_font("helvetica", "", 7.8)
        for item in brief.news_items[:4]:
            pdf.set_text_color(*cls.COLOR_ACCENT)
            pdf.cell(4, 3.8, "-", new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_text_color(*cls.COLOR_TEXT_MAIN)
            pdf.multi_cell(printable_width - 4, 3.6, sanitize_text(item))
            pdf.ln(0.4)
        pdf.ln(1.0)

        # ==========================================
        # SECTION 3: HIRES & DEPARTURES
        # ==========================================
        draw_section_header("3. Leadership Moves & Departures", "03")
        pdf.set_font("helvetica", "", 7.8)
        for item in brief.hires_departures[:2]:
            pdf.set_text_color(*cls.COLOR_ACCENT)
            pdf.cell(4, 3.8, "-", new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_text_color(*cls.COLOR_TEXT_MAIN)
            pdf.multi_cell(printable_width - 4, 3.6, sanitize_text(item))
            pdf.ln(0.4)
        pdf.ln(1.0)

        # ==========================================
        # SECTION 4: LAUNCHES & FUNDING
        # ==========================================
        draw_section_header("4. Launches, Capital & Partnerships", "04")
        pdf.set_font("helvetica", "", 7.8)
        for item in brief.launches_funding[:2]:
            pdf.set_text_color(*cls.COLOR_ACCENT)
            pdf.cell(4, 3.8, "-", new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_text_color(*cls.COLOR_TEXT_MAIN)
            pdf.multi_cell(printable_width - 4, 3.6, sanitize_text(item))
            pdf.ln(0.4)
        pdf.ln(1.0)

        # ==========================================
        # SECTION 5: OPEN QUESTIONS
        # ==========================================
        draw_section_header("5. Strategic Open Questions to Ask in Meeting", "05")
        q_count = min(len(brief.open_questions), 3)

        for i in range(q_count):
            q_text = sanitize_text(brief.open_questions[i])
            pdf.set_font("helvetica", "B", 7.8)
            pdf.set_text_color(*cls.COLOR_ACCENT)
            pdf.cell(6, 3.8, f"Q{i+1}:", new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font("helvetica", "", 7.8)
            pdf.set_text_color(*cls.COLOR_TEXT_MAIN)
            pdf.multi_cell(printable_width - 6, 3.6, q_text)
            pdf.ln(0.5)

        pdf.ln(1.0)

        # ==========================================
        # SECTION 6: SOURCES (CLICKABLE HYPERLINKS)
        # ==========================================
        draw_section_header("6. Grounded Sources (Numbered & Dated)", "06")
        pdf.set_font("helvetica", "", 7)

        max_sources = min(len(brief.sources), 6)
        col_w = printable_width / 2.0

        for i in range(0, max_sources, 2):
            s1 = brief.sources[i]
            s2 = brief.sources[i + 1] if i + 1 < max_sources else None

            # Left column source
            d1 = f" ({s1.published_date})" if s1.published_date else ""
            txt1 = sanitize_text(f"[{s1.id}] {s1.domain}{d1} - {s1.title[:36]}")
            pdf.set_text_color(*cls.COLOR_ACCENT)
            pdf.cell(col_w - 2, 3.5, txt1, link=s1.url, new_x=XPos.RIGHT, new_y=YPos.TOP)

            # Right column source
            if s2:
                d2 = f" ({s2.published_date})" if s2.published_date else ""
                txt2 = sanitize_text(f"[{s2.id}] {s2.domain}{d2} - {s2.title[:36]}")
                pdf.cell(col_w - 2, 3.5, txt2, link=s2.url, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            else:
                pdf.ln(3.5)

        # Footer note (Pinned to bottom of page)
        pdf.set_xy(12, 287)
        pdf.set_font("helvetica", "I", 6.5)
        pdf.set_text_color(*cls.COLOR_TEXT_MUTED)
        pdf.cell(
            printable_width,
            3,
            sanitize_text("Generated by Briefly Agent  |  Every claim grounded in verified sources  |  One-Page Brief"),
            align="C"
        )

        return bytes(pdf.output())

    @classmethod
    def export_to_file(cls, brief: BriefData, filepath: str) -> str:
        """Writes brief to disk and returns absolute path."""
        data = cls.render(brief)
        with open(filepath, "wb") as f:
            f.write(data)
        return filepath
