"""
Scoring Engine Module
Evaluates how ATS-friendly and job-relevant the resume is.
"""

import re
from typing import Dict, List, Tuple
from collections import Counter


def extract_keywords(text: str, top_n: int = 30) -> List[str]:
    """
    Extract important keywords from text (simple version).
    Removes common stop words and short words.
    """
    stop_words = {
        "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
        "have", "has", "had", "will", "would", "can", "could", "should", "may",
        "our", "you", "your", "they", "their", "what", "which", "when", "where",
        "who", "how", "all", "any", "both", "each", "few", "more", "most", "other",
        "some", "such", "than", "too", "very", "just", "about", "into", "over",
        "after", "before", "between", "under", "again", "further", "then", "once",
        "here", "there", "also", "been", "being", "have", "does", "did", "doing",
        "a", "an", "of", "in", "on", "at", "to", "by", "as", "is", "it", "or", "be"
    }

    # Clean and tokenize
    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9\-\+]{2,}\b", text.lower())
    words = [w for w in words if w not in stop_words]

    # Count frequency
    counter = Counter(words)
    return [word for word, _ in counter.most_common(top_n)]


def keyword_match_score(resume_text: str, job_description: str) -> Tuple[float, List[str], List[str]]:
    """
    Calculate how many important keywords from the job description appear in the resume.
    
    Returns:
        score (0-100), matched keywords, missing keywords
    """
    job_keywords = extract_keywords(job_description, top_n=25)
    resume_lower = resume_text.lower()

    matched = []
    missing = []

    for kw in job_keywords:
        if kw in resume_lower:
            matched.append(kw)
        else:
            missing.append(kw)

    if not job_keywords:
        return 50.0, [], []

    score = (len(matched) / len(job_keywords)) * 100
    return round(score, 1), matched, missing


def structural_score(resume_text: str) -> Tuple[float, Dict[str, bool]]:
    """
    Check basic ATS-friendly structural elements.
    """
    text_lower = resume_text.lower()

    checks = {
        "has_summary": any(h in text_lower for h in ["summary", "profile", "objective"]),
        "has_experience": any(h in text_lower for h in ["experience", "employment", "work history"]),
        "has_education": "education" in text_lower,
        "has_skills": "skill" in text_lower,
        "has_contact_email": bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", resume_text)),
        "has_phone": bool(re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", resume_text)),
        "uses_action_verbs": any(v in text_lower for v in [
            "developed", "managed", "led", "created", "implemented", "improved",
            "designed", "built", "achieved", "increased", "reduced", "optimized",
            "collaborated", "delivered", "launched", "analyzed"
        ]),
        "not_too_short": len(resume_text) > 400,
        "not_too_long": len(resume_text) < 6000,
    }

    passed = sum(1 for v in checks.values() if v)
    score = (passed / len(checks)) * 100
    return round(score, 1), checks


def calculate_overall_score(resume_text: str, job_description: str) -> Dict:
    """
    Main scoring function.
    
    Returns a detailed score report.
    """
    kw_score, matched, missing = keyword_match_score(resume_text, job_description)
    struct_score, structure_checks = structural_score(resume_text)

    # Weighted overall score
    # Keyword match is more important for job targeting
    overall = (kw_score * 0.65) + (struct_score * 0.35)
    overall = round(overall, 1)

    # Simple rating
    if overall >= 80:
        rating = "Excellent"
    elif overall >= 65:
        rating = "Good"
    elif overall >= 50:
        rating = "Average"
    else:
        rating = "Needs Improvement"

    return {
        "overall_score": overall,
        "rating": rating,
        "keyword_score": kw_score,
        "structural_score": struct_score,
        "matched_keywords": matched,
        "missing_keywords": missing[:10],  # show top missing
        "structure_checks": structure_checks,
        "needs_improvement": overall < 70
    }