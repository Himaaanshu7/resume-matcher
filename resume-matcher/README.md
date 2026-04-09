# Resume Matcher

An AI-powered tool that analyzes how well your resume matches a job description — using semantic similarity, keyword gap analysis, and LLM coaching.

**Live Demo:** https://resume-matcher-pdjd3nkkyhwlxdmfztladr.streamlit.app/

## Features

- **Semantic Matching** — compares resume and job description using `all-MiniLM-L6-v2` (sentence-transformers)
- **Per-Bullet Scoring** — scores every resume bullet against the JD and flags weak ones
- **Tech Keyword Gap Analysis** — identifies missing technologies, tools, and frameworks from the JD
- **Section Detection** — automatically detects Experience, Skills, Education, etc.
- **AI Coach Feedback** — generates actionable improvement suggestions via Groq (llama-3.1-8b)
- **Bullet Rewriter** — rewrites weak bullets to better match the JD
- **Interactive UI** — clean Streamlit interface with a match score gauge chart

## Tech Stack

| Component | Tool |
|---|---|
| Semantic similarity | `sentence-transformers` (all-MiniLM-L6-v2) |
| Resume parsing | `pdfplumber`, `python-docx` |
| AI feedback | Groq API (llama-3.1-8b-instant) |
| UI | Streamlit + Plotly |
| ML utilities | scikit-learn, PyTorch |

## Project Structure

```
resume-matcher/
├── app.py              # Streamlit UI
├── matcher.py          # Semantic similarity + keyword gap engine
├── llm_feedback.py     # Groq LLM feedback and bullet rewriter
├── resume_parser.py    # PDF / DOCX / text extraction
└── requirements.txt    # Dependencies
```

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/Himaaanshu7/resume-matcher.git
cd resume-matcher
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up Groq API key

Get a free key at [console.groq.com](https://console.groq.com) (no credit card needed).

For local development, create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "gsk_your_key_here"
```

> Without a key, the match score and keyword analysis still work — only AI feedback and bullet rewrite are disabled.

### 4. Run the app

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

## Deploying to Streamlit Cloud

1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Set main file path to `resume-matcher/app.py`
4. Go to **Settings → Secrets** and add:
```toml
GROQ_API_KEY = "gsk_your_key_here"
```
5. Click **Deploy**

## Usage

1. Upload your resume (PDF or DOCX) or paste the text directly
2. Paste the job description
3. Click **Analyze Match**
   - View your match score (0–100%)
   - See missing tech keywords
   - Review per-bullet scores
   - Click **Rewrite with LLM** on weak bullets
4. Click **Generate AI Feedback** for coaching advice

## Score Interpretation

| Score | Meaning |
|---|---|
| 60%+ | Strong match |
| 40–60% | Moderate match — improvements recommended |
| Below 40% | Weak match — significant gaps detected |

## License

MIT
