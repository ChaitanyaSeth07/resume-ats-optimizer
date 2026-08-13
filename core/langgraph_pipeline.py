"""
Graph-style optimization pipeline (LangGraph-ready architecture).

Phase 1: explicit state machine in Python (no hard dependency on langgraph package).
Uses:
- existing optimize_resume / scoring
- error diagnosis
- JSON error memory
- targeted single-error fixes per iteration
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

from openai import OpenAI
from dotenv import load_dotenv

from core.graph_state import ResumeGraphState, initial_state
from core.llm_optimizer import optimize_resume
from core.scoring_engine import calculate_overall_score
from core.error_diagnosis import diagnose_errors, select_next_error
from core.error_memory import retrieve_similar_patterns, log_fix_outcome

load_dotenv()


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")

    try:
        import streamlit as st
        if "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
        if "OPENAI_BASE_URL" in st.secrets:
            base_url = st.secrets["OPENAI_BASE_URL"]
    except Exception:
        pass

    if not api_key:
        raise ValueError("API key not found. Please set OPENAI_API_KEY.")

    return OpenAI(api_key=api_key, base_url=base_url)


def _targeted_fix(
    current_resume: str,
    job_description: str,
    selected_error: Dict[str, Any],
    retrieved_patterns: list,
    model: str = "llama-3.3-70b-versatile",
) -> Optional[str]:
    """Ask the LLM to fix ONE selected error only."""
    pattern_text = ""
    if retrieved_patterns:
        lines = []
        for i, p in enumerate(retrieved_patterns[:3], 1):
            lines.append(
                f"{i}. Strategy: {p.get('fix_strategy', '')} "
                f"(success_rate={p.get('success_rate', 0)})"
            )
        pattern_text = "\n".join(lines)

    prompt = f"""
You are an expert ATS resume editor.

Fix ONLY this specific issue in the resume:
Error code: {selected_error.get('code')}
Issue: {selected_error.get('description')}
Section focus: {selected_error.get('section')}
Recommended strategy: {selected_error.get('fix_strategy')}

Helpful past strategies:
{pattern_text if pattern_text else "None"}

JOB DESCRIPTION:
\"\"\"
{job_description}
\"\"\"

CURRENT RESUME:
\"\"\"
{current_resume}
\"\"\"

Rules:
1. Fix the stated issue only as much as needed.
2. Do NOT invent jobs, degrees, employers, or metrics.
3. Keep truthful content from the current resume.
4. Maintain a clean ATS-friendly structure with standard section headings.
5. Return the full updated resume in this structure:

CONTACT:
...
SUMMARY:
...
EXPERIENCE:
...
EDUCATION:
...
SKILLS:
...
PROJECTS:
...
CERTIFICATIONS:
...
OTHER:
...
"""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You fix one resume issue at a time. Never invent experience or numbers.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2500,
        )
        content = response.choices[0].message.content
        return content.strip() if content else None
    except Exception as e:
        print(f"Targeted fix failed: {e}")
        return None


def _should_stop(state: ResumeGraphState) -> Tuple[bool, str]:
    score = float((state.get("score_report") or {}).get("overall_score") or 0)
    target = float(state.get("target_score") or 75)
    attempt = int(state.get("attempt") or 0)
    max_attempts = int(state.get("max_attempts") or 3)
    active = state.get("active_errors") or []

    if score >= target:
        return True, "target_reached"
    if attempt >= max_attempts:
        return True, "max_attempts"
    if not active:
        return True, "no_active_errors"

    # stop if last two fixes failed
    history = state.get("fix_history") or []
    if len(history) >= 2:
        if not history[-1].get("improved") and not history[-2].get("improved"):
            return True, "no_improvement_streak"

    return False, ""


def run_graph_optimization(
    structured_resume: Dict[str, Any],
    job_description: str,
    original_text: str = "",
    target_score: float = 75.0,
    max_attempts: int = 3,
    design_options: Optional[Dict[str, Any]] = None,
    job_family: str = "general",
) -> Tuple[Optional[str], Dict[str, Any], int, ResumeGraphState]:
    """
    Run the full graph-style optimization loop.

    Returns:
        final_resume, final_score_report, attempts_used, final_state
    """
    state: ResumeGraphState = initial_state(
        original_text=original_text or "",
        job_description=job_description,
        structured_resume=structured_resume,
        target_score=target_score,
        max_attempts=max_attempts,
        design_options=design_options or {},
    )

    # ---- Node: initial_optimize ----
    first = optimize_resume(structured_resume, job_description)
    if not first:
        state["stop_reason"] = "initial_optimize_failed"
        return None, {}, 0, state

    state["current_resume"] = first
    state["attempt"] = 1

    # ---- Node: score_resume ----
    score_report = calculate_overall_score(first, job_description)
    state["score_report"] = score_report
    state["previous_score"] = None

    # ---- Node: diagnose_errors ----
    active = diagnose_errors(
        resume_text=first,
        score_report=score_report,
        previous_score=None,
        previous_error_code=None,
        fix_history=[],
    )
    state["active_errors"] = active

    stop, reason = _should_stop(state)
    if stop:
        state["final_resume"] = state["current_resume"]
        state["stop_reason"] = reason or "complete"
        return state["final_resume"], state["score_report"], state["attempt"], state

    # ---- Repair loop ----
    while True:
        stop, reason = _should_stop(state)
        if stop:
            state["final_resume"] = state["current_resume"]
            state["stop_reason"] = reason
            break

        if state["attempt"] >= state["max_attempts"]:
            state["final_resume"] = state["current_resume"]
            state["stop_reason"] = "max_attempts"
            break

        # select one error
        selected = select_next_error(state.get("active_errors") or [], state.get("fix_history") or [])
        if not selected:
            state["final_resume"] = state["current_resume"]
            state["stop_reason"] = "no_selected_error"
            break

        state["selected_error"] = selected

        # retrieve patterns from memory
        patterns = retrieve_similar_patterns(
            error_code=selected.get("code", ""),
            description=selected.get("description", ""),
            job_family=job_family,
            top_k=3,
        )
        state["retrieved_patterns"] = patterns

        score_before = float((state.get("score_report") or {}).get("overall_score") or 0)
        previous_resume = state.get("current_resume")

        # targeted fix
        fixed = _targeted_fix(
            current_resume=state["current_resume"],
            job_description=job_description,
            selected_error=selected,
            retrieved_patterns=patterns,
        )

        if not fixed:
            # count failed attempt and stop if needed
            state["attempt"] = int(state["attempt"]) + 1
            state["fix_history"] = list(state.get("fix_history") or []) + [{
                "attempt": state["attempt"],
                "error_code": selected.get("code"),
                "fix_strategy": selected.get("fix_strategy"),
                "score_before": score_before,
                "score_after": score_before,
                "improved": False,
            }]
            continue

        # score again
        new_score_report = calculate_overall_score(fixed, job_description)
        score_after = float(new_score_report.get("overall_score") or 0)
        improved = score_after > score_before

        state["previous_resume"] = previous_resume
        state["previous_score"] = score_before
        state["current_resume"] = fixed
        state["score_report"] = new_score_report
        state["attempt"] = int(state["attempt"]) + 1

        history_item = {
            "attempt": state["attempt"],
            "error_code": selected.get("code"),
            "fix_strategy": selected.get("fix_strategy"),
            "score_before": score_before,
            "score_after": score_after,
            "improved": improved,
        }
        state["fix_history"] = list(state.get("fix_history") or []) + [history_item]

        # log anonymized outcome to memory
        log_fix_outcome(
            error_code=selected.get("code", "UNKNOWN"),
            description=selected.get("description", ""),
            fix_strategy=selected.get("fix_strategy", ""),
            score_before=score_before,
            score_after=score_after,
            job_family=job_family,
            source=selected.get("source", "user"),
        )

        # re-diagnose
        active = diagnose_errors(
            resume_text=fixed,
            score_report=new_score_report,
            previous_score=score_before,
            previous_error_code=selected.get("code"),
            fix_history=state.get("fix_history") or [],
        )
        state["active_errors"] = active

    if not state.get("final_resume"):
        state["final_resume"] = state.get("current_resume")

    return (
        state.get("final_resume"),
        state.get("score_report") or {},
        int(state.get("attempt") or 0),
        state,
    )