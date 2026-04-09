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
    Advanced semantic keyword gap detection:
    1. Extracts meaningful technical phrases (1–3 words) from the JD
    2. Filters out jargon, soft-skill filler, and generic words
    3. Uses sentence-transformers to check if the resume semantically covers each phrase
    4. Returns phrases the resume genuinely lacks, ranked by JD frequency
    """
    import re

    # Broad jargon/filler blocklist — words that appear in JDs but carry no technical signal
    JARGON = {
        # generic soft skills & filler
        "ability", "able", "across", "additionally", "agile", "analytical",
        "and", "are", "as", "at", "be", "been", "being", "best", "between",
        "both", "but", "by", "can", "candidate", "collaborative", "communication",
        "company", "complex", "competitive", "cross", "culture", "deep",
        "demonstrated", "desired", "detail", "develop", "drive", "driven",
        "duties", "dynamic", "eager", "end", "ensure", "environment",
        "equivalent", "excellent", "experience", "expertise", "fast",
        "fit", "for", "from", "functional", "good", "great", "grow",
        "growth", "hands", "have", "high", "highly", "ideal", "identify",
        "implement", "in", "including", "individual", "initiative",
        "innovation", "innovative", "into", "is", "it", "join", "key",
        "knowledge", "large", "lead", "leading", "learn", "level", "like",
        "looking", "make", "manage", "management", "may", "minimum",
        "must", "new", "not", "of", "on", "opportunity", "or", "other",
        "our", "out", "own", "passionate", "people", "plus", "proactive",
        "problem", "problems", "proven", "provide", "quality", "related",
        "relevant", "remote", "required", "requirements", "responsibilities",
        "results", "role", "scale", "self", "skills", "solving", "strong",
        "support", "take", "team", "teamwork", "that", "the", "their",
        "they", "this", "time", "to", "together", "tools", "track",
        "understanding", "up", "us", "use", "using", "various", "we",
        "well", "will", "with", "work", "working", "years", "you", "your",
    }

    def is_technical(phrase: str) -> bool:
        """Keep only phrases that look like real technical terms."""
        p = phrase.lower().strip()
        words = p.split()
        # Drop if any word is pure jargon
        if any(w in JARGON for w in words):
            return False
        # Drop pure numbers
        if re.fullmatch(r"[\d\.\-]+", p):
            return False
        # Must have at least one word that's 3+ chars and not a number
        has_substance = any(len(w) >= 3 and not w.isdigit() for w in words)
        return has_substance

    def extract_phrases(text: str) -> list[str]:
        """Extract 1–3 word candidate phrases from text."""
        # Normalise
        text = re.sub(r"[^\w\s\+\#\.\-]", " ", text)
        tokens = text.split()
        phrases = []
        for size in (1, 2, 3):
            for i in range(len(tokens) - size + 1):
                phrase = " ".join(tokens[i: i + size])
                # Keep token-level technical markers (C++, Node.js, scikit-learn, etc.)
                phrase = re.sub(r"\s+", " ", phrase).strip()
                if is_technical(phrase):
                    phrases.append(phrase.lower())
        return phrases

    # Build candidate set from JD, ranked by frequency
    jd_phrases = extract_phrases(jd_text)
    freq: dict[str, int] = {}
    for p in jd_phrases:
        freq[p] = freq.get(p, 0) + 1

    # Keep only phrases that appear ≥2 times OR are multi-word (more specific)
    candidates = [
        p for p, f in sorted(freq.items(), key=lambda x: x[1], reverse=True)
        if f >= 2 or len(p.split()) >= 2
    ]

    if not candidates:
        return []

    # Semantic check: encode candidates + resume sentences
    model = _get_model()
    resume_sentences = [s.strip() for s in re.split(r"[\n\.]+", resume_text) if len(s.strip()) > 15]
    if not resume_sentences:
        resume_sentences = [resume_text]

    candidate_embs = model.encode(candidates, convert_to_tensor=True, show_progress_bar=False)
    resume_embs = model.encode(resume_sentences, convert_to_tensor=True, show_progress_bar=False)

    # For each candidate, find its max similarity to any resume sentence
    sim_matrix = util.cos_sim(candidate_embs, resume_embs)  # [num_candidates x num_sentences]
    max_sims = sim_matrix.max(dim=1).values.tolist()

    # A candidate is "missing" if the resume doesn't semantically cover it
    SEMANTIC_THRESHOLD = 0.40
    missing = [
        candidates[i]
        for i, sim in enumerate(max_sims)
        if sim < SEMANTIC_THRESHOLD
    ]

    # Re-rank missing by JD frequency
    missing_ranked = sorted(missing, key=lambda p: freq.get(p, 0), reverse=True)
    return missing_ranked[:top_n]
