"""
app.py
Streamlit UI for the AI Resume-JD Matcher.
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from resume_parser import extract_text, extract_bullets, extract_sections
from matcher import overall_score, score_bullets, top_missing_keywords
from llm_feedback import get_feedback, rewrite_bullet

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Resume Matcher", page_icon="📄", layout="wide")

st.title("AI Resume & Job Description Matcher")
st.caption("Powered by sentence-transformers + Groq (free LLM API)")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    top_n_keywords = st.slider("Missing keywords to show", 5, 20, 10)
    show_all_bullets = st.checkbox("Show all bullet scores", value=False)
    st.divider()
    st.subheader("AI Features (Groq)")
    groq_api_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Free key at https://console.groq.com — no credit card needed",
    )
    if not groq_api_key:
        st.warning("Add a free Groq API key to enable AI features.")
    else:
        st.success("API key set — AI features enabled.")

# ── Initialise session state ──────────────────────────────────────────────────
for key in ["score", "bullet_scores", "missing_kw", "resume_text", "jd_text",
            "sections", "ai_feedback", "rewrites"]:
    if key not in st.session_state:
        st.session_state[key] = None if key in ["score", "bullet_scores",
                                                  "missing_kw", "sections"] else "" if key in [
            "resume_text", "jd_text", "ai_feedback"] else {}

# ── Input columns ─────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Resume")
    resume_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx", "txt"], key="resume")
    resume_text_input = st.text_area("Or paste resume text", height=200, key="resume_raw")

with col2:
    st.subheader("Job Description")
    jd_input = st.text_area("Paste job description here", height=300, key="jd_raw")

# Resolve resume text
resume_text = ""
if resume_file:
    resume_text = extract_text(resume_file)
elif resume_text_input.strip():
    resume_text = resume_text_input.strip()

# ── Analyze button ────────────────────────────────────────────────────────────
if st.button("Analyze Match", type="primary", disabled=not (resume_text and jd_input)):
    with st.spinner("Computing similarity..."):
        st.session_state.score = overall_score(resume_text, jd_input)
        st.session_state.bullet_scores = score_bullets(extract_bullets(resume_text), jd_input)
        st.session_state.missing_kw = top_missing_keywords(resume_text, jd_input, top_n=top_n_keywords)
        st.session_state.sections = extract_sections(resume_text)
        st.session_state.resume_text = resume_text
        st.session_state.jd_text = jd_input
        st.session_state.ai_feedback = ""
        st.session_state.rewrites = {}

# ── Results (rendered from session state — persists across reruns) ────────────
if st.session_state.score is not None:
    score = st.session_state.score
    bullet_scores = st.session_state.bullet_scores
    missing_kw = st.session_state.missing_kw

    # ── Gauge ─────────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Overall Match Score")
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(score * 100, 1),
        number={"suffix": "%"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#4CAF50" if score >= 0.6 else "#FF9800" if score >= 0.4 else "#F44336"},
            "steps": [
                {"range": [0, 40], "color": "#FFEBEE"},
                {"range": [40, 60], "color": "#FFF8E1"},
                {"range": [60, 100], "color": "#E8F5E9"},
            ],
            "threshold": {"line": {"color": "black", "width": 3}, "thickness": 0.75, "value": 60},
        },
        title={"text": "Resume ↔ JD Similarity"},
    ))
    gauge.update_layout(height=280, margin=dict(t=30, b=0))
    st.plotly_chart(gauge, use_container_width=True)

    if score >= 0.6:
        st.success("Strong match — this resume aligns well with the JD.")
    elif score >= 0.4:
        st.warning("Moderate match — improvements recommended.")
    else:
        st.error("Weak match — significant gaps detected.")

    # ── Keywords & Sections ───────────────────────────────────────────────────
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Missing Keywords")
        if missing_kw:
            for kw in missing_kw:
                st.markdown(f"- `{kw}`")
        else:
            st.info("No major keyword gaps found.")

    with col4:
        st.subheader("Detected Sections")
        for sec in st.session_state.sections:
            st.markdown(f"- **{sec.title()}**")

    # ── Bullet scores ─────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Resume Bullet Scores")
    display_bullets = bullet_scores if show_all_bullets else bullet_scores[:10]

    if display_bullets:
        df = pd.DataFrame(display_bullets)
        df["score_pct"] = (df["score"] * 100).round(1)
        df["strength"] = df["score"].apply(
            lambda s: "Strong" if s >= 0.45 else ("OK" if s >= 0.30 else "Weak")
        )
        st.dataframe(
            df[["bullet", "score_pct", "strength"]].rename(
                columns={"bullet": "Resume Bullet", "score_pct": "Match %", "strength": "Strength"}
            ),
            use_container_width=True,
            hide_index=True,
        )

        weak_bullets = [r["bullet"] for r in bullet_scores if r["score"] < 0.30][:3]
        if weak_bullets:
            st.subheader("Suggested Rewrites (Weak Bullets)")
            for idx, b in enumerate(weak_bullets):
                bullet_key = f"bullet_{idx}"
                with st.expander(f"Weak bullet {idx + 1}: {b[:80]}{'...' if len(b) > 80 else ''}"):
                    st.markdown(f"**Original:** {b}")
                    if st.button("Rewrite with LLM", key=f"rw_btn_{idx}", disabled=not groq_api_key):
                        with st.spinner("Rewriting..."):
                            st.session_state.rewrites[bullet_key] = rewrite_bullet(
                                b, st.session_state.jd_text, api_key=groq_api_key
                            )
                    if bullet_key in st.session_state.rewrites:
                        st.success(f"**Rewritten:** {st.session_state.rewrites[bullet_key]}")
    else:
        st.info("No bullet points detected in resume.")

    # ── AI Feedback ───────────────────────────────────────────────────────────
    st.divider()
    st.subheader("AI Coach Feedback")

    if st.button("Generate AI Feedback", type="secondary", disabled=not groq_api_key):
        with st.spinner("Asking Groq (llama3-8b)..."):
            st.session_state.ai_feedback = get_feedback(
                st.session_state.resume_text,
                st.session_state.jd_text,
                missing_kw,
                api_key=groq_api_key,
            )

    if st.session_state.ai_feedback:
        st.text_area("Feedback", value=st.session_state.ai_feedback, height=250)
