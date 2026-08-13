"""
Rule-based error diagnosis.
Maps score reports + lightweight text checks to taxonomy error codes.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

from core.error_taxonomy import get_error_info


ACTION_VERBS = {
    "developed", "managed", "led", "created", "implemented", "improved",
    "designed", "built", "achieved", "increased", "reduced", "optimized",
    "collaborated", "delivered", "launched", "analyzed", "architected",
    "automated", "orchestrated", "spearheaded", "executed", "owned",
}

WEAK_VERBS = {
    "helped", "assisted", "worked", "responsible", "involved", "tasked",
    "handled", "did", "made", "was", "were",
}


def _has_metrics(text: str) -> bool:
    return bool(re.search(r"(\d+%|\$\d+|\d+\s*(k|m|million|users|clients|projects)?)", text.lower()))


def _action_verb_ratio(text: str) -> float:
    words = re.findall(r"[a-zA-Z]+", text.lower())
    if not words:
        return 0.0
    strong = sum(1 for w in words if w in ACTION_VERBS)
    weak = sum(1 for w in words if w in WEAK_VERBS)
    total_signal = strong + weak
    if total_signal == 0:
        return 0.5
    return strong / total_signal


def diagnose_errors(
    resume_text: str,
    score_report: Dict[str, Any],
    previous_score: Optional[float] = None,
    previous_error_code: Optional[str] = None,
    fix_history: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    fix_history = fix_history or []
    text = resume_text or ""
    lower = text.lower()
    errors: List[Dict[str, Any]] = []

    keyword_score = float(score_report.get("keyword_score") or 0)
    structural_score = float(score_report.get("structural_score") or 0)
    overall_score = float(score_report.get("overall_score") or 0)
    missing_keywords = score_report.get("missing_keywords") or []
    structure_checks = score_report.get("structure_checks") or {}

    def add(code: str, section: str, priority: str, extra: str = ""):
        info = get_error_info(code)
        source = "user" if code.startswith("U") else "system"
        desc = info["meaning"]
        if extra:
            desc = f"{desc}. {extra}"
        errors.append({
            "code": code,
            "source": source,
            "label": info["label"],
            "description": desc,
            "section": section,
            "priority": priority,
            "fix_strategy": info["default_fix"],
        })

    if keyword_score < 60:
        extra = ""
        if missing_keywords:
            extra = "Missing examples: " + ", ".join(list(missing_keywords)[:8])
        add("U04_KEYWORD_GAP", "skills_experience", "high", extra)

    if structural_score < 65:
        add("U05_POOR_STRUCTURE", "structure", "high")

    if not structure_checks.get("has_summary", True):
        add("U01_WEAK_SUMMARY", "summary", "medium")
    else:
        if len(text) < 800:
            add("U01_WEAK_SUMMARY", "summary", "medium")

    if not _has_metrics(text):
        add("U02_NO_METRICS", "experience", "high")

    if _action_verb_ratio(text) < 0.35:
        add("U06_WEAK_VERBS", "experience", "medium")

    if not structure_checks.get("has_contact_email", True):
        add("U10_CONTACT_INCOMPLETE", "contact", "medium")

    if len(text) < 400 or len(text) > 6500:
        add("U09_LENGTH_ISSUE", "global", "low")

    if keyword_score < 70 and missing_keywords:
        add("U07_SKILLS_UNFOCUSED", "skills", "medium")

    if not _has_metrics(text) and _action_verb_ratio(text) < 0.4:
        add("U03_TASK_NOT_IMPACT", "experience", "medium")
        add("U08_TOO_VAGUE", "experience", "low")

    if previous_score is not None and overall_score <= previous_score:
        add("S01_NO_SCORE_GAIN", "loop", "high")

    if previous_error_code == "U04_KEYWORD_GAP" and keyword_score < 60:
        add("S02_KEYWORD_STILL_MISSING", "loop", "high")

    if len(fix_history) >= 2:
        last = fix_history[-1].get("error_code")
        prev = fix_history[-2].get("error_code")
        if last and last == prev:
            last_improved = fix_history[-1].get("improved", False)
            if not last_improved:
                add("S05_REPEAT_FIX", "loop", "high")

    seen: Set[str] = set()
    unique: List[Dict[str, Any]] = []
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    errors.sort(key=lambda e: priority_rank.get(e.get("priority", "low"), 3))

    for e in errors:
        if e["code"] not in seen:
            seen.add(e["code"])
            unique.append(e)

    return unique


def select_next_error(active_errors: List[Dict[str, Any]], fix_history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not active_errors:
        return None

    recent_codes = [h.get("error_code") for h in fix_history[-2:]]
    for err in active_errors:
        code = err.get("code")
        if recent_codes.count(code) >= 2:
            continue
        return err
    return active_errors[0]