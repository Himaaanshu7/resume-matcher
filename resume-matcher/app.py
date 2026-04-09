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

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Resume Matcher",
    page_icon="📄",
    layout="wide",
)

st.title("AI Resume & Job Description Matcher")
st.caption("100% local · free · powered by sentence-transformers + Ollama")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    llm_model = st.selectbox(
        "Local LLM model (Ollama)",
        ["mistral", "llama3", "gemma", "phi3", "tinyllama"],
        index=0,
    )
    top_n_keywords = st.slider("Missing keywords to show", 5, 20, 10)
    show_all_bullets = st.checkbox("Show all bullet scores", value=False)

# ── Input columns ─────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Resume")
    resume_file = st.file_uploader(
        "Upload PDF or DOCX", type=["pdf", "docx", "txt"], key="resume"
    )
    resume_text_input = st.text_area(
        "Or paste resume text", height=200, key="resume_text"
    )

with col2:
    st.subheader("Job Description")
    jd_text = st.text_area("Paste job description here", height=300, key="jd")

# ── Resolve resume text ───────────────────────────────────────────────────────
resume_text = ""
if resume_file:
    resume_text = extract_text(resume_file)
elif resume_text_input.strip():
    resume_text = resume_text_input.strip()

# ── Analyze button ────────────────────────────────────────────────────────────
analyze = st.button("Analyze Match", type="primary", disabled=not (resume_text and jd_text))

if analyze:
    with st.spinner("Computing similarity..."):
        score = overall_score(resume_text, jd_text)
        bullets = extract_bullets(resume_text)
        bullet_scores = score_bullets(bullets, jd_text)
        missing_kw = top_missing_keywords(resume_text, jd_text, top_n=top_n_keywords)

    # ── Score gauge ───────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Overall Match Score")

    gauge = go.Figure(
        go.Indicator(
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
                "threshold": {
                    "line": {"color": "black", "width": 3},
                    "thickness": 0.75,
                    "value": 60,
                },
            },
            title={"text": "Resume ↔ JD Similarity"},
        )
    )
    gauge.update_layout(height=280, margin=dict(t=30, b=0))
    st.plotly_chart(gauge, use_container_width=True)

    if score >= 0.6:
        st.success("Strong match — this resume aligns well with the JD.")
    elif score >= 0.4:
        st.warning("Moderate match — improvements recommended.")
    else:
        st.error("Weak match — significant gaps detected.")

    # ── Sections & keyword gaps ───────────────────────────────────────────────
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
        sections = extract_sections(resume_text)
        for sec in sections:
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

        # Rewrite weak bullets
        weak_bullets = [r["bullet"] for r in bullet_scores if r["score"] < 0.30][:3]
        if weak_bullets:
            st.subheader("Suggested Rewrites (Weak Bullets)")
            for b in weak_bullets:
                with st.expander(f"Original: {b[:80]}..."):
                    if st.button("Rewrite with LLM", key=f"rw_{b[:20]}"):
                        with st.spinner("Rewriting..."):
                            rewritten = rewrite_bullet(b, jd_text, model=llm_model)
                        st.success(rewritten)
    else:
        st.info("No bullet points detected in resume.")

    # ── LLM Feedback ─────────────────────────────────────────────────────────
    st.divider()
    st.subheader("AI Coach Feedback")

    if st.button("Generate AI Feedback", type="secondary"):
        with st.spinner(f"Asking {llm_model} locally..."):
            feedback = get_feedback(resume_text, jd_text, missing_kw, model=llm_model)
        st.text_area("Feedback", value=feedback, height=250)
