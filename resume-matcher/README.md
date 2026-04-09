# Resume Matcher

An AI-powered tool that analyzes how well your resume matches a job description — using semantic similarity, keyword gap analysis, and local LLM coaching. Runs 100% locally with no API keys required.

## Features

- **Semantic Matching** — compares resume and job description using `all-MiniLM-L6-v2` (sentence-transformers)
- **Per-Bullet Scoring** — scores every resume bullet against the JD and flags weak ones
- **Keyword Gap Analysis** — identifies important JD keywords missing from your resume
- **Section Detection** — automatically detects Experience, Skills, Education, etc.
- **AI Coach Feedback** — generates actionable improvement suggestions via a local LLM (Ollama)
- **Bullet Rewriter** — rewrites weak bullets to better match the JD
- **Interactive UI** — clean Streamlit interface with a match score gauge chart

## Tech Stack

| Component | Tool |
|---|---|
| Semantic similarity | `sentence-transformers` (all-MiniLM-L6-v2) |
| Resume parsing | `pdfplumber`, `python-docx` |
| Local LLM | Ollama (Mistral / LLaMA 3 / Gemma) |
| UI | Streamlit + Plotly |
| ML utilities | scikit-learn, PyTorch |

## Project Structure

```
resume-matcher/
├── app.py              # Streamlit UI
├── matcher.py          # Semantic similarity engine
├── llm_feedback.py     # Local LLM feedback via Ollama
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

### 3. (Optional) Set up Ollama for AI feedback

Download Ollama from [ollama.com](https://ollama.com), then:

```bash
ollama pull mistral
ollama serve
```

> The app works without Ollama — AI feedback will simply show a fallback message.

### 4. Run the app

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

## Usage

1. Upload your resume (PDF or DOCX) or paste the text directly
2. Paste the job description
3. Click **Analyze Match**
   - View your match score (0–100%)
   - See missing keywords
   - Review per-bullet scores
   - Click "Rewrite with LLM" on weak bullets
4. Click **Generate AI Feedback** for coaching advice

## Score Interpretation

| Score | Meaning |
|---|---|
| 60%+ | Strong match |
| 40–60% | Moderate match — improvements recommended |
| Below 40% | Weak match — significant gaps detected |

## License

MIT
