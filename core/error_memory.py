"""
JSON-based Error Memory (Phase 1)

Stores anonymized error patterns and fix outcomes only.
No resume text, names, emails, or full job descriptions.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.error_taxonomy import ALL_ERRORS, get_error_info

MEMORY_FILE = "error_memory.json"


def _default_seed_patterns() -> List[Dict[str, Any]]:
    seeds = []
    for code, meta in ALL_ERRORS.items():
        source = "user" if code.startswith("U") else "system"
        seeds.append({
            "id": f"seed_{code}",
            "error_code": code,
            "source": source,
            "description": meta["meaning"],
            "fix_strategy": meta["default_fix"],
            "job_family": "general",
            "times_seen": 1,
            "times_succeeded": 0,
            "times_failed": 0,
            "avg_score_gain": 0.0,
            "success_rate": 0.0,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "seed": True,
        })
    return seeds


def _ensure_memory_file(path: str = MEMORY_FILE) -> None:
    if not os.path.exists(path):
        data = {"patterns": _default_seed_patterns()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def load_memory(path: str = MEMORY_FILE) -> Dict[str, Any]:
    _ensure_memory_file(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(data: Dict[str, Any], path: str = MEMORY_FILE) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _tokenize(text: str) -> set:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9\+\#\.]{1,}", (text or "").lower())
    stop = {
        "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
        "have", "has", "had", "will", "would", "can", "could", "should", "a", "an",
        "of", "in", "on", "at", "to", "by", "as", "is", "it", "or", "be", "into",
    }
    return {w for w in words if w not in stop and len(w) > 2}


def _similarity(query: str, pattern: Dict[str, Any]) -> float:
    q = _tokenize(query)
    p = _tokenize(
        f"{pattern.get('error_code', '')} {pattern.get('description', '')} "
        f"{pattern.get('fix_strategy', '')} {pattern.get('job_family', '')}"
    )
    if not q or not p:
        return 0.0
    overlap = len(q & p)
    return overlap / max(len(q), 1)


def retrieve_similar_patterns(
    error_code: str,
    description: str = "",
    job_family: str = "general",
    top_k: int = 3,
    path: str = MEMORY_FILE,
) -> List[Dict[str, Any]]:
    data = load_memory(path)
    patterns = data.get("patterns", [])

    query = f"{error_code} {description} {job_family}"
    scored = []

    for pat in patterns:
        score = 0.0
        if pat.get("error_code") == error_code:
            score += 2.0
        if pat.get("job_family") == job_family:
            score += 0.5
        score += _similarity(query, pat)
        score += float(pat.get("success_rate", 0.0))
        scored.append((score, pat))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:top_k]]


def log_fix_outcome(
    error_code: str,
    description: str,
    fix_strategy: str,
    score_before: float,
    score_after: float,
    job_family: str = "general",
    source: str = "user",
    path: str = MEMORY_FILE,
) -> Dict[str, Any]:
    data = load_memory(path)
    patterns = data.get("patterns", [])
    improved = score_after > score_before
    gain = float(score_after) - float(score_before)

    existing = None
    for pat in patterns:
        if (
            not pat.get("seed")
            and pat.get("error_code") == error_code
            and pat.get("job_family") == job_family
            and pat.get("fix_strategy") == fix_strategy
        ):
            existing = pat
            break

    now = datetime.utcnow().isoformat() + "Z"

    if existing is None:
        info = get_error_info(error_code)
        existing = {
            "id": f"pat_{error_code}_{len(patterns)+1}",
            "error_code": error_code,
            "source": source if source in {"user", "system"} else "user",
            "description": description or info.get("meaning", ""),
            "fix_strategy": fix_strategy or info.get("default_fix", ""),
            "job_family": job_family or "general",
            "times_seen": 0,
            "times_succeeded": 0,
            "times_failed": 0,
            "avg_score_gain": 0.0,
            "success_rate": 0.0,
            "created_at": now,
            "updated_at": now,
            "seed": False,
        }
        patterns.append(existing)

    n = int(existing.get("times_seen", 0))
    prev_avg = float(existing.get("avg_score_gain", 0.0))
    new_n = n + 1
    existing["times_seen"] = new_n
    existing["avg_score_gain"] = round(((prev_avg * n) + gain) / new_n, 3)

    if improved:
        existing["times_succeeded"] = int(existing.get("times_succeeded", 0)) + 1
    else:
        existing["times_failed"] = int(existing.get("times_failed", 0)) + 1

    seen = max(int(existing.get("times_seen", 1)), 1)
    existing["success_rate"] = round(int(existing.get("times_succeeded", 0)) / seen, 3)
    existing["updated_at"] = now

    data["patterns"] = patterns
    save_memory(data, path)
    return existing


def memory_stats(path: str = MEMORY_FILE) -> Dict[str, Any]:
    data = load_memory(path)
    patterns = data.get("patterns", [])
    learned = [p for p in patterns if not p.get("seed")]
    return {
        "total_patterns": len(patterns),
        "seed_patterns": len(patterns) - len(learned),
        "learned_patterns": len(learned),
        "top_successful": sorted(
            learned,
            key=lambda p: (p.get("success_rate", 0), p.get("times_seen", 0)),
            reverse=True,
        )[:5],
    }