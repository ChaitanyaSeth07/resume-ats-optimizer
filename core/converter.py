"""
Converter Module (with secure temp file handling)
"""

from io import BytesIO
import tempfile
import os
from typing import Optional


def convert_docx_to_pdf(docx_buffer: BytesIO) -> Optional[BytesIO]:
    """
    Convert DOCX to PDF with proper temporary file cleanup.
    """
    tmp_docx_path = None
    tmp_pdf_path = None

    try:
        from docx2pdf import convert

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_docx:
            tmp_docx.write(docx_buffer.getvalue())
            tmp_docx_path = tmp_docx.name

        tmp_pdf_path = tmp_docx_path.replace(".docx", ".pdf")

        convert(tmp_docx_path, tmp_pdf_path)

        with open(tmp_pdf_path, "rb") as f:
            pdf_buffer = BytesIO(f.read())

        pdf_buffer.seek(0)
        return pdf_buffer

    except Exception as e:
        print(f"PDF conversion failed: {e}")
        return None

    finally:
        # Always try to clean up temporary files
        for path in [tmp_docx_path, tmp_pdf_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception:
                    pass