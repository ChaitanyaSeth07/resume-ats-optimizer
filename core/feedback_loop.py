"""
Feedback Loop Module
Implements the practical generate → score → improve cycle.
"""

from typing import Dict, Tuple, Optional
from core.llm_optimizer import optimize_resume, build_optimization_prompt
from core.scoring_engine import calculate_overall_score
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
)


def build_improvement_prompt(
    previous_resume: str,
    job_description: str,
    score_report: Dict
) -> str:
    """
    Build a prompt that tells the AI exactly what is weak and how to improve.
    """
    missing = ", ".join(score_report.get("missing_keywords", [])[:8])
    rating = score_report.get("rating", "Needs Improvement")
    overall = score_report.get("overall_score", 0)

    prompt = f"""
You previously optimized a resume. The current version scored {overall}/100 ({rating}).

Job Description:
\"\"\"
{job_description}
\"\"\"

Current Optimized Resume:
\"\"\"
{previous_resume}
\"\"\"

Main weaknesses:
- Missing important keywords: {missing if missing else "None major"}
- Overall score is still below target.

Your task:
Improve this resume further so it becomes more ATS-friendly and better matched to the job description.
Focus especially on naturally including the missing keywords and strengthening the language.
Do NOT invent new jobs, degrees, or fake metrics.
Keep the same structure and truthful information.

Return the complete improved resume in the same structured format as before.
"""
    return prompt.strip()


def improve_resume_with_feedback(
    previous_resume: str,
    job_description: str,
    score_report: Dict,
    model: str = "llama-3.3-70b-versatile"
) -> Optional[str]:
    """
    Ask the LLM to improve the resume based on the score feedback.
    """
    try:
        prompt = build_improvement_prompt(previous_resume, job_description, score_report)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume writer specializing in ATS optimization. Improve the resume based on the feedback."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4,
            max_tokens=2500
        )

        improved = response.choices[0].message.content
        return improved.strip() if improved else None

    except Exception as e:
        print(f"Error in feedback improvement: {e}")
        return None


def run_feedback_loop(
    structured_resume: Dict,
    job_description: str,
    max_attempts: int = 3,
    target_score: float = 75.0
) -> Tuple[str, Dict, int]:
    """
    Full feedback loop:
    1. Optimize
    2. Score
    3. If score < target → improve and repeat
    
    Returns:
        final_resume, final_score_report, attempts_used
    """
    # First generation
    current_resume = optimize_resume(structured_resume, job_description)
    if current_resume is None:
        return None, {}, 0

    score_report = calculate_overall_score(current_resume, job_description)
    attempts = 1

    while score_report["overall_score"] < target_score and attempts < max_attempts:
        improved = improve_resume_with_feedback(
            current_resume,
            job_description,
            score_report
        )

        if improved is None:
            break

        current_resume = improved
        score_report = calculate_overall_score(current_resume, job_description)
        attempts += 1

    return current_resume, score_report, attempts