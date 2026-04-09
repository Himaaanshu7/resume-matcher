"""
llm_feedback.py
Generates AI feedback using google/flan-t5-base locally via HuggingFace transformers.
No API key, no Ollama needed — model downloads once (~250MB) and is cached.
"""

from transformers import pipeline
import torch

_pipe = None


def _get_pipeline():
    global _pipe
    if _pipe is None:
        device = 0 if torch.cuda.is_available() else -1
        _pipe = pipeline(
            "text2text-generation",
            model="google/flan-t5-base",
            device=device,
            max_new_tokens=256,
        )
    return _pipe


def get_feedback(
    resume_text: str,
    jd_text: str,
    missing_keywords: list[str],
    model: str = None,  # kept for API compatibility, unused
) -> str:
    """
    Returns coaching feedback comparing the resume to the JD.
    """
    kw_str = ", ".join(missing_keywords[:10]) if missing_keywords else "none"

    prompt = f"""You are a resume coach. Given the job description and resume below, do three things:
1. In 2 sentences say how well the resume matches the job.
2. List 3 specific bullets the candidate should add or improve.
3. List 2 skills from the job description missing from the resume.

Job Description: {jd_text[:800]}

Resume: {resume_text[:800]}

Missing keywords: {kw_str}

Feedback:"""

    try:
        pipe = _get_pipeline()
        result = pipe(prompt, max_new_tokens=256, do_sample=False)
        return result[0]["generated_text"].strip()
    except Exception as e:
        return f"[Error generating feedback: {e}]"


def rewrite_bullet(bullet: str, jd_text: str, model: str = None) -> str:
    """
    Rewrites a weak resume bullet to better match the JD.
    """
    prompt = f"""Rewrite this resume bullet to better match the job description.
Use a strong action verb. Be specific. Keep it under 20 words.

Job description keywords: {jd_text[:400]}

Original bullet: {bullet}

Rewritten bullet:"""

    try:
        pipe = _get_pipeline()
        result = pipe(prompt, max_new_tokens=80, do_sample=False)
        return result[0]["generated_text"].strip()
    except Exception as e:
        return f"[Error rewriting bullet: {e}]"
