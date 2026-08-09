"""
Security utilities for Resume ATS Optimizer
"""

import os
import re
from typing import Tuple, Optional
from io import BytesIO

# Maximum allowed upload size (5 MB)
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Allowed MIME / extensions
ALLOWED_EXTENSIONS = {".pdf"}


def validate_uploaded_file(uploaded_file) -> Tuple[bool, str]:
    """
    Validate file type and size.
    Returns (is_valid, error_message)
    """
    if uploaded_file is None:
        return False, "No file uploaded."

    # Check extension
    filename = uploaded_file.name.lower()
    if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        return False, "Only PDF files are allowed."

    # Check size
    file_size = uploaded_file.size if hasattr(uploaded_file, "size") else len(uploaded_file.getvalue())
    if file_size > MAX_FILE_SIZE_BYTES:
        return False, f"File is too large. Maximum allowed size is {MAX_FILE_SIZE_MB} MB."

    if file_size == 0:
        return False, "Uploaded file is empty."

    return True, ""


def sanitize_text_for_logging(text: str, max_length: int = 0) -> str:
    """
    We do not store resume content.
    This function exists only as a safeguard.
    """
    return ""


def basic_output_validation(optimized_text: str) -> Tuple[bool, str]:
    """
    Very basic checks on LLM output.
    """
    if not optimized_text or len(optimized_text.strip()) < 100:
        return False, "Optimized resume is too short or empty."

    # Check for obvious refusal / error patterns
    lower = optimized_text.lower()
    bad_patterns = [
        "i cannot", "i can't assist", "as an ai", "i'm unable",
        "sorry, but i cannot", "i do not have access"
    ]
    for pattern in bad_patterns:
        if pattern in lower:
            return False, "LLM returned an unusable response."

    return True, ""


def clear_sensitive_session_keys(session_state):
    """
    Remove sensitive data from Streamlit session state.
    """
    keys_to_clear = [
        "resume_text",
        "structured_resume",
        "final_resume",
        "optimized_resume",
        "original_text",
        "job_description"
    ]
    for key in keys_to_clear:
        if key in session_state:
            del session_state[key]


def get_api_key_safely() -> Optional[str]:
    """
    Prefer Streamlit secrets in deployment, fall back to .env for local.
    """
    # Try Streamlit secrets first (for Cloud deployment)
    try:
        import streamlit as st
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass

    # Fall back to environment variable
    return os.getenv("OPENAI_API_KEY")