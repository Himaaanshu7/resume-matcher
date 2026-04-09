"""
llm_feedback.py
Generates AI feedback using Groq's free API (llama3-8b).
Get a free API key at: https://console.groq.com  (no credit card needed)
Enter the key in the Streamlit sidebar — no .env file required.
"""

from groq import Groq


def _client(api_key: str) -> Groq:
    return Groq(api_key=api_key)


def _chat(api_key: str, prompt: str, max_tokens: int = 400) -> str:
    client = _client(api_key)
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def get_feedback(
    resume_text: str,
    jd_text: str,
    missing_keywords: list[str],
    api_key: str = "",
) -> str:
    if not api_key:
        return (
            "No Groq API key provided.\n\n"
            "Get a FREE key at https://console.groq.com (no credit card needed),\n"
            "then paste it into the API Key field in the sidebar."
        )

    kw_str = ", ".join(missing_keywords[:10]) if missing_keywords else "none"
    prompt = f"""You are a professional resume coach. A candidate is applying for the job below.

JOB DESCRIPTION:
{jd_text[:1200]}

RESUME:
{resume_text[:1200]}

MISSING KEYWORDS: {kw_str}

Give feedback in exactly this format:
1. Match summary (2 sentences): how well the resume fits the role.
2. 3 specific bullet points the candidate should ADD or REWRITE with examples.
3. 2 critical skills/experiences from the JD completely absent from the resume.

Be direct and actionable."""

    try:
        return _chat(api_key, prompt, max_tokens=450)
    except Exception as e:
        return f"[Groq API error: {e}]"


def rewrite_bullet(bullet: str, jd_text: str, api_key: str = "") -> str:
    if not api_key:
        return (
            "No Groq API key provided. "
            "Add your free key from https://console.groq.com in the sidebar."
        )

    prompt = f"""Rewrite this resume bullet to better match the job description.
Rules: start with a strong action verb, be specific, keep it under 20 words, quantify if possible.

Job Description (excerpt): {jd_text[:500]}

Original bullet: {bullet}

Rewritten bullet (one line only):"""

    try:
        return _chat(api_key, prompt, max_tokens=60)
    except Exception as e:
        return f"[Groq API error: {e}]"
