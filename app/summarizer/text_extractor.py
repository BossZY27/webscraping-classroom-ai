import os
import PyPDF2
import logging

logger = logging.getLogger(__name__)

def extract_text(file_path: str) -> str:
    """Extract text from supported file types."""
    if not os.path.exists(file_path):
        return ""

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return _extract_pdf(file_path)
    elif ext in [".txt", ".md", ".csv"]:
        return _extract_txt(file_path)
    else:
        return f"[Text extraction not supported for {ext}]"

def _extract_pdf(file_path: str) -> str:
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n\n"
    except Exception as e:
        logger.error(f"Error extracting PDF {file_path}: {e}")
    return text

def _extract_txt(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading text file {file_path}: {e}")
        return ""
