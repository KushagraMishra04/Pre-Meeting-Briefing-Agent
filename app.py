"""
Pre-Meeting Briefing Agent - Streamlit Application.
Generates executive one-page briefs with 100% sourced claims for any company or person.
"""
import os
from datetime import datetime, time, timedelta
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.models import EntityType
from src.pipeline import BriefingPipeline
from src.brief_generator import BriefGenerator

# Page setup
st.set_page_config(
    page_title="Pre-Meeting Briefing Agent",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom executive styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .brief-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 16px;
    }
    .section-title {
        color: #0369A1;
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .question-box {
        background-color: #F0FDF4;
        border-left: 4px solid #16A34A;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 12px;
    }
    .stat-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        background: #E0F2FE;
        color: #0369A1;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# SIDEBAR: CONFIG & DEMO PRESETS
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ Agent Configuration")

    gemini_key_env = os.getenv("GEMINI_API_KEY", "")
    tavily_key_env = os.getenv("TAVILY_API_KEY", "")

    gemini_key = st.text_input(
        "Gemini API Key",
        value=gemini_key_env,
        type="password",
        help="Required for LLM extraction, verification and strategic questions."
    )

    tavily_key = st.text_input(
        "Tavily API Key (Optional)",
        value=tavily_key_env,
        type="password",
        help="Primary search provider. If left blank, DuckDuckGo is used automatically."
    )

    if tavily_key:
        st.success("Tavily Search: Active")
    else:
        st.info("Search Engine: DuckDuckGo (Zero-config Fallback)")

    model_choice = st.selectbox(
        "Gemini Model",
        options=["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
        index=0
    )

    st.markdown("---")
    st.markdown("### ⚡ Quick Demo Presets")
    st.caption("Click a preset to populate test inputs for live judging:")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("Stripe", use_container_width=True):
            st.session_state["preset_entity"] = "Stripe"
            st.session_state["preset_type"] = "Company"
        if st.button("Anthropic", use_container_width=True):
            st.session_state["preset_entity"] = "Anthropic"
            st.session_state["preset_type"] = "Company"
        if st.button("Databricks", use_container_width=True):
            st.session_state["preset_entity"] = "Databricks"
            st.session_state["preset_type"] = "Company"

    with col_p2:
        if st.button("Satya Nadella", use_container_width=True):
            st.session_state["preset_entity"] = "Satya Nadella"
            st.session_state["preset_type"] = "Person"
        if st.button("Jensen Huang", use_container_width=True):
            st.session_state["preset_entity"] = "Jensen Huang"
            st.session_state["preset_type"] = "Person"
        if st.button("Sam Altman", use_container_width=True):
            st.session_state["preset_entity"] = "Sam Altman"
            st.session_state["preset_type"] = "Person"

    st.markdown("---")
    with st.expander("📌 Problem Blueprint", expanded=False):
        st.markdown("""
        **Input:** Entity + Meeting Time  
        **Window:** Strict Last 30 Days  
        **Output:** One-page brief, every claim sourced:
        1. Snapshot (2 lines)
        2. News (30d) (top 3-5 items)
        3. Hires & Departures
        4. Launches & Funding
        5. Open Questions
        6. Sources (numbered & dated)
        """)


# ==========================================
# MAIN INTERFACE: INPUTS
# ==========================================
st.markdown('<div class="main-header">📋 Pre-Meeting Briefing Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Generate an executive one-page intelligence brief covering the last 30 days of news, hires, and launches—with 100% sourced claims.</div>', unsafe_allow_html=True)

# Form defaults
default_entity = st.session_state.get("preset_entity", "Stripe")
default_type_idx = 0
if st.session_state.get("preset_type") == "Company":
    default_type_idx = 1
elif st.session_state.get("preset_type") == "Person":
    default_type_idx = 2

col_in1, col_in2, col_in3 = st.columns([2.5, 1.2, 1.3])

with col_in1:
    entity_input = st.text_input(
        "Entity (Company or Person)",
        value=default_entity,
        placeholder="e.g. Stripe, Anthropic, Satya Nadella..."
    )

with col_in2:
    meeting_date = st.date_input("Meeting Date", value=datetime.now() + timedelta(days=1))

with col_in3:
    meeting_time_val = st.time_input("Meeting Time", value=time(10, 0))

# Combine into meeting datetime
combined_meeting_dt = datetime.combine(meeting_date, meeting_time_val)
window_start_dt = combined_meeting_dt - timedelta(days=30)

st.markdown(
    f'<span class="stat-pill">🗓️ Meeting: {combined_meeting_dt.strftime("%b %d, %Y at %I:%M %p")}</span>'
    f'<span class="stat-pill">⏳ Strict 30-Day Scope: {window_start_dt.strftime("%b %d")} – {combined_meeting_dt.strftime("%b %d, %Y")}</span>',
    unsafe_allow_html=True
)

st.write("")
generate_btn = st.button("🚀 Generate Executive Brief", type="primary", use_container_width=True)

# ==========================================
# PIPELINE EXECUTION
# ==========================================
if generate_btn:
    if not entity_input.strip():
        st.error("Please enter a company or person name.")
        st.stop()

    progress_bar = st.progress(0.0)
    status_text = st.empty()

    def on_progress_update(msg: str, pct: float):
        progress_bar.progress(pct)
        status_text.markdown(f"**{msg}**")

    try:
        pipeline = BriefingPipeline(
            gemini_api_key=gemini_key,
            tavily_api_key=tavily_key,
            model=model_choice
        )

        with st.spinner("Investigating last 30 days of data and verifying sources..."):
            result = pipeline.run(
                entity_name=entity_input,
                meeting_time=combined_meeting_dt,
                on_progress=on_progress_update
            )

        st.session_state["latest_result"] = result
        progress_bar.progress(1.0)
        status_text.success("Executive brief generated and verified!")

    except Exception as e:
        st.error(f"Error during briefing pipeline: {e}")
        status_text.empty()
        progress_bar.empty()


# ==========================================
# DISPLAY GENERATED BRIEF
# ==========================================
if "latest_result" in st.session_state:
    result = st.session_state["latest_result"]
    brief = result.brief

    st.markdown("---")

    # Header with Quick Actions
    col_act1, col_act2, col_act3 = st.columns([2, 1, 1])

    with col_act1:
        st.markdown(f"### Brief: {brief.entity.name}")
        st.caption(f"Covering {brief.entity.window_display} • Every claim linked to verified source")

    with col_act2:
        # One-Page PDF Download
        pdf_filename = f"{brief.entity.name.replace(' ', '_')}_PreMeeting_Brief.pdf"
        st.download_button(
            label="📄 Download 1-Page PDF",
            data=result.pdf_bytes,
            file_name=pdf_filename,
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

    with col_act3:
        # Markdown Copy
        st.download_button(
            label="📝 Download Markdown",
            data=result.markdown,
            file_name=f"{brief.entity.name.replace(' ', '_')}_Brief.md",
            mime="text/markdown",
            use_container_width=True
        )

    tab_brief, tab_sources, tab_audit = st.tabs(["📄 Executive Brief", "🔗 Verified Sources", "🔍 Grounding & Claim Audit"])

    with tab_brief:
        # Section 1: Snapshot
        st.markdown('<div class="brief-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">1. Snapshot</div>', unsafe_allow_html=True)
        st.markdown(brief.snapshot)
        st.markdown('</div>', unsafe_allow_html=True)

        # 2-Column layout for News & Launches
        col_n1, col_n2 = st.columns(2)

        with col_n1:
            # Section 2: News (30d)
            st.markdown('<div class="brief-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">2. Material News (Last 30 Days)</div>', unsafe_allow_html=True)
            for item in brief.news_items:
                st.markdown(f"• {item}")
            st.markdown('</div>', unsafe_allow_html=True)

            # Section 3: Hires & Departures
            st.markdown('<div class="brief-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">3. Leadership Moves & Departures</div>', unsafe_allow_html=True)
            for item in brief.hires_departures:
                st.markdown(f"• {item}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_n2:
            # Section 4: Launches & Funding
            st.markdown('<div class="brief-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">4. Launches & Capital Activity</div>', unsafe_allow_html=True)
            for item in brief.launches_funding:
                st.markdown(f"• {item}")
            st.markdown('</div>', unsafe_allow_html=True)

            # Section 5: Open Questions
            st.markdown('<div class="brief-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">5. Strategic Questions to Ask in Meeting</div>', unsafe_allow_html=True)
            for i, q in enumerate(brief.open_questions, 1):
                st.markdown(f"**Q{i}:** {q}")
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_sources:
        st.markdown("#### Verified Sourced References (Numbered & Dated)")
        st.caption("Every claim in the brief corresponds to a numbered citation below:")

        if brief.sources:
            for s in brief.sources:
                d_str = f" • *Published: {s.published_date}*" if s.published_date else ""
                st.markdown(
                    f"**[{s.id}]** [{s.title}]({s.url}) `{s.domain}`{d_str}"
                )
        else:
            st.info("No external sources recorded.")

    with tab_audit:
        st.markdown("#### Pipeline Grounding & Claim Extraction Audit")
        st.caption("Inspect the raw extraction and grounding verification for hackathon judging.")

        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.metric("Total Raw Search Snippets", len(result.raw_results))
        with col_a2:
            st.metric("Total Verified Grounded Claims", len(result.verified_claims))

        with st.expander("View All Grounded Claims"):
            for vc in result.verified_claims:
                st.markdown(
                    f"- **[{vc.source_id}] [{vc.category.upper()}]** {vc.statement} "
                    f"*(Source: {vc.source_domain}, Within Window: {vc.is_within_window})*"
                )

        with st.expander("View Raw Search Snippets"):
            for idx, r in enumerate(result.raw_results, 1):
                st.markdown(f"**#{idx} [{r.engine.upper()} / {r.query_category}]** [{r.title}]({r.url})")
                st.write(r.snippet)
                st.divider()
