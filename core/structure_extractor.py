"""
Structure Extractor Module
Takes raw resume text and organizes it into clear sections.
"""

import re
from typing import Dict, List, Optional


# Common section headers found in resumes (case-insensitive)
SECTION_HEADERS = {
    "summary": [
        r"professional summary", r"summary", r"profile", r"about me",
        r"objective", r"career objective", r"professional profile"
    ],
    "experience": [
        r"work experience", r"professional experience", r"experience",
        r"employment history", r"work history", r"career history"
    ],
    "education": [
        r"education", r"academic background", r"academic history",
        r"educational background"
    ],
    "skills": [
        r"skills", r"technical skills", r"core competencies",
        r"key skills", r"areas of expertise", r"technologies"
    ],
    "projects": [
        r"projects", r"personal projects", r"key projects",
        r"selected projects", r"academic projects"
    ],
    "certifications": [
        r"certifications", r"certificates", r"licenses",
        r"professional certifications", r"courses"
    ],
    "achievements": [
        r"achievements", r"awards", r"honors", r"accomplishments"
    ],
    "languages": [
        r"languages", r"language proficiency"
    ],
    "interests": [
        r"interests", r"hobbies"
    ]
}


def _normalize_header(text: str) -> str:
    """Clean and normalize a potential header line."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\s]", "", text)  # remove punctuation
    text = re.sub(r"\s+", " ", text)
    return text


def _is_section_header(line: str) -> Optional[str]:
    """
    Check if a line is a known section header.
    Returns the section key (e.g. 'experience') or None.
    """
    normalized = _normalize_header(line)
    
    # Skip very long lines (unlikely to be headers)
    if len(normalized.split()) > 6:
        return None
    
    for section_key, patterns in SECTION_HEADERS.items():
        for pattern in patterns:
            if re.fullmatch(pattern, normalized) or normalized == pattern:
                return section_key
            # Also allow partial match for slightly varied headers
            if pattern in normalized and len(normalized) < 40:
                return section_key
    return None


def extract_contact_info(text: str) -> Dict[str, str]:
    """
    Attempt to extract basic contact information from the top of the resume.
    """
    contact = {
        "name": "",
        "email": "",
        "phone": "",
        "linkedin": "",
        "location": "",
        "raw_header": ""
    }
    
    lines = text.strip().split("\n")
    header_lines = lines[:12]  # Usually contact info is near the top
    header_text = "\n".join(header_lines)
    contact["raw_header"] = header_text
    
    # Email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", header_text)
    if email_match:
        contact["email"] = email_match.group(0)
    
    # Phone (various formats)
    phone_match = re.search(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}(?:[-.\s]?\d{1,4})?",
        header_text
    )
    if phone_match:
        contact["phone"] = phone_match.group(0).strip()
    
    # LinkedIn
    linkedin_match = re.search(
        r"(?:linkedin\.com/in/|linkedin\.com/pub/)[\w\-_/]+",
        header_text,
        re.IGNORECASE
    )
    if linkedin_match:
        contact["linkedin"] = linkedin_match.group(0)
    
    # Very basic name guess (first non-empty line that isn't email/phone)
    for line in header_lines:
        clean = line.strip()
        if not clean:
            continue
        if "@" in clean or re.search(r"\d{3}", clean):
            continue
        if len(clean.split()) <= 5 and len(clean) < 50:
            contact["name"] = clean
            break
    
    return contact


def extract_structure(raw_text: str) -> Dict:
    """
    Main function: Convert raw resume text into a structured dictionary.
    
    Returns:
        {
            "contact": {...},
            "sections": {
                "summary": "...",
                "experience": "...",
                "education": "...",
                ...
            },
            "raw_text": "original text"
        }
    """
    if not raw_text or not raw_text.strip():
        return {
            "contact": {},
            "sections": {},
            "raw_text": ""
        }
    
    # Extract contact info
    contact = extract_contact_info(raw_text)
    
    # Split into lines and find section boundaries
    lines = raw_text.split("\n")
    sections: Dict[str, List[str]] = {}
    current_section = "other"
    sections[current_section] = []
    
    for line in lines:
        section_key = _is_section_header(line)
        
        if section_key:
            current_section = section_key
            if current_section not in sections:
                sections[current_section] = []
            # Do not include the header line itself in the content
            continue
        
        sections[current_section].append(line)
    
    # Clean up each section (join lines and strip)
    cleaned_sections = {}
    for key, content_lines in sections.items():
        content = "\n".join(content_lines).strip()
        # Remove excessive blank lines
        content = re.sub(r"\n{3,}", "\n\n", content)
        if content:
            cleaned_sections[key] = content
    
    # Prefer "summary" over leftover "other" at the top if it looks like a summary
    if "summary" not in cleaned_sections and "other" in cleaned_sections:
        # Simple heuristic: if "other" is relatively short, treat it as summary
        if len(cleaned_sections["other"]) < 600:
            cleaned_sections["summary"] = cleaned_sections.pop("other")
    
    return {
        "contact": contact,
        "sections": cleaned_sections,
        "raw_text": raw_text
    }


def print_structure_summary(structured: Dict) -> None:
    """Helper to pretty-print the extracted structure (useful for debugging)."""
    print("=" * 50)
    print("EXTRACTED STRUCTURE")
    print("=" * 50)
    
    contact = structured.get("contact", {})
    print("\n[Contact]")
    for k, v in contact.items():
        if v and k != "raw_header":
            print(f"  {k}: {v}")
    
    print("\n[Sections found]")
    for section, content in structured.get("sections", {}).items():
        preview = content[:120].replace("\n", " ")
        print(f"  • {section.upper()}: {preview}...")
    
    print("=" * 50)