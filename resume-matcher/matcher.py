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
    Tech-focused keyword gap detection:
    1. Scans JD for known technologies, tools, languages, frameworks, platforms
    2. Checks each against the resume using exact + semantic matching
    3. Returns only real tech skills that are genuinely missing
    """
    import re

    # ── Comprehensive tech taxonomy ───────────────────────────────────────────
    TECH_VOCAB = {
        # Languages
        "python", "r", "java", "javascript", "typescript", "c", "c++", "c#",
        "go", "golang", "rust", "swift", "kotlin", "scala", "ruby", "php",
        "perl", "bash", "shell", "powershell", "matlab", "julia", "groovy",
        "dart", "lua", "haskell", "elixir", "clojure", "f#", "vba", "cobol",
        "fortran", "assembly", "solidity",

        # Web frontend
        "react", "angular", "vue", "vue.js", "react.js", "next.js", "nuxt.js",
        "svelte", "html", "css", "sass", "scss", "tailwind", "bootstrap",
        "webpack", "vite", "babel", "jquery", "redux", "graphql",

        # Web backend
        "node.js", "express", "django", "flask", "fastapi", "spring", "spring boot",
        "rails", "ruby on rails", "laravel", "asp.net", ".net", "nestjs",
        "fastify", "tornado", "aiohttp",

        # Databases
        "sql", "mysql", "postgresql", "postgres", "sqlite", "oracle", "sql server",
        "mongodb", "cassandra", "redis", "elasticsearch", "dynamodb", "firestore",
        "neo4j", "couchdb", "influxdb", "mariadb", "hbase", "snowflake",
        "bigquery", "redshift", "clickhouse", "supabase",

        # Cloud & DevOps
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
        "terraform", "ansible", "jenkins", "github actions", "gitlab ci",
        "circleci", "helm", "prometheus", "grafana", "datadog", "splunk",
        "nginx", "apache", "linux", "unix", "ci/cd", "devops", "sre",
        "cloudformation", "pulumi", "vagrant", "chef", "puppet",

        # Data & ML
        "pandas", "numpy", "scikit-learn", "sklearn", "tensorflow", "pytorch",
        "keras", "xgboost", "lightgbm", "catboost", "huggingface", "transformers",
        "opencv", "nltk", "spacy", "spark", "pyspark", "hadoop", "kafka",
        "airflow", "dbt", "mlflow", "kubeflow", "sagemaker", "databricks",
        "tableau", "power bi", "looker", "matplotlib", "seaborn", "plotly",
        "jupyter", "dask", "ray", "langchain", "openai", "llm", "rag",

        # APIs & protocols
        "rest", "rest api", "graphql", "grpc", "soap", "websocket", "oauth",
        "jwt", "openapi", "swagger",

        # Mobile
        "android", "ios", "react native", "flutter", "xamarin", "ionic",

        # Testing
        "pytest", "junit", "selenium", "cypress", "jest", "mocha",
        "unit testing", "integration testing", "tdd", "bdd",

        # Version control & tools
        "git", "github", "gitlab", "bitbucket", "jira", "confluence",
        "postman", "linux", "bash scripting",

        # Architecture & concepts
        "microservices", "serverless", "event-driven", "message queue",
        "rabbitmq", "celery", "etl", "elt", "data pipeline", "data warehouse",
        "machine learning", "deep learning", "nlp", "computer vision",
        "reinforcement learning", "generative ai", "vector database",
        "pinecone", "weaviate", "chromadb",

        # Domains
        "blockchain", "web3", "cybersecurity", "networking", "embedded systems",
    }

    # Multi-word terms need special handling — build a lookup set
    MULTI_WORD_TECH = {t for t in TECH_VOCAB if " " in t}
    SINGLE_WORD_TECH = {t for t in TECH_VOCAB if " " not in t}

    def normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower().strip())

    def find_tech_in_text(text: str) -> set[str]:
        """Find all known tech terms present in a block of text."""
        text_lower = text.lower()
        found = set()
        # Single-word exact match (word boundary)
        for term in SINGLE_WORD_TECH:
            if re.search(rf"\b{re.escape(term)}\b", text_lower):
                found.add(term)
        # Multi-word exact match
        for term in MULTI_WORD_TECH:
            if term in text_lower:
                found.add(term)
        return found

    jd_tech = find_tech_in_text(jd_text)
    resume_tech = find_tech_in_text(resume_text)

    # Exact missing: in JD but not in resume
    exact_missing = jd_tech - resume_tech

    if not exact_missing:
        return []

    # Semantic check: even if the exact term is missing, the resume might
    # describe the same concept differently (e.g. "sklearn" vs "scikit-learn")
    model = _get_model()
    candidates = sorted(exact_missing)
    resume_sentences = [s.strip() for s in re.split(r"[\n\.]+", resume_text) if len(s.strip()) > 10]
    if not resume_sentences:
        resume_sentences = [resume_text]

    candidate_embs = model.encode(candidates, convert_to_tensor=True, show_progress_bar=False)
    resume_embs = model.encode(resume_sentences, convert_to_tensor=True, show_progress_bar=False)

    sim_matrix = util.cos_sim(candidate_embs, resume_embs)
    max_sims = sim_matrix.max(dim=1).values.tolist()

    SEMANTIC_THRESHOLD = 0.55  # tighter threshold for known tech terms
    truly_missing = [
        candidates[i]
        for i, sim in enumerate(max_sims)
        if sim < SEMANTIC_THRESHOLD
    ]

    # Rank by frequency in JD (most-mentioned = most important)
    def jd_freq(term: str) -> int:
        return len(re.findall(rf"\b{re.escape(term)}\b", jd_text.lower()))

    truly_missing.sort(key=jd_freq, reverse=True)
    return truly_missing[:top_n]
