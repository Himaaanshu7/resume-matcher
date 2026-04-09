"""
matcher.py
Computes semantic similarity between resume text/bullets and a job description
using sentence-transformers (all-MiniLM-L6-v2, free & local).
"""

from sentence_transformers import SentenceTransformer, util
import torch

_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def overall_score(resume_text: str, jd_text: str) -> float:
    """
    Returns cosine similarity [0.0 – 1.0] between the full resume and JD.
    """
    model = _get_model()
    embs = model.encode([resume_text, jd_text], convert_to_tensor=True)
    score = util.cos_sim(embs[0], embs[1]).item()
    return round(score, 4)


def score_bullets(bullets: list[str], jd_text: str) -> list[dict]:
    """
    Scores each resume bullet against the JD.
    Returns list of dicts sorted by score descending:
      [{"bullet": str, "score": float}, ...]
    """
    if not bullets:
        return []

    model = _get_model()
    jd_emb = model.encode(jd_text, convert_to_tensor=True)
    bullet_embs = model.encode(bullets, convert_to_tensor=True)

    scores = util.cos_sim(bullet_embs, jd_emb).squeeze(1).tolist()
    if isinstance(scores, float):
        scores = [scores]

    results = [
        {"bullet": b, "score": round(s, 4)}
        for b, s in zip(bullets, scores)
    ]
    return sorted(results, key=lambda x: x["score"], reverse=True)


def top_missing_keywords(resume_text: str, jd_text: str, top_n: int = 10) -> list[str]:
    """
    Simple keyword gap: returns words present in JD but absent in resume.
    Filters stopwords and short tokens.
    """
    import re

    STOPWORDS = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "is", "are", "was", "be", "by", "as", "we", "you",
        "your", "our", "will", "have", "has", "that", "this", "it", "from",
    }

    def tokenize(text: str) -> set[str]:
        tokens = re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#\-\.]{2,}\b", text.lower())
        return {t for t in tokens if t not in STOPWORDS}

    jd_words = tokenize(jd_text)
    resume_words = tokenize(resume_text)
    missing = jd_words - resume_words

    # Rank missing words by how often they appear in JD
    import re as _re
    freq = {
        w: len(_re.findall(rf"\b{w}\b", jd_text.lower()))
        for w in missing
    }
    ranked = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in ranked[:top_n]]
