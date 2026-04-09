"""
resume_parser.py
Extracts plain text from PDF, DOCX, or raw text resumes.
"""

import re
import pdfplumber
import docx
from io import BytesIO


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file given its raw bytes."""
    text_parts = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file given its raw bytes."""
    doc = docx.Document(BytesIO(file_bytes))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs)


def extract_text(uploaded_file) -> str:
    """
    Auto-detect file type and extract text.
    Accepts a Streamlit UploadedFile object.
    """
    file_bytes = uploaded_file.read()
    name = uploaded_file.name.lower()

    if name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif name.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    else:
        # Assume plain text
        return file_bytes.decode("utf-8", errors="ignore")


def extract_bullets(resume_text: str) -> list[str]:
    """
    Pull out bullet-point lines from the resume text.
    Handles •, -, *, and numbered list items.
    """
    lines = resume_text.splitlines()
    bullets = []
    bullet_pattern = re.compile(r"^\s*([•\-\*]|\d+[\.\)])\s+(.+)")

    for line in lines:
        match = bullet_pattern.match(line)
        if match:
            bullets.append(match.group(2).strip())
        elif len(line.strip()) > 40:
            # Include long non-bulleted lines (likely experience descriptions)
            bullets.append(line.strip())

    return [b for b in bullets if len(b) > 20]


def extract_sections(resume_text: str) -> dict[str, str]:
    """
    Attempt to split resume into named sections.
    Returns a dict like {'experience': '...', 'skills': '...', ...}
    """
    section_headers = [
        "experience", "education", "skills", "projects",
        "summary", "objective", "certifications", "awards",
        "publications", "volunteer", "languages",
    ]
    pattern = re.compile(
        r"(?im)^(" + "|".join(section_headers) + r")[:\s]*$"
    )

    sections: dict[str, str] = {}
    current_section = "header"
    current_lines: list[str] = []

    for line in resume_text.splitlines():
        header_match = pattern.match(line.strip().lower())
        if header_match:
            sections[current_section] = "\n".join(current_lines).strip()
            current_section = header_match.group(1).lower()
            current_lines = []
        else:
            current_lines.append(line)

    sections[current_section] = "\n".join(current_lines).strip()
    return {k: v for k, v in sections.items() if v}
