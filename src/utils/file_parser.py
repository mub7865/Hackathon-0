"""
File Parser Utility

Handles text extraction from PDFs and images.
"""

import os
from typing import Optional
from pypdf import PdfReader
from PIL import Image


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text content
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"Error reading PDF: {e}"


def extract_text_from_image(image_path: str) -> dict:
    """
    Load image and return basic metadata.
    For Bronze tier, we'll pass image to Claude's vision API.

    Args:
        image_path: Path to image file

    Returns:
        Dictionary with image metadata
    """
    try:
        img = Image.open(image_path)
        return {
            'format': img.format,
            'size': img.size,
            'mode': img.mode,
            'path': image_path
        }
    except Exception as e:
        return {'error': str(e)}


def get_file_content(file_path: str) -> str:
    """
    Universal file content extractor.

    Args:
        file_path: Path to file

    Returns:
        File content or metadata string
    """
    if not os.path.exists(file_path):
        return "[File not found]"

    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_ext in ['.png', '.jpg', '.jpeg']:
        # For images, return path for Claude vision API
        metadata = extract_text_from_image(file_path)
        if 'error' in metadata:
            return f"[Image error: {metadata['error']}]"
        return f"[Image file: {metadata.get('format')} {metadata.get('size')}]"
    elif file_ext in ['.txt', '.md']:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"[Error reading file: {e}]"
    else:
        return "[Unsupported file type]"


def is_file_too_large(file_path: str, max_size_mb: int = 10) -> bool:
    """
    Check if file exceeds size limit.

    Args:
        file_path: Path to file
        max_size_mb: Maximum file size in MB

    Returns:
        True if file is too large
    """
    max_bytes = max_size_mb * 1024 * 1024
    size = os.path.getsize(file_path)
    return size > max_bytes


def get_file_mime_type(file_path: str) -> str:
    """
    Get MIME type based on file extension.

    Args:
        file_path: Path to file

    Returns:
        MIME type string
    """
    ext = os.path.splitext(file_path)[1].lower()
    mime_types = {
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg'
    }
    return mime_types.get(ext, 'application/octet-stream')
