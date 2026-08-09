"""
LLM Optimizer Module (Security-hardened)
Uses Groq via OpenAI-compatible API.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Optional

load_dotenv()

def get_client():
    """Create OpenAI-compatible client with safe key loading."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Prefer Streamlit secrets when available
    try:
        import streamlit as st
        if "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass

    if not api_key:
        raise ValueError("API key not found. Please set OPENAI_API_KEY.")

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
    try:
        import streamlit as st
        if "OPENAI_BASE_URL" in st.secrets:
            base_url = st.secrets["OPENAI_BASE_URL"]
    except Exception:
        pass

    return OpenAI(api_key=api_key, base_url=base_url)


def build_optimization_prompt(structured_resume: Dict, job_description: str) -> str:
    contact = structured_resume.get("contact", {})
    sections = structured_resume.get("sections", {})

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
You are an expert resume writer and ATS specialist.

Improve the resume so that it is:
1. Highly ATS-friendly
2. Tailored to the job description
3. Uses strong action verbs
4. Keeps all original facts truthful (DO NOT invent experience, jobs, degrees, or metrics)
5. Clear and professional

JOB DESCRIPTION:
\"\"\"
{job_description}
\"\"\"

CURRENT RESUME:
\"\"\"
{resume_content}
\"\"\"

Return the improved resume in this exact structure:

CONTACT:
Name: ...
Email: ...
Phone: ...
LinkedIn: ...
Location: ...

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

Critical rules:
- Never invent new jobs, companies, degrees, or numbers.
- Keep the same real experiences.
- Only improve language, structure, and keyword alignment.
"""
    return prompt.strip()


def optimize_resume(structured_resume: Dict, job_description: str, model: str = "llama-3.3-70b-versatile") -> Optional[str]:
    try:
        client = get_client()
        prompt = build_optimization_prompt(structured_resume, job_description)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume writer. Never invent experience or metrics. Only improve wording and structure."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=2500
        )

        result = response.choices[0].message.content
        return result.strip() if result else None

    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None