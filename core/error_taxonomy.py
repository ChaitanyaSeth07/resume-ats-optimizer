"""
Error Taxonomy for Resume ATS Optimizer

Fixed label set for user-side and system-side mistakes.
Used by diagnosis, LangGraph repair loop, and error memory.
"""

from typing import Dict, List


USER_ERRORS: Dict[str, Dict[str, str]] = {
    "U01_WEAK_SUMMARY": {
        "label": "Weak summary",
        "meaning": "Generic or objective-style summary with little targeted value",
        "default_fix": "Rewrite summary to highlight relevant strengths aligned to the job description without inventing experience",
    },
    "U02_NO_METRICS": {
        "label": "Missing metrics",
        "meaning": "Bullets lack numbers, scale, or measurable outcomes",
        "default_fix": "Strengthen bullets with truthful scope/impact; add metrics only if implied by existing content, never invent numbers",
    },
    "U03_TASK_NOT_IMPACT": {
        "label": "Task-only bullets",
        "meaning": "Duties listed instead of achievements or impact",
        "default_fix": "Convert task descriptions into achievement-oriented bullets using strong verbs and clear outcomes",
    },
    "U04_KEYWORD_GAP": {
        "label": "Keyword gap",
        "meaning": "Important job-description terms are missing from the resume",
        "default_fix": "Naturally integrate missing keywords into skills and experience where truthful and relevant",
    },
    "U05_POOR_STRUCTURE": {
        "label": "Poor structure",
        "meaning": "Missing standard sections or unclear headings",
        "default_fix": "Reorganize into clear standard sections: Summary, Experience, Education, Skills",
    },
    "U06_WEAK_VERBS": {
        "label": "Weak verbs",
        "meaning": "Passive or soft language in experience bullets",
        "default_fix": "Replace weak/passive phrasing with strong action verbs while keeping facts truthful",
    },
    "U07_SKILLS_UNFOCUSED": {
        "label": "Unfocused skills",
        "meaning": "Skills list not aligned to the job description",
        "default_fix": "Prioritize and group skills to match job-description requirements",
    },
    "U08_TOO_VAGUE": {
        "label": "Vague content",
        "meaning": "Claims without evidence, scope, or specificity",
        "default_fix": "Add specificity and concrete context without inventing employers, titles, or metrics",
    },
    "U09_LENGTH_ISSUE": {
        "label": "Length issue",
        "meaning": "Resume content is too short or excessively long",
        "default_fix": "Tighten verbose sections or expand thin sections with truthful detail",
    },
    "U10_CONTACT_INCOMPLETE": {
        "label": "Contact incomplete",
        "meaning": "Missing email, phone, or other key contact details",
        "default_fix": "Preserve and clearly present available contact fields; do not invent contact data",
    },
}


SYSTEM_ERRORS: Dict[str, Dict[str, str]] = {
    "S01_NO_SCORE_GAIN": {
        "label": "No score gain",
        "meaning": "Rewrite did not improve overall score",
        "default_fix": "Try a different repair strategy focused on the highest-priority remaining error",
    },
    "S02_KEYWORD_STILL_MISSING": {
        "label": "Keywords still missing",
        "meaning": "Targeted keywords were not successfully incorporated",
        "default_fix": "Explicitly weave the remaining missing keywords into skills and relevant bullets",
    },
    "S03_OVERGENERIC": {
        "label": "Over-generic rewrite",
        "meaning": "Language became fluffy or generic after optimization",
        "default_fix": "Reduce fluff; restore concrete, role-specific wording from original content",
    },
    "S04_STRUCTURE_REGRESSED": {
        "label": "Structure regressed",
        "meaning": "Section clarity worsened after rewrite",
        "default_fix": "Restore standard section headings and clean section boundaries",
    },
    "S05_REPEAT_FIX": {
        "label": "Repeated same fix",
        "meaning": "Same repair was attempted again with no meaningful change",
        "default_fix": "Switch error target or strategy; avoid repeating the identical fix",
    },
    "S06_HALLUCINATION_RISK": {
        "label": "Hallucination risk",
        "meaning": "Possible invented metrics or experience detected",
        "default_fix": "Remove unverifiable additions; keep only content grounded in the original resume",
    },
    "S07_PARTIAL_SECTION_FIX": {
        "label": "Partial section fix",
        "meaning": "Only one section improved while others remain weak",
        "default_fix": "Apply the next fix to a different weak section",
    },
}


ALL_ERRORS = {**USER_ERRORS, **SYSTEM_ERRORS}


def get_error_info(code: str) -> Dict[str, str]:
    return ALL_ERRORS.get(code, {
        "label": code,
        "meaning": "Unknown error",
        "default_fix": "Improve clarity, relevance, and ATS alignment without inventing facts",
    })


def list_user_error_codes() -> List[str]:
    return list(USER_ERRORS.keys())


def list_system_error_codes() -> List[str]:
    return list(SYSTEM_ERRORS.keys())


def is_valid_error_code(code: str) -> bool:
    return code in ALL_ERRORS