"""
PDF Parser Module
Extracts clean text from resume PDFs using pdfplumber.
"""

import pdfplumber
from typing import Optional


def extract_text_from_pdf(pdf_file) -> Optional[str]:
    """
    Extract all text from an uploaded PDF file.
    
    Args:
        pdf_file: Streamlit UploadedFile or file-like object
        
    Returns:
        Extracted text as a single string, or None if extraction fails.
    """
    try:
        text_parts = []
        
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        full_text = "\n\n".join(text_parts).strip()
        
        if not full_text:
            return None
            
        return full_text
        
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None


def get_pdf_info(pdf_file) -> dict:
    """
    Get basic metadata about the PDF (page count, etc.).
    """
    try:
        with pdfplumber.open(pdf_file) as pdf:
            return {
                "page_count": len(pdf.pages),
                "metadata": pdf.metadata or {}
            }
    except Exception:
        return {"page_count": 0, "metadata": {}}