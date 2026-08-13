"""
LangGraph-compatible state schema for the resume optimization pipeline.
"""

from typing import TypedDict, List, Dict, Optional, Any


class ResumeGraphState(TypedDict, total=False):
    original_text: str
    job_description: str
    structured_resume: Dict[str, Any]
    design_options: Dict[str, Any]

    current_resume: str
    previous_resume: Optional[str]

    score_report: Dict[str, Any]
    previous_score: Optional[float]
    target_score: float

    active_errors: List[Dict[str, Any]]
    selected_error: Optional[Dict[str, Any]]
    retrieved_patterns: List[Dict[str, Any]]

    attempt: int
    max_attempts: int
    fix_history: List[Dict[str, Any]]

    final_resume: Optional[str]
    stop_reason: Optional[str]


def initial_state(
    original_text: str,
    job_description: str,
    structured_resume: Dict[str, Any],
    target_score: float = 75.0,
    max_attempts: int = 3,
    design_options: Optional[Dict[str, Any]] = None,
) -> ResumeGraphState:
    return {
        "original_text": original_text,
        "job_description": job_description,
        "structured_resume": structured_resume,
        "design_options": design_options or {},
        "current_resume": "",
        "previous_resume": None,
        "score_report": {},
        "previous_score": None,
        "target_score": float(target_score),
        "active_errors": [],
        "selected_error": None,
        "retrieved_patterns": [],
        "attempt": 0,
        "max_attempts": int(max_attempts),
        "fix_history": [],
        "final_resume": None,
        "stop_reason": None,
    }