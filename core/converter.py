"""
Converter Module
Converts DOCX → PDF when possible.
"""

from io import BytesIO
import tempfile
import os
from typing import Optional

def convert_docx_to_pdf(docx_buffer: BytesIO) -> Optional[BytesIO]:
    """
    Convert a DOCX (BytesIO) to PDF (BytesIO).
    Returns None if conversion is not possible on this system.
    """
    try:
        from docx2pdf import convert

        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_docx:
            tmp_docx.write(docx_buffer.getvalue())
            tmp_docx_path = tmp_docx.name

        tmp_pdf_path = tmp_docx_path.replace(".docx", ".pdf")

        # Convert
        convert(tmp_docx_path, tmp_pdf_path)

        # Read the PDF back into memory
        with open(tmp_pdf_path, "rb") as f:
            pdf_buffer = BytesIO(f.read())

        # Cleanup
        os.unlink(tmp_docx_path)
        if os.path.exists(tmp_pdf_path):
            os.unlink(tmp_pdf_path)

        pdf_buffer.seek(0)
        return pdf_buffer

    except Exception as e:
        print(f"PDF conversion failed: {e}")
        return None