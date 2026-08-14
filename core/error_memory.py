"""
Error Memory (Phase 2)

- JSON file remains the source of truth for patterns/outcomes
- Chroma is used for semantic retrieval when available
- Falls back to lexical JSON retrieval if Chroma is unavailable

Privacy: stores only anonymized error patterns, never resume text.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.error_taxonomy import ALL_ERRORS, get_error_info

MEMORY_FILE = "error_memory.json"
CHROMA_DIR = "error_memory_chroma"
CHROMA_COLLECTION = "resume_error_patterns"

# ---------------------------------------------------------------------------
# JSON persistence
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Lexical fallback retrieval
# ---------------------------------------------------------------------------

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
    return len(q & p) / max(len(q), 1)


def _lexical_retrieve(
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


# ---------------------------------------------------------------------------
# Chroma helpers
# ---------------------------------------------------------------------------

def _pattern_document(pat: Dict[str, Any]) -> str:
    return (
        f"Error code: {pat.get('error_code', '')}. "
        f"Description: {pat.get('description', '')}. "
        f"Fix strategy: {pat.get('fix_strategy', '')}. "
        f"Job family: {pat.get('job_family', 'general')}."
    )


def _get_chroma_collection():
    """Return Chroma collection or None if unavailable."""
    try:
        import chromadb
        from chromadb.config import Settings

        client = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        return client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
    except Exception as e:
        print(f"Chroma unavailable, using JSON retrieval: {e}")
        return None


def sync_patterns_to_chroma(path: str = MEMORY_FILE) -> int:
    """
    Upsert all JSON patterns into Chroma.
    Returns number of patterns synced, or 0 on failure.
    """
    collection = _get_chroma_collection()
    if collection is None:
        return 0

    data = load_memory(path)
    patterns = data.get("patterns", [])
    if not patterns:
        return 0

    ids, documents, metadatas = [], [], []
    for pat in patterns:
        pid = str(pat.get("id") or f"pat_{pat.get('error_code')}")
        ids.append(pid)
        documents.append(_pattern_document(pat))
        metadatas.append({
            "error_code": str(pat.get("error_code", "")),
            "source": str(pat.get("source", "")),
            "job_family": str(pat.get("job_family", "general")),
            "success_rate": float(pat.get("success_rate", 0.0) or 0.0),
            "times_seen": int(pat.get("times_seen", 0) or 0),
            "seed": bool(pat.get("seed", False)),
        })

    # upsert in batches
    batch = 50
    for i in range(0, len(ids), batch):
        collection.upsert(
            ids=ids[i:i + batch],
            documents=documents[i:i + batch],
            metadatas=metadatas[i:i + batch],
        )
    return len(ids)


def _chroma_retrieve(
    error_code: str,
    description: str = "",
    job_family: str = "general",
    top_k: int = 3,
) -> Optional[List[Dict[str, Any]]]:
    collection = _get_chroma_collection()
    if collection is None:
        return None

    query = (
        f"Error code: {error_code}. "
        f"Description: {description}. "
        f"Job family: {job_family}."
    )

    try:
        result = collection.query(
            query_texts=[query],
            n_results=max(top_k * 3, top_k),
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        print(f"Chroma query failed: {e}")
        return None

    data = load_memory()
    by_id = {str(p.get("id")): p for p in data.get("patterns", [])}

    ids = (result.get("ids") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    dists = (result.get("distances") or [[]])[0]

    ranked = []
    for i, pid in enumerate(ids):
        pat = by_id.get(str(pid))
        if not pat:
            # reconstruct minimal pattern from metadata if needed
            meta = metas[i] if i < len(metas) else {}
            pat = {
                "id": pid,
                "error_code": meta.get("error_code", error_code),
                "description": description,
                "fix_strategy": get_error_info(meta.get("error_code", error_code)).get("default_fix", ""),
                "job_family": meta.get("job_family", job_family),
                "success_rate": meta.get("success_rate", 0.0),
                "times_seen": meta.get("times_seen", 0),
            }
        # prefer same error code slightly
        bonus = 0.0
        if pat.get("error_code") == error_code:
            bonus += 0.15
        if pat.get("job_family") == job_family:
            bonus += 0.05
        distance = float(dists[i]) if i < len(dists) else 1.0
        # cosine distance: lower is better → convert to score
        score = (1.0 - distance) + bonus + float(pat.get("success_rate", 0.0) or 0.0)
        ranked.append((score, pat))

    ranked.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in ranked[:top_k]]


# ---------------------------------------------------------------------------
# Public API (compatible with existing pipeline)
# ---------------------------------------------------------------------------

def retrieve_similar_patterns(
    error_code: str,
    description: str = "",
    job_family: str = "general",
    top_k: int = 3,
    path: str = MEMORY_FILE,
) -> List[Dict[str, Any]]:
    """
    Semantic retrieval via Chroma when available; JSON lexical fallback otherwise.
    """
    # Ensure chroma has latest JSON patterns
    try:
        sync_patterns_to_chroma(path)
    except Exception as e:
        print(f"Chroma sync skipped: {e}")

    chroma_hits = _chroma_retrieve(error_code, description, job_family, top_k)
    if chroma_hits:
        return chroma_hits
    return _lexical_retrieve(error_code, description, job_family, top_k, path)


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
    """
    Update JSON memory with anonymized outcome, then sync to Chroma.
    """
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

    # keep vector index updated
    try:
        sync_patterns_to_chroma(path)
    except Exception as e:
        print(f"Chroma sync after log failed: {e}")

    return existing


def memory_stats(path: str = MEMORY_FILE) -> Dict[str, Any]:
    data = load_memory(path)
    patterns = data.get("patterns", [])
    learned = [p for p in patterns if not p.get("seed")]
    chroma_ok = _get_chroma_collection() is not None
    return {
        "total_patterns": len(patterns),
        "seed_patterns": len(patterns) - len(learned),
        "learned_patterns": len(learned),
        "chroma_enabled": chroma_ok,
        "top_successful": sorted(
            learned,
            key=lambda p: (p.get("success_rate", 0), p.get("times_seen", 0)),
            reverse=True,
        )[:5],
    }