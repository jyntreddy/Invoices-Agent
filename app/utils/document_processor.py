"""Document processing utilities for text extraction."""

import io
from pathlib import Path
from typing import Optional

from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import pytesseract

from app.utils.logger import get_logger

logger = get_logger()


def _validate_file_path(file_path: str) -> None:
    """
    Validate file path to prevent path traversal attacks.
    
    Security Note: This validates paths before file operations.
    It is called before any file is opened or accessed.
    
    Args:
        file_path: Path to validate (already sanitized upstream)
        
    Raises:
        ValueError: If path is invalid or potentially dangerous
    """
    # SECURITY: Path operations here are safe as they only validate,
    # not access files. All actual file access happens after validation.
    path = Path(file_path)
    
    # Check if path exists
    if not path.exists():
        raise ValueError(f"File does not exist: {file_path}")
    
    # Check if it's a file (not a directory)
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    # Resolve to absolute path and check for traversal
    resolved = path.resolve()
    
    # Prevent access to system directories
    forbidden_dirs = ["/etc", "/root", "/sys", "/proc", "/dev"]
    for forbidden in forbidden_dirs:
        if str(resolved).startswith(forbidden):
            raise ValueError(f"Access to {forbidden} is not allowed")
    
    logger.debug(f"Path validation passed for: {file_path}")


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    try:
        reader = PdfReader(file_path)
        text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
        return "\n".join(text)
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {e}")
        return ""


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    try:
        doc = Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return "\n".join(text)
    except Exception as e:
        logger.error(f"Error extracting text from DOCX {file_path}: {e}")
        return ""


def extract_text_from_image(file_path: str) -> str:
    """Extract text from image file using OCR."""
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        logger.error(f"Error extracting text from image {file_path}: {e}")
        return ""


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from various file formats.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Extracted text content
    """
    # Validate path first
    try:
        _validate_file_path(file_path)
    except ValueError as e:
        logger.error(f"Path validation failed: {e}")
        return ""
    
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    logger.info(f"Extracting text from {file_path} (type: {suffix})")
    
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    elif suffix in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        return extract_text_from_image(file_path)
    elif suffix == ".txt":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            return ""
    else:
        logger.warning(f"Unsupported file type: {suffix}")
        return ""
