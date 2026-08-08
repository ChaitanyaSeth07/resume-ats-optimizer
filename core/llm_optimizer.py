"""
LLM Optimizer Module
Uses Groq (free tier) via OpenAI-compatible API to improve the resume.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Optional

# Load environment variables from .env file
load_dotenv()

# Initialize the client for Groq
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
)


def build_optimization_prompt(structured_resume: Dict, job_description: str) -> str:
    """
    Create a strong prompt for the LLM to optimize the resume.
    """
    contact = structured_resume.get("contact", {})
    sections = structured_resume.get("sections", {})

    # Build a readable version of the current resume
    resume_content = ""
    if contact.get("name"):
        resume_content += f"Name: {contact.get('name')}\n"
    if contact.get("email"):
        resume_content += f"Email: {contact.get('email')}\n"
    if contact.get("phone"):
        resume_content += f"Phone: {contact.get('phone')}\n"
    if contact.get("linkedin"):
        resume_content += f"LinkedIn: {contact.get('linkedin')}\n"
    resume_content += "\n"

    for section_name, content in sections.items():
        resume_content += f"=== {section_name.upper()} ===\n{content}\n\n"

    prompt = f"""
You are an expert resume writer and ATS (Applicant Tracking System) specialist.

Your task is to improve the following resume so that it:
1. Is highly ATS-friendly (clean structure, standard headings, strong keywords)
2. Is tailored to the job description provided
3. Uses strong action verbs and quantifiable achievements where possible
4. Keeps all original facts truthful (do NOT invent experience or numbers)
5. Improves clarity, impact, and professional language
6. Maintains a modern, clean, professional tone

JOB DESCRIPTION:
\"\"\"
{job_description}
\"\"\"

CURRENT RESUME:
\"\"\"
{resume_content}
\"\"\"

Please return the improved resume in the following structured format exactly:

CONTACT:
Name: ...
Email: ...
Phone: ...
LinkedIn: ...
Location: ...

SUMMARY:
(improved professional summary)

EXPERIENCE:
(improved work experience with strong bullets)

EDUCATION:
(education section)

SKILLS:
(optimized skills list, preferably matching keywords from the job description)

PROJECTS:
(if applicable)

CERTIFICATIONS:
(if applicable)

OTHER:
(any other relevant sections)

Important rules:
- Do not add fake experience or fake metrics.
- Keep the same jobs and education.
- Make bullet points start with strong action verbs.
- Prioritize keywords from the job description naturally.
- Keep it concise and professional.
"""
    return prompt.strip()


def optimize_resume(structured_resume: Dict, job_description: str, model: str = "llama-3.3-70b-versatile") -> Optional[str]:
    """
    Call the LLM (Groq) to optimize the resume.
    
    Args:
        structured_resume: Output from structure_extractor
        job_description: The target job description
        model: Model name on Groq (llama-3.3-70b-versatile is recommended)
        
    Returns:
        Improved resume as plain text, or None if failed.
    """
    try:
        prompt = build_optimization_prompt(structured_resume, job_description)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume writer specializing in ATS optimization."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4,
            max_tokens=2500
        )

        improved_resume = response.choices[0].message.content
        return improved_resume.strip() if improved_resume else None

    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None