"""
llm_feedback.py
Generates AI feedback using a local Ollama model (e.g. mistral, llama3, gemma).
Ollama must be running locally: https://ollama.com/download
"""

import ollama


DEFAULT_MODEL = "mistral"  # swap to "llama3" or "gemma" if preferred


def _prompt(resume_text: str, jd_text: str, missing_keywords: list[str]) -> str:
    kw_str = ", ".join(missing_keywords) if missing_keywords else "none identified"
    return f"""You are a professional resume coach. A candidate is applying for a job.

--- JOB DESCRIPTION ---
{jd_text[:2000]}

--- RESUME ---
{resume_text[:2000]}

--- MISSING KEYWORDS ---
{kw_str}

Your task:
1. In 2-3 sentences, explain how well the resume matches the job description.
2. List 3 specific resume bullets the candidate should ADD or REWRITE to better match the JD.
3. List 2 skills or experiences from the JD that are completely absent from the resume.

Be concise, actionable, and direct. Use plain text, no markdown headers."""


def get_feedback(
    resume_text: str,
    jd_text: str,
    missing_keywords: list[str],
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Calls local Ollama LLM and returns string feedback.
    Falls back to a static message if Ollama is not running.
    """
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": _prompt(resume_text, jd_text, missing_keywords)}],
        )
        return response["message"]["content"].strip()
    except Exception as e:
        return (
            f"[LLM unavailable: {e}]\n\n"
            "To enable AI feedback, install Ollama (https://ollama.com) and run:\n"
            f"  ollama pull {model}\n"
            "  ollama serve"
        )


def rewrite_bullet(bullet: str, jd_text: str, model: str = DEFAULT_MODEL) -> str:
    """
    Takes a weak resume bullet and rewrites it to better match the JD.
    """
    prompt = f"""Rewrite this resume bullet to better match the job description below.
Keep it under 20 words. Start with a strong action verb. Be specific and quantified if possible.

Job Description (excerpt):
{jd_text[:800]}

Original bullet:
{bullet}

Rewritten bullet:"""

    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"].strip()
    except Exception as e:
        return f"[LLM unavailable: {e}]"
