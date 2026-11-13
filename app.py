"""Pre-Meeting Briefing Agent - Executive Intelligence Dashboard.
Theme: Warm Peach bleeding into Sunset Orange.
Featuring extra-large, high-visibility search consoles and enterprise trust features.
"""
import os
import re
from datetime import datetime, time, timedelta
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.models import EntityType, BriefData, ToneMode, AttendeeProfile
from src.pipeline import BriefingPipeline, PipelineResult
from src.brief_generator import BriefGenerator
from src.pdf_exporter import PDFExporter
from src.demo_data import get_demo_briefs
from src.calendar_parser import CalendarParser
from src.ask_brief import AskBriefEngine
from src.post_meeting import PostMeetingEngine
from src.diff_engine import DiffEngine


def clean_text(text: str) -> str:
    """Escapes dollar signs so KaTeX doesn't break prose into math formulas."""
    if not text:
        return ""
    return re.sub(r'(?<!\\)\$', r'\\$', text)


# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Briefly • Pre-Meeting Executive Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# WARM PEACH & ORANGE GRADIENT THEME (High-Visibility)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Global Page Background: Warm Peach bleeding into Sunset Orange */
    .stApp {
        background: linear-gradient(140deg, #FFF7ED 0%, #FFEDD5 30%, #FED7AA 70%, #FDBA74 100%) !important;
        background-attachment: fixed !important;
        color: #1C1917;
    }
    
    /* High-Visibility Card Containers */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background: rgba(255, 255, 255, 0.94) !important;
        backdrop-filter: blur(14px) !important;
        border: 2px solid #FB923C !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 30px -5px rgba(234, 88, 12, 0.12), 0 4px 10px -2px rgba(0, 0, 0, 0.04) !important;
        padding: 24px 28px !important;
    }
    
    /* SEARCH BARS: EXTRA LARGE & HIGH VISIBILITY */
    div[data-baseweb="input"] {
        background-color: #FFFFFF !important;
        border: 2.5px solid #F97316 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 16px rgba(249, 115, 22, 0.14) !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    div[data-baseweb="input"]:focus-within {
        border-color: #C2410C !important;
        box-shadow: 0 0 0 3px rgba(234, 88, 12, 0.30), 0 6px 22px rgba(234, 88, 12, 0.20) !important;
    }
    
    /* Search Bar Typography */
    div[data-baseweb="input"] input {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        color: #1C1917 !important;
        padding: 12px 18px !important;
    }
    
    div[data-baseweb="input"] input::placeholder {
        color: #9A3412 !important;
        font-weight: 400 !important;
        opacity: 0.75 !important;
    }
    
    /* Labels above search bars */
    .stTextInput label, .stDateInput label, .stTimeInput label {
        font-size: 0.96rem !important;
        font-weight: 700 !important;
        color: #7C2D12 !important;
        margin-bottom: 4px !important;
    }
    
    /* Date and Time Inputs Matching Style */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] {
        border: 2px solid #FB923C !important;
        border-radius: 12px !important;
        background: #FFFFFF !important;
        min-height: 50px !important;
        box-shadow: 0 4px 14px rgba(251, 146, 60, 0.10) !important;
    }
    
    /* Primary Action Buttons: Radiant Light Orange */
    div.stButton > button[kind="primary"],
    div.stDownloadButton > button[kind="primary"],
    button[data-testid="baseButton-primary"],
    button[kind="primary"] {
        background: linear-gradient(135deg, #FFA053 0%, #FB8231 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #FA7C2B !important;
        border-radius: 12px !important;
        font-weight: 750 !important;
        font-size: 1.02rem !important;
        padding: 11px 22px !important;
        min-height: 50px !important;
        box-shadow: 0 4px 14px rgba(251, 130, 49, 0.28) !important;
        text-shadow: 0 1px 2px rgba(124, 45, 18, 0.40) !important;
        transition: all 0.18s ease-in-out !important;
    }
    
    div.stButton > button[kind="primary"]:hover,
    div.stDownloadButton > button[kind="primary"]:hover,
    button[data-testid="baseButton-primary"]:hover,
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #FFAC68 0%, #FA751B 100%) !important;
        box-shadow: 0 6px 20px rgba(251, 130, 49, 0.38) !important;
        border-color: #F97316 !important;
        transform: translateY(-1px) !important;
        color: #FFFFFF !important;
    }

    /* Secondary / Chip / Standard Buttons: Resized Sleek Light-Orange Pills */
    div.stButton > button[kind="secondary"],
    div.stDownloadButton > button[kind="secondary"],
    button[data-testid="baseButton-secondary"],
    button[kind="secondary"],
    div.stButton > button:not([kind="primary"]),
    div.stDownloadButton > button:not([kind="primary"]) {
        background: linear-gradient(135deg, #FFB073 0%, #FA8638 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #FA7C2B !important;
        border-radius: 9999px !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        height: 36px !important;
        min-height: 36px !important;
        padding: 4px 14px !important;
        box-shadow: 0 2px 8px rgba(250, 134, 56, 0.20) !important;
        text-shadow: 0 1px 2px rgba(124, 45, 18, 0.35) !important;
        transition: all 0.15s ease-in-out !important;
    }

    div.stButton > button[kind="secondary"]:hover,
    div.stDownloadButton > button[kind="secondary"]:hover,
    button[data-testid="baseButton-secondary"]:hover,
    button[kind="secondary"]:hover,
    div.stButton > button:not([kind="primary"]):hover,
    div.stDownloadButton > button:not([kind="primary"]):hover {
        background: linear-gradient(135deg, #FFB882 0%, #F97825 100%) !important;
        border-color: #F97316 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(250, 134, 56, 0.32) !important;
        transform: translateY(-1px) !important;
    }

    /* Link Buttons */
    div.stLinkButton > a {
        background: linear-gradient(135deg, #FFB073 0%, #FA8638 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #FA7C2B !important;
        border-radius: 9999px !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        height: 36px !important;
        min-height: 36px !important;
        padding: 4px 14px !important;
        text-decoration: none !important;
        box-shadow: 0 2px 8px rgba(250, 134, 56, 0.20) !important;
        text-shadow: 0 1px 2px rgba(124, 45, 18, 0.35) !important;
        transition: all 0.18s ease-in-out !important;
    }

    div.stLinkButton > a:hover {
        background: linear-gradient(135deg, #FFB882 0%, #F97825 100%) !important;
        border-color: #F97316 !important;
        color: #FFFFFF !important;
    }
    
    /* Top Brand Tag */
    .brand-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: #7C2D12;
        letter-spacing: -0.6px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .brand-badge {
        font-size: 0.80rem;
        font-weight: 700;
        color: #EA580C;
        background: #FFF7ED;
        border: 1.5px solid #FDBA74;
        padding: 4px 10px;
        border-radius: 8px;
    }
    .trust-badge {
        font-size: 0.80rem;
        font-weight: 700;
        color: #15803D;
        background: #F0FDF4;
        border: 1.5px solid #BBF7D0;
        padding: 4px 10px;
        border-radius: 8px;
    }
    
    /* Metadata scope pills */
    .meta-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 14px;
        border-radius: 9999px;
        background: #FFFFFF;
        color: #7C2D12;
        font-size: 0.83rem;
        font-weight: 600;
        border: 1.5px solid #FED7AA;
        box-shadow: 0 1px 4px rgba(251, 146, 60, 0.08);
    }
    .meta-pill-active {
        background: #FFF7ED;
        color: #C2410C;
        border: 1.5px solid #FB923C;
        font-weight: 700;
    }

    /* ==========================================
       HIGH-VISIBILITY CLICKABLE SEGMENTED TAB BUTTONS
       ========================================== */
    div[data-testid="stTabs"] {
        margin-top: 14px !important;
        margin-bottom: 24px !important;
    }

    /* Tab List Container Bar - Frosted Oval Island Blended with Peach Theme */
    div[data-testid="stTabs"] [role="tablist"],
    div[data-testid="stTabs"] > div:first-child,
    .stTabs [role="tablist"] {
        background: rgba(255, 247, 237, 0.65) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        border: 1.5px solid rgba(251, 146, 60, 0.35) !important;
        border-radius: 9999px !important; /* Full Oval Capsule */
        padding: 5px 8px !important;
        gap: 6px !important;
        box-shadow: 0 4px 16px rgba(251, 146, 60, 0.08) !important;
        display: inline-flex !important;
        max-width: 100% !important;
        flex-wrap: wrap !important;
        align-items: center !important;
    }

    /* Individual Tab Buttons - Oval Capsule Shape Blended with Site */
    div[data-testid="stTabs"] button,
    div[data-testid="stTabs"] [role="tab"],
    div[data-testid="stTab"],
    button[data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.70) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        border: 1.5px solid rgba(253, 186, 116, 0.60) !important;
        border-radius: 9999px !important; /* Full Oval */
        padding: 8px 18px !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        color: #7C2D12 !important;
        box-shadow: 0 2px 6px rgba(234, 88, 12, 0.04) !important;
        cursor: pointer !important;
        transition: all 0.18s ease-in-out !important;
        margin: 2px !important;
    }

    div[data-testid="stTabs"] button p,
    div[data-testid="stTabs"] button span,
    div[data-testid="stTab"] p,
    div[data-testid="stTab"] span,
    div[data-testid="stTab"] div {
        color: #7C2D12 !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
    }

    /* Hover Elevation */
    div[data-testid="stTabs"] button:hover,
    div[data-testid="stTabs"] [role="tab"]:hover,
    div[data-testid="stTab"]:hover {
        background: rgba(255, 237, 213, 0.92) !important;
        border-color: #FB923C !important;
        color: #C2410C !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 3px 10px rgba(251, 146, 60, 0.18) !important;
    }

    div[data-testid="stTabs"] button:hover p,
    div[data-testid="stTabs"] button:hover span,
    div[data-testid="stTab"]:hover p,
    div[data-testid="stTab"]:hover span {
        color: #C2410C !important;
    }

    /* Active Selected Tab: Radiant Light Orange Oval */
    div[data-testid="stTabs"] button[aria-selected="true"],
    div[data-testid="stTabs"] [role="tab"][aria-selected="true"],
    div[data-testid="stTab"][aria-selected="true"] {
        background: linear-gradient(135deg, #FFA053 0%, #FB8231 100%) !important;
        border: 1.5px solid #FA7C2B !important;
        border-radius: 9999px !important; /* Full Oval */
        box-shadow: 0 4px 14px rgba(251, 130, 49, 0.32) !important;
        transform: translateY(-1px) !important;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] p,
    div[data-testid="stTabs"] button[aria-selected="true"] span,
    div[data-testid="stTab"][aria-selected="true"] p,
    div[data-testid="stTab"][aria-selected="true"] span {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        text-shadow: 0 1px 2px rgba(124, 45, 18, 0.45) !important;
    }

    /* Remove default thin underline/border elements */
    div[data-testid="stTabs"] hr,
    div[data-baseweb="tab-highlight"],
    div[data-baseweb="tab-border"] {
        display: none !important;
        height: 0 !important;
    }
    
    /* Hide default chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ==========================================
# APP TOP BAR
# ==========================================
col_brand, col_cfg = st.columns([4, 1])

with col_brand:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
        <span class="brand-title">⚡ Briefly</span>
        <span class="brand-badge">PRE-MEETING AGENT</span>
        <span class="trust-badge">🛡️ TRUST & SAFETY AUDITED</span>
    </div>
    """, unsafe_allow_html=True)

with col_cfg:
    with st.popover("⚙️ Settings", use_container_width=True):
        st.markdown("##### Configuration")
        st.caption("Optional API keys. Built-in search works out of the box.")

        env_gemini = os.getenv("GEMINI_API_KEY", "")
        env_tavily = os.getenv("TAVILY_API_KEY", "")

        gemini_api_key = st.text_input(
            "Gemini API Key",
            value=st.session_state.get("cfg_gemini", env_gemini),
            type="password",
            help="Powers LLM extraction, questions, and post-meeting follow-ups."
        )
        tavily_api_key = st.text_input(
            "Tavily API Key (Optional)",
            value=st.session_state.get("cfg_tavily", env_tavily),
            type="password",
            help="Primary search provider; falls back to DuckDuckGo if blank."
        )
        model_choice = st.selectbox(
            "Gemini Model",
            options=["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
            index=0
        )

        st.session_state["cfg_gemini"] = gemini_api_key
        st.session_state["cfg_tavily"] = tavily_api_key
        st.session_state["cfg_model"] = model_choice

        if gemini_api_key:
            st.success("Gemini API: Connected")
        else:
            st.info("LLM Mode: Semantic Fallback (Active)")

        if tavily_api_key:
            st.success("Search Engine: Tavily")
        else:
            st.info("Search Engine: DuckDuckGo (Free & Active)")


active_gemini_key = st.session_state.get("cfg_gemini", os.getenv("GEMINI_API_KEY", ""))
active_tavily_key = st.session_state.get("cfg_tavily", os.getenv("TAVILY_API_KEY", ""))
active_model = st.session_state.get("cfg_model", "gemini-2.5-flash")

demo_briefs = get_demo_briefs()
sample_invites = CalendarParser.get_sample_invites()


# ==========================================
# THE MAIN HIGHLIGHT: COMMAND & SEARCH ENGINE
# (Two Extra-Large, High-Visibility Search Bars)
# ==========================================
with st.container(border=True):
    st.markdown("""
        <div style="font-size: 1.40rem; font-weight: 800; color: #7C2D12; display: flex; align-items: center; gap: 8px; letter-spacing: -0.4px; margin-bottom: 2px;">
            🔍 Research Any Company, Attendee or Meeting Live
        </div>
        <div style="font-size: 0.95rem; color: #9A3412; margin-bottom: 18px; font-weight: 500;">
            Generate attendee profiles, 30-day verified intelligence, and goal-aware strategic questions with 100% click-to-evidence grounding.
        </div>
    """, unsafe_allow_html=True)

    # SEARCH BAR #1: MAIN TARGET ENTITY SEARCH BAR (Prominent, High Visibility)
    st.markdown("<div style='font-size: 1.05rem; font-weight: 800; color: #7C2D12; margin-bottom: 4px;'>🔍 1. TARGET ENTITY SEARCH (Company, Executive or Topic)</div>", unsafe_allow_html=True)
    
    col_s1, col_s2, col_s3, col_s4 = st.columns([3.2, 1.4, 1.1, 1.8])

    with col_s1:
        entity_query = st.text_input(
            "Target Entity",
            value=st.session_state.get("query_input_val", ""),
            placeholder="Type company or person (e.g. Stripe, Anthropic, Databricks, Satya Nadella)...",
            label_visibility="collapsed"
        )

    with col_s2:
        m_date = st.date_input(
            "Meeting Date",
            value=st.session_state.get("meeting_date_val", datetime.now() + timedelta(days=1)),
            label_visibility="collapsed"
        )

    with col_s3:
        m_time = st.time_input(
            "Meeting Time",
            value=st.session_state.get("meeting_time_val", time(10, 0)),
            label_visibility="collapsed"
        )

    with col_s4:
        run_btn = st.button("⚡ Generate Brief", type="primary", use_container_width=True)

    st.write("")

    # SEARCH BAR #2: MEETING OBJECTIVE / STRATEGIC GOAL SEARCH BAR (Prominent, High Visibility)
    st.markdown("<div style='font-size: 1.05rem; font-weight: 800; color: #7C2D12; margin-bottom: 4px;'>🎯 2. MEETING OBJECTIVE & STRATEGIC GOAL SEARCH</div>", unsafe_allow_html=True)
    
    col_g1, col_g2 = st.columns([3.2, 2.5])

    with col_g1:
        meeting_goal_input = st.text_input(
            "Meeting Objective",
            value=st.session_state.get("goal_input_val", ""),
            placeholder="Type target goal (e.g. Negotiate enterprise volume tiers for agentic checkout protocol)...",
            label_visibility="collapsed"
        )

    with col_g2:
        attendees_input = st.text_input(
            "Key Attendees",
            value=st.session_state.get("attendees_input_val", ""),
            placeholder="Key attendees (e.g. Patrick Collison, Will Gaybrick)...",
            label_visibility="collapsed"
        )

    # Format & Tone Toggle
    st.write("")
    tone_choice = st.radio(
        "Format & Tone Toggle",
        options=[
            ToneMode.EXECUTIVE.value,
            ToneMode.STANDARD.value,
            ToneMode.DEEP_DIVE.value
        ],
        index=1,
        horizontal=True
    )

    selected_tone = ToneMode.STANDARD
    if "Executive" in tone_choice:
        selected_tone = ToneMode.EXECUTIVE
    elif "Deep-Dive" in tone_choice:
        selected_tone = ToneMode.DEEP_DIVE

    # Two Feature Toolbars: Calendar Import & Recurring Sync Diff
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        with st.expander("📅 Import Calendar Invite (.ics or text)", expanded=False):
            st.caption("Paste meeting invite text or choose a preset to extract date, attendees, and goal:")
            col_c_sel, col_c_btn = st.columns([2.5, 1.2])
            with col_c_sel:
                chosen_invite_key = st.selectbox("Sample Calendar Invites", options=list(sample_invites.keys()))
            with col_c_btn:
                st.write("")
                load_cal_btn = st.button("Apply Invite", use_container_width=True)

            if load_cal_btn:
                raw_ics = sample_invites[chosen_invite_key]
                parsed = CalendarParser.parse_ics(raw_ics) if "BEGIN:VCALENDAR" in raw_ics else CalendarParser.parse_plain_text(raw_ics)
                st.session_state["query_input_val"] = chosen_invite_key.split()[0]
                st.session_state["goal_input_val"] = parsed.goal_agenda
                st.session_state["attendees_input_val"] = ", ".join(parsed.attendees)
                st.session_state["meeting_date_val"] = parsed.meeting_time.date()
                st.session_state["meeting_time_val"] = parsed.meeting_time.time()
                st.success(f"✓ Parsed invite for '{parsed.title}' with {len(parsed.attendees)} attendees!")
                st.rerun()

    with col_exp2:
        with st.expander("🔄 Recurring Meeting? 'Since Last Brief' Diff", expanded=False):
            st.caption("Provide prior meeting notes to highlight only NEW developments since your last sync:")
            diff_notes_val = st.text_area(
                "Prior Sync Notes",
                value=st.session_state.get("prev_notes_input_val", "Discussed initial merchant acquiring rates. Agreed to explore pilot integration next quarter. Patrick Collison mentioned stablecoin roadmap."),
                height=68,
                key="diff_notes_quick",
                label_visibility="collapsed"
            )
            if st.button("Load Prior Notes for Diff", key="btn_apply_quick_diff", use_container_width=True):
                st.session_state["prev_notes_input_val"] = diff_notes_val
                st.success("✓ Prior meeting context loaded! View the diff in the '🔄 Since Last Brief' tab.")
                st.rerun()

    # Scope Pills
    meeting_dt = datetime.combine(m_date, m_time)
    w_start = meeting_dt - timedelta(days=30)
    w_display = f"{w_start.strftime('%b %d')} – {meeting_dt.strftime('%b %d, %Y')}"

    st.markdown(f"""
        <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; margin-bottom: 14px; padding-top: 14px; border-top: 1.5px solid #FED7AA;">
            <span class="meta-pill">🗓️ Meeting: <b>{meeting_dt.strftime('%b %d, %Y at %I:%M %p')}</b></span>
            <span class="meta-pill meta-pill-active">⏳ 30-Day Window: <b>{w_display}</b></span>
            <span class="meta-pill">🛡️ Verification: <b>100% Grounded Quotes</b></span>
            <span class="meta-pill">🔒 Privacy: <b>Professional Data Only</b></span>
        </div>
    """, unsafe_allow_html=True)

    # Instant Demo Preset Chips (Sleek, compact, perfectly proportioned)
    col_chip_lbl, col_c1, col_c2, col_c3, col_c4 = st.columns([1.1, 1.0, 1.5, 1.4, 0.8])
    with col_chip_lbl:
        st.markdown("<div style='display: flex; align-items: center; height: 36px; font-size: 0.86rem; font-weight: 800; color: #7C2D12;'>⚡ Instant Demos:</div>", unsafe_allow_html=True)
    with col_c1:
        if st.button("🏢 Stripe", key="chip_stripe", use_container_width=True):
            st.session_state["active_brief"] = demo_briefs["Stripe"]
            st.session_state["active_pdf"] = PDFExporter.render(demo_briefs["Stripe"])
            st.session_state["active_entity_name"] = "Stripe"
            st.session_state["query_input_val"] = "Stripe"
            st.rerun()
    with col_c2:
        if st.button("🤖 Anthropic (Deep-Dive)", key="chip_anthropic", use_container_width=True):
            st.session_state["active_brief"] = demo_briefs["Anthropic"]
            st.session_state["active_pdf"] = PDFExporter.render(demo_briefs["Anthropic"])
            st.session_state["active_entity_name"] = "Anthropic"
            st.session_state["query_input_val"] = "Anthropic"
            st.rerun()
    with col_c3:
        if st.button("🏥 Acme Health (Quiet)", key="chip_acme", use_container_width=True):
            st.session_state["active_brief"] = demo_briefs["Acme Health (Quiet Entity)"]
            st.session_state["active_pdf"] = PDFExporter.render(demo_briefs["Acme Health (Quiet Entity)"])
            st.session_state["active_entity_name"] = "Acme Health Tech"
            st.session_state["query_input_val"] = "Acme Health Tech"
            st.rerun()
    with col_c4:
        if st.button("🔄 Reset", key="chip_reset", use_container_width=True):
            st.session_state["active_brief"] = demo_briefs["Stripe"]
            st.session_state["active_pdf"] = PDFExporter.render(demo_briefs["Stripe"])
            st.session_state["active_entity_name"] = "Stripe"
            st.session_state["query_input_val"] = ""
            st.session_state["goal_input_val"] = ""
            st.session_state["attendees_input_val"] = ""
            st.rerun()


# ==========================================
# PIPELINE EXECUTION
# ==========================================
if run_btn:
    if not entity_query.strip():
        st.warning("Please enter a company, person, or meeting title.")
        st.stop()

    status_box = st.status(f"Investigating **{entity_query}** across the last 30 days...", expanded=True)

    try:
        pipeline = BriefingPipeline(
            gemini_api_key=active_gemini_key,
            tavily_api_key=active_tavily_key,
            model=active_model
        )

        def progress_tracker(message: str, pct: float):
            status_box.write(f"• {message}")

        parsed_attendees = [a.strip() for a in attendees_input.split(",") if a.strip()]

        result: PipelineResult = pipeline.run(
            entity_name=entity_query,
            meeting_time=meeting_dt,
            meeting_goal=meeting_goal_input.strip() or None,
            tone_mode=selected_tone,
            attendee_names=parsed_attendees,
            on_progress=progress_tracker
        )

        status_box.update(
            label=f"✓ Brief complete for **{entity_query}** ({len(result.brief.sources)} sources grounded • Trust audited)",
            state="complete",
            expanded=False
        )

        st.session_state["active_brief"] = result.brief
        st.session_state["active_pdf"] = result.pdf_bytes
        st.session_state["active_entity_name"] = result.brief.entity.name

    except Exception as e:
        status_box.update(label=f"Search failed: {e}", state="error")
        st.error(f"Error details: {e}")


# ==========================================
# DEFAULT TO STRIPE ON FIRST VISIT
# ==========================================
if "active_brief" not in st.session_state:
    st.session_state["active_brief"] = demo_briefs["Stripe"]
    st.session_state["active_pdf"] = PDFExporter.render(demo_briefs["Stripe"])
    st.session_state["active_entity_name"] = "Stripe"


# ==========================================
# ACTIVE BRIEF & ACTION BAR
# ==========================================
brief: BriefData = st.session_state["active_brief"]
pdf_bytes: bytes = st.session_state.get("active_pdf", b"")
entity_name: str = brief.entity.name

col_a1, col_a2, col_a3 = st.columns([3.2, 1.4, 1.2])

with col_a1:
    st.markdown(f"### 📋 {entity_name}")
    st.caption(f"Mode: **{brief.tone_mode.value}** • Window: {brief.entity.window_display} • Goal: {brief.meeting_goal or 'Executive Alignment'}")

with col_a2:
    if pdf_bytes:
        pdf_name = f"{entity_name.replace(' ', '_')}_{brief.tone_mode.name}_Brief.pdf"
        st.download_button(
            label="📄 Download Executive PDF",
            data=pdf_bytes,
            file_name=pdf_name,
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

with col_a3:
    md_content = BriefGenerator.to_markdown(brief)
    st.download_button(
        label="📝 Export Markdown",
        data=md_content,
        file_name=f"{entity_name.replace(' ', '_')}_Brief.md",
        mime="text/markdown",
        use_container_width=True
    )

# Document Tabs
tab_brief, tab_chat, tab_diff, tab_post, tab_vault, tab_audit = st.tabs([
    "📄 Executive Brief",
    "💬 Ask-The-Brief (Q&A)",
    "🔄 Since Last Brief (Diff)",
    "📝 Post-Meeting Follow-Up",
    "🔗 Sourced Evidence Vault",
    "🛡️ Hallucination Audit Panel"
])


# ------------------------------------------
# TAB 1: EXECUTIVE BRIEF
# ------------------------------------------
with tab_brief:
    with st.container(border=True):
        col_m_l, col_m_r = st.columns([3, 2])
        with col_m_l:
            st.caption(f":orange[**EXECUTIVE BRIEF  •  {brief.tone_mode.name}  •  30-DAY INTELLIGENCE**]")
            st.title(entity_name)
            if brief.entity.role_or_industry:
                st.markdown(f"**{clean_text(brief.entity.role_or_industry)}**")
            if brief.meeting_goal:
                st.markdown(f"🎯 **Objective:** *{clean_text(brief.meeting_goal)}*")

        with col_m_r:
            st.info(
                f"🗓️ **Meeting:** {brief.entity.meeting_time.strftime('%b %d, %Y • %I:%M %p')}\n\n"
                f"⏳ **Scope (30 Days):** {brief.entity.window_display}"
            )

        st.divider()

        # Recurring Meeting Feature Callout Banner
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%); border: 1.5px solid #FB923C; border-radius: 12px; padding: 10px 18px; margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.25rem;">🔄</span>
                <div>
                    <span style="font-weight: 800; font-size: 0.92rem; color: #7C2D12;">Recurring Meeting? </span>
                    <span style="font-size: 0.86rem; color: #9A3412;">Isolate and highlight only new developments since your last sync in the <b>'🔄 Since Last Brief (Diff)'</b> tab above.</span>
                </div>
            </div>
            <span style="font-size: 0.78rem; font-weight: 700; color: #EA580C; background: #FFFFFF; border: 1px solid #FDBA74; padding: 3px 10px; border-radius: 20px;">RECURRING DIFF ENGINE</span>
        </div>
        """, unsafe_allow_html=True)

        # Attendee Profiles if present
        if brief.attendees:
            st.markdown("##### 👥 Attendee Profiles (Privacy-Compliant)")
            att_cols = st.columns(min(len(brief.attendees), 3))
            for idx, att in enumerate(brief.attendees[:3]):
                with att_cols[idx]:
                    with st.container(border=True):
                        st.markdown(f"**{clean_text(att.name)}**")
                        st.caption(f"{clean_text(att.role_title)} • {clean_text(att.organization_tenure)}")
                        if att.is_quiet_entity:
                            st.info("Nothing notable in the last 30 days.")
                        else:
                            st.markdown(f"**Recent Activity:** {clean_text(att.recent_activity)}")
                            st.caption(f"Shared Context: {clean_text(att.shared_interests)}")
            st.divider()

        # EXECUTIVE MODE: Exactly 5 strategic bullets
        if brief.tone_mode == ToneMode.EXECUTIVE:
            st.markdown("##### ⚡ Executive Strategic Briefing (5 Decision Bullets)")
            for i, bullet in enumerate(brief.executive_bullets, 1):
                st.success(f"**{i}.** {clean_text(bullet)}")
            st.divider()

        # STANDARD & DEEP-DIVE MODE
        else:
            # Section 1: Snapshot
            st.markdown("##### 01. Snapshot & Identity (2 Lines)")
            st.info(clean_text(brief.snapshot))

            if brief.quiet_entity_note:
                st.warning(f"ℹ️ **Quiet-Entity Notice:** {brief.quiet_entity_note}")

            col_c1, col_c2 = st.columns(2)

            with col_c1:
                # News with Click-to-Evidence
                st.markdown("##### 02. Material News (Last 30 Days)")
                with st.container(border=True):
                    if brief.news_items:
                        for item in brief.news_items:
                            status_badge = f":orange[[{item.evidence.status.value}]]" if item.evidence else ""
                            fresh_badge = f"*{item.evidence.freshness}*" if item.evidence else ""
                            st.markdown(f"- {clean_text(item.statement)} **{item.citation_tag}** {status_badge} • {fresh_badge}")
                            if item.evidence and item.evidence.verbatim_quote:
                                with st.expander(f"🔍 Click to Evidence {item.citation_tag}", expanded=False):
                                    st.markdown(f"**Verbatim Source Quote:**\n> \"{clean_text(item.evidence.verbatim_quote)}\"")
                                    st.caption(f"Source: [{clean_text(item.evidence.source_title)}]({item.evidence.source_url})")
                    else:
                        st.write("Nothing notable in the last 30 days.")

                # Hires & Departures
                st.markdown("##### 03. Leadership Moves & Departures")
                with st.container(border=True):
                    if brief.hires_departures:
                        for item in brief.hires_departures:
                            st.markdown(f"- {clean_text(item.statement)} **{item.citation_tag}**")
                            if item.evidence and item.evidence.verbatim_quote:
                                with st.expander(f"🔍 Click to Evidence {item.citation_tag}", expanded=False):
                                    st.markdown(f"**Verbatim Source Quote:**\n> \"{clean_text(item.evidence.verbatim_quote)}\"")
                    else:
                        st.write("Nothing notable in the last 30 days.")

            with col_c2:
                # Launches & Funding
                st.markdown("##### 04. Launches, Capital & Partnerships")
                with st.container(border=True):
                    if brief.launches_funding:
                        for item in brief.launches_funding:
                            conflict_tag = " :red[⚠️ CONFLICT DETECTED]" if item.conflict_detected else ""
                            st.markdown(f"- {clean_text(item.statement)} **{item.citation_tag}**{conflict_tag}")
                            if item.evidence and item.evidence.verbatim_quote:
                                with st.expander(f"🔍 Click to Evidence {item.citation_tag}", expanded=False):
                                    st.markdown(f"**Verbatim Source Quote:**\n> \"{clean_text(item.evidence.verbatim_quote)}\"")
                                    if item.evidence.conflict_note:
                                        st.error(f"Flagged Discrepancy: {item.evidence.conflict_note}")
                    else:
                        st.write("Nothing notable in the last 30 days.")

                # Deep-Dive debates if selected
                if brief.tone_mode == ToneMode.DEEP_DIVE and brief.deep_dive_context:
                    st.markdown("##### 🔬 Strategic Debates & Outcomes")
                    with st.container(border=True):
                        st.markdown(f"*{clean_text(brief.deep_dive_context.get('historical_context', ''))}*")
                        st.markdown("**Key Strategic Debates:**")
                        for d in brief.deep_dive_context.get("key_debates", []):
                            st.markdown(f"- {clean_text(d)}")

        # Goal-Aware Questions
        st.markdown("##### 05. Goal-Aware Strategic Questions")
        for i, q in enumerate(brief.goal_aware_questions, 1):
            st.success(f"**Q{i}:** {clean_text(q)}")

        # Grounded Sources
        st.markdown("##### 06. Grounded Sources (Numbered & Dated)")
        s_cols = st.columns(2)
        for idx, s in enumerate(brief.sources[:8]):
            target_col = s_cols[idx % 2]
            with target_col:
                with st.container(border=True):
                    st.markdown(f"**[{s.id}] [{clean_text(s.title[:45])}...]({s.url})**")
                    st.caption(f"`{s.domain}` • Freshness: *{s.freshness}*")

        # In-Brief Hallucination Audit Panel
        st.markdown("---")
        st.markdown("""
        <div style="background: #FFF7ED; border: 1.5px solid #FDBA74; border-left: 4px solid #EA580C; border-radius: 8px; padding: 16px 20px; margin-top: 20px;">
            <div style="font-weight: 800; color: #7C2D12; font-size: 1.0rem; margin-bottom: 6px;">
                🛡️ Hallucination Audit Panel
            </div>
        """, unsafe_allow_html=True)
        col_au1, col_au2, col_au3 = st.columns(3)
        with col_au1:
            st.metric("Total Claims Verified", brief.audit_panel.total_claims_verified)
        with col_au2:
            st.metric("Dropped Claims", brief.audit_panel.dropped_claims_count)
        with col_au3:
            st.metric("Privacy Filters", brief.audit_panel.privacy_filtered_count)

        if brief.audit_panel.dropped_claims:
            st.markdown("**Drop Reason(s):**")
            for dc in brief.audit_panel.dropped_claims:
                st.caption(f"• **{dc.drop_reason}**: *\"{clean_text(dc.statement)}\"*")
        else:
            st.caption("• **Drop Reason(s):** None (Zero hallucinations; 100% of claims grounded in verified quotes).")

        if brief.audit_panel.conflicts_detected:
            st.warning("⚠️ **Flagged Source Discrepancies:** " + " | ".join(brief.audit_panel.conflicts_detected))

        st.markdown("</div>", unsafe_allow_html=True)


# ------------------------------------------
# TAB 2: ASK-THE-BRIEF (GROUNDED CHAT)
# ------------------------------------------
with tab_chat:
    st.markdown("#### 💬 Ask-The-Brief (Grounded Conversational Q&A)")
    st.caption("Ask questions about this meeting, attendees, or recent developments. Every response is strictly cited with sources.")

    sample_questions = [
        f"What are the biggest operational risks for {entity_name}?",
        f"What recent product launch occurred in the last 30 days?",
        f"What should I specifically ask the attendees in this meeting?",
        f"What are their primary revenue drivers?"
    ]
    st.markdown("**Suggested Questions:**")
    col_q1, col_q2 = st.columns(2)
    for idx, sq in enumerate(sample_questions):
        target = col_q1 if idx % 2 == 0 else col_q2
        if target.button(sq, key=f"sq_{idx}", use_container_width=True):
            st.session_state["user_chat_input"] = sq

    user_query = st.text_input(
        "Ask a question about the brief:",
        value=st.session_state.get("user_chat_input", ""),
        placeholder=f"e.g. Has {entity_name} announced any funding recently?"
    )

    if st.button("Submit Question", type="primary", use_container_width=False) or user_query:
        if user_query:
            with st.spinner("Searching verified brief context..."):
                engine = AskBriefEngine(gemini_api_key=active_gemini_key, model=active_model)
                answer = engine.answer_question(user_query, brief)
                st.markdown("##### Answer:")
                st.info(clean_text(answer))


# ------------------------------------------
# TAB 3: SINCE LAST BRIEF (DIFF ENGINE)
# ------------------------------------------
with tab_diff:
    st.markdown("""
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 6px;">
            <div style="font-size: 1.25rem; font-weight: 800; color: #7C2D12;">
                🔄 'Since Last Brief' Diff Engine (Recurring Meetings)
            </div>
            <span style="font-size: 0.80rem; font-weight: 700; color: #EA580C; background: #FFF7ED; border: 1.5px solid #FDBA74; padding: 4px 12px; border-radius: 20px;">
                DELTA ISOLATION ACTIVE
            </span>
        </div>
        <div style="font-size: 0.90rem; color: #9A3412; margin-bottom: 16px;">
            Compare context against your previous meeting notes to filter out old discussions and highlight <b>ONLY new developments</b> (new hires, product launches, policy updates, or strategic shifts) over the past 30 days.
        </div>
    """, unsafe_allow_html=True)

    default_notes_text = (
        "In our previous sync last month, we reviewed Stripe's stablecoin payments expansion and discussed initial partner integration timelines. "
        "Patrick mentioned evaluating automated credit facilities with enterprise logistics partners."
    )
    current_notes_val = st.session_state.get("prev_notes_input_val", default_notes_text)

    col_btn_pre, col_btn_clr = st.columns([3, 1])
    with col_btn_pre:
        if st.button("⚡ Load Realistic 30-Day Prior Notes Preset", key="btn_load_preset_notes", use_container_width=True):
            st.session_state["prev_notes_input_val"] = default_notes_text
            st.rerun()
    with col_btn_clr:
        if st.button("🧹 Clear Notes", key="btn_clear_notes", use_container_width=True):
            st.session_state["prev_notes_input_val"] = ""
            st.rerun()

    prev_notes_input = st.text_area(
        "Previous Meeting Notes / Discussion Context",
        value=current_notes_val,
        height=95,
        placeholder="Paste bullets, transcript excerpts, or summary from your prior meeting with this team..."
    )

    col_c_diff, col_c_info = st.columns([1.5, 3])
    with col_c_diff:
        recompute_btn = st.button("⚡ Compute Intelligence Delta", type="primary", use_container_width=True)

    if recompute_btn or "computed_diff" not in st.session_state:
        diff_res = DiffEngine.compute_diff(
            current_news=brief.news_items,
            current_hires=brief.hires_departures,
            current_launches=brief.launches_funding,
            previous_notes_or_brief=prev_notes_input
        )
        st.session_state["computed_diff"] = diff_res

    active_diff = st.session_state.get("computed_diff", brief.diff)
    if active_diff:
        st.markdown(f"""
            <div style="background: #FFFFFF; border: 1.5px solid #FDBA74; border-radius: 12px; padding: 10px 16px; margin: 14px 0; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
                <span style="font-size: 0.88rem; color: #7C2D12; font-weight: 700;">
                    📊 Baseline Comparison: <i>{active_diff.previous_meeting_date}</i>
                </span>
                <span style="font-size: 0.82rem; color: #15803D; font-weight: 700;">
                    ✓ Prior Topics Filtered • Incremental Delta Isolated
                </span>
            </div>
        """, unsafe_allow_html=True)

        col_df1, col_df2 = st.columns(2)
        with col_df1:
            with st.container(border=True):
                st.markdown("##### 🚀 New External Developments")
                st.caption("Fresh intelligence that occurred since your prior sync:")
                if active_diff.new_developments:
                    for nd in active_diff.new_developments:
                        st.success(f"• {clean_text(nd)}")
                else:
                    st.info("Nothing new since last sync.")

        with col_df2:
            with st.container(border=True):
                st.markdown("##### 👥 Leadership & Product Shifts")
                st.caption("Personnel changes and new launches not discussed previously:")
                if active_diff.leadership_updates:
                    for lh in active_diff.leadership_updates:
                        st.info(f"• **Leadership Move:** {clean_text(lh)}")
                if active_diff.product_shifts:
                    for ps in active_diff.product_shifts:
                        st.info(f"• **Product Launch:** {clean_text(ps)}")
                if not active_diff.leadership_updates and not active_diff.product_shifts:
                    st.info("No new leadership or product announcements since last sync.")


# ------------------------------------------
# TAB 4: POST-MEETING FOLLOW-UP MODE
# ------------------------------------------
with tab_post:
    st.markdown("#### 📝 Post-Meeting Action Items & Follow-Up Email")
    st.caption("Paste meeting notes or a transcript after the call to automatically generate owner-assigned Action Items and an executive follow-up email.")

    sample_transcript = f"""Meeting with {entity_name} team.
- Reviewed Agentic Commerce SDK. Patrick confirmed beta sandbox access will be provisioned by Friday.
- Action: @Sarah to send API security specifications by Wednesday.
- Action: @Patrick to introduce engineering lead for latency testing by next Tuesday.
- Agreed to reconvene in two weeks to review pilot results."""

    transcript_input = st.text_area("Meeting Transcript or Rough Notes:", value=sample_transcript, height=130)

    if st.button("⚡ Generate Follow-Up Pack", type="primary"):
        with st.spinner("Extracting action items and drafting follow-up email..."):
            pm_engine = PostMeetingEngine(gemini_api_key=active_gemini_key, model=active_model)
            att_names = [a.name for a in brief.attendees] if brief.attendees else ["Team"]
            actions, email_draft = pm_engine.process_transcript(
                meeting_title=f"{entity_name} Review",
                attendees=att_names,
                notes_or_transcript=transcript_input
            )
            st.session_state["post_actions"] = actions
            st.session_state["post_email"] = email_draft

    if "post_actions" in st.session_state:
        st.markdown("##### Owner-Assigned Action Items")
        for ai in st.session_state["post_actions"]:
            st.markdown(f"- [ ] **{ai.task}** • **Owner:** `{ai.owner}` • **Deadline:** `{ai.deadline}` • Priority: `{ai.priority}`")

        st.markdown("##### Executive Follow-Up Email Draft")
        email_obj = st.session_state["post_email"]
        st.text_input("Subject:", value=email_obj.subject)
        st.text_area("Email Body:", value=email_obj.body, height=220)


# ------------------------------------------
# TAB 5: SOURCED EVIDENCE VAULT
# ------------------------------------------
with tab_vault:
    st.markdown("#### 🔗 Sourced Evidence Vault (Verbatim Citations)")
    st.caption("Audited repository of articles, publish timestamps, and verbatim quotes substantiating the brief:")

    if brief.sources:
        for s in brief.sources:
            col_v1, col_v2 = st.columns([4, 1])
            with col_v1:
                st.markdown(f"**[{s.id}] [{clean_text(s.title)}]({s.url})**")
                st.caption(f"Domain: `{s.domain}` • Freshness: *{s.freshness}* • Date: {s.published_date}")
            with col_v2:
                st.link_button("Open Article ↗", s.url, use_container_width=True)
            st.divider()


# ------------------------------------------
# TAB 6: HALLUCINATION AUDIT PANEL
# ------------------------------------------
with tab_audit:
    st.markdown("#### 🛡️ Comprehensive Hallucination & Trust Audit")
    st.caption("Auditing metrics validating that every claim is grounded, fresh, and privacy-compliant.")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Total Claims Verified", brief.audit_panel.total_claims_verified)
    with col_m2:
        st.metric("Dropped Claims", brief.audit_panel.dropped_claims_count)
    with col_m3:
        st.metric("Privacy Filters Applied", brief.audit_panel.privacy_filtered_count)
    with col_m4:
        st.metric("Verification Rate", brief.audit_panel.verification_score)

    st.markdown("---")
    st.markdown("##### Dropped Claims & Reason Log")
    if brief.audit_panel.dropped_claims:
        for dc in brief.audit_panel.dropped_claims:
            st.error(f"**Reason:** {dc.drop_reason}\n\n**Statement Removed:** *\"{clean_text(dc.statement)}\"*\n\n**Raw Source:** `{dc.raw_source}`")
    else:
        st.success("✓ Zero claims dropped. Every factual statement is substantiated by an authenticated source quote.")

    if brief.audit_panel.conflicts_detected:
        st.markdown("##### Flagged Discrepancies Across Sources")
        for conf in brief.audit_panel.conflicts_detected:
            st.warning(f"⚠️ {conf}")
