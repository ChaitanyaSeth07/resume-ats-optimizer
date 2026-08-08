"""
DOCX Builder Module (Improved)
Creates a clean, modern, professional, and highly ATS-friendly Word document.
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import re
from io import BytesIO


def set_run_font(run, name="Calibri", size=11, bold=False, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def set_paragraph_format(paragraph, before=0, after=6, line_spacing=1.15, alignment=None):
    pf = paragraph.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line_spacing
    if alignment:
        paragraph.alignment = alignment


def add_horizontal_line(doc):
    """Subtle horizontal line under the header."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(10)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "222222")
    pBdr.append(bottom)
    pPr.append(pBdr)


def parse_optimized_resume(text: str) -> dict:
    """Parse the structured text coming from the LLM."""
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
    for line in text.split("\n"):
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


def add_section_heading(doc, title: str):
    """Consistent section headings that ATS can easily detect."""
    p = doc.add_paragraph()
    run = p.add_run(title.upper())
    set_run_font(run, size=12, bold=True, color=(30, 30, 30))
    set_paragraph_format(p, before=12, after=4)
    
    # Small underline effect via bottom border
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "555555")
    pBdr.append(bottom)
    pPr.append(pBdr)


def add_body_content(doc, content: str):
    """Add body text with proper bullet handling and spacing."""
    if not content.strip():
        return

    for raw_line in content.strip().split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        p = doc.add_paragraph()

        # Bullet detection
        if line.startswith(("-", "•", "*", "–", "—")):
            clean = re.sub(r"^[-•*–—]\s*", "", line)
            run = p.add_run("• " + clean)
        else:
            run = p.add_run(line)

        set_run_font(run, size=10.5)
        set_paragraph_format(p, before=1, after=3, line_spacing=1.12)


def create_ats_docx(optimized_text: str) -> BytesIO:
    """
    Create a polished, modern, ATS-safe DOCX.
    """
    doc = Document()

    # Page setup - clean margins
    for section in doc.sections:
        section.top_margin = Inches(0.55)
        section.bottom_margin = Inches(0.55)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)

    # Base style
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)

    parsed = parse_optimized_resume(optimized_text)

    # ========== HEADER / CONTACT ==========
    contact_lines = [l.strip() for l in parsed["contact"].strip().split("\n") if l.strip()]

    name = ""
    contact_parts = []

    for i, line in enumerate(contact_lines):
        cleaned = re.sub(r"^(Name|Email|Phone|LinkedIn|Location):\s*", "", line, flags=re.IGNORECASE).strip()
        if i == 0 or line.lower().startswith("name"):
            name = cleaned
        else:
            if cleaned:
                contact_parts.append(cleaned)

    # Name
    if name:
        name_p = doc.add_paragraph()
        name_run = name_p.add_run(name)
        set_run_font(name_run, size=20, bold=True, color=(20, 20, 20))
        set_paragraph_format(name_p, before=0, after=2, alignment=WD_ALIGN_PARAGRAPH.CENTER)

    # Contact line
    if contact_parts:
        info_p = doc.add_paragraph()
        info_run = info_p.add_run("  |  ".join(contact_parts))
        set_run_font(info_run, size=9.5, color=(60, 60, 60))
        set_paragraph_format(info_p, before=0, after=4, alignment=WD_ALIGN_PARAGRAPH.CENTER)

    add_horizontal_line(doc)

    # ========== SECTIONS ==========
    section_order = [
        ("Professional Summary", parsed["summary"]),
        ("Experience", parsed["experience"]),
        ("Education", parsed["education"]),
        ("Skills", parsed["skills"]),
        ("Projects", parsed["projects"]),
        ("Certifications", parsed["certifications"]),
    ]

    for title, content in section_order:
        if content.strip():
            add_section_heading(doc, title)
            add_body_content(doc, content)

    if parsed["other"].strip():
        add_section_heading(doc, "Additional Information")
        add_body_content(doc, parsed["other"])

    # Save to memory
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer