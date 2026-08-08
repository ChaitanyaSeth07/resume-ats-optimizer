"""
DOCX Builder Module
Creates a clean, modern, ATS-friendly Word document from the optimized resume text.
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import re
from typing import Optional
from io import BytesIO


def set_paragraph_spacing(paragraph, before=0, after=6, line_spacing=1.15):
    """Helper to set consistent spacing."""
    pf = paragraph.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line_spacing


def add_horizontal_line(doc):
    """Add a simple horizontal line."""
    paragraph = doc.add_paragraph()
    p = paragraph._p
    pPr = p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '000000')
    pBdr.append(bottom)
    pPr.append(pBdr)
    set_paragraph_spacing(paragraph, before=2, after=8)


def parse_optimized_resume(text: str) -> dict:
    """
    Simple parser that splits the LLM output into sections.
    """
    sections = {
        "contact": "",
        "summary": "",
        "experience": "",
        "education": "",
        "skills": "",
        "projects": "",
        "certifications": "",
        "other": ""
    }

    current = "other"
    lines = text.split("\n")

    for line in lines:
        upper = line.strip().upper()
        if upper.startswith("CONTACT"):
            current = "contact"
            continue
        elif upper.startswith("SUMMARY"):
            current = "summary"
            continue
        elif upper.startswith("EXPERIENCE"):
            current = "experience"
            continue
        elif upper.startswith("EDUCATION"):
            current = "education"
            continue
        elif upper.startswith("SKILLS"):
            current = "skills"
            continue
        elif upper.startswith("PROJECTS"):
            current = "projects"
            continue
        elif upper.startswith("CERTIFICATIONS"):
            current = "certifications"
            continue
        elif upper.startswith("OTHER"):
            current = "other"
            continue

        if line.strip():
            sections[current] += line + "\n"

    return sections


def create_ats_docx(optimized_text: str) -> BytesIO:
    """
    Create a clean ATS-friendly DOCX from the optimized resume text.
    Returns a BytesIO object ready for download.
    """
    doc = Document()

    # Set narrow margins (ATS friendly)
    for section in doc.sections:
        section.top_margin = Inches(0.6)
        section.bottom_margin = Inches(0.6)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)

    # Default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)

    parsed = parse_optimized_resume(optimized_text)

    # === CONTACT / HEADER ===
    contact_lines = [l.strip() for l in parsed["contact"].strip().split("\n") if l.strip()]
    
    if contact_lines:
        # Name (first line usually)
        name = contact_lines[0].replace("Name:", "").strip()
        name_para = doc.add_paragraph()
        name_run = name_para.add_run(name)
        name_run.bold = True
        name_run.font.size = Pt(18)
        name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_paragraph_spacing(name_para, before=0, after=4)

        # Rest of contact info
        contact_info = []
        for line in contact_lines[1:]:
            clean = re.sub(r"^(Email|Phone|LinkedIn|Location):\s*", "", line, flags=re.IGNORECASE)
            if clean:
                contact_info.append(clean)

        if contact_info:
            info_para = doc.add_paragraph()
            info_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            info_run = info_para.add_run(" | ".join(contact_info))
            info_run.font.size = Pt(10)
            set_paragraph_spacing(info_para, before=0, after=6)

    add_horizontal_line(doc)

    # Helper to add a section
    def add_section(title: str, content: str):
        if not content.strip():
            return

        # Section heading
        heading = doc.add_paragraph()
        run = heading.add_run(title.upper())
        run.bold = True
        run.font.size = Pt(12)
        set_paragraph_spacing(heading, before=10, after=4)

        # Content
        for line in content.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            para = doc.add_paragraph()
            # Detect bullet points
            if line.startswith(("-", "•", "*", "–")):
                line = line.lstrip("-•*– ").strip()
                run = para.add_run("• " + line)
            else:
                run = para.add_run(line)

            run.font.size = Pt(11)
            set_paragraph_spacing(para, before=0, after=3)

    # Add sections in order
    add_section("Professional Summary", parsed["summary"])
    add_section("Experience", parsed["experience"])
    add_section("Education", parsed["education"])
    add_section("Skills", parsed["skills"])
    add_section("Projects", parsed["projects"])
    add_section("Certifications", parsed["certifications"])

    if parsed["other"].strip():
        add_section("Additional Information", parsed["other"])

    # Save to memory
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer