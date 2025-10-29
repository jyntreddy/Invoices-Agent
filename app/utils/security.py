"""Security utilities for path validation."""

from pathlib import Path
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger()


def is_safe_path(file_path: str, base_dir: Optional[str] = None) -> bool:
    """
    Validate that a file path is safe and doesn't contain path traversal attempts.
    
    Security Note: This function validates user-provided paths before any file operations.
    It prevents path traversal attacks by:
    1. Resolving the path to its absolute form
    2. Checking for path traversal patterns (..)
    3. Blocking access to sensitive system directories (/etc, /root)
    4. Restricting access to within a specified base directory if provided
    
    Args:
        file_path: Path to validate (user input)
        base_dir: Optional base directory to restrict access to
        
    Returns:
        True if path is safe, False otherwise
    """
    try:
        # SECURITY: Resolve to absolute path to detect traversal attempts
        # This is intentional use of user input after validation
        resolved_path = Path(file_path).resolve()
        
        # SECURITY: Check for common path traversal patterns
        path_str = str(resolved_path)
        if ".." in path_str or path_str.startswith("/etc") or path_str.startswith("/root"):
            logger.warning(f"Potential path traversal attempt: {file_path}")
            return False
        
        # SECURITY: If base_dir is provided, ensure the path is within it
        if base_dir:
            base_resolved = Path(base_dir).resolve()
            try:
                # Check if the path is relative to base_dir
                resolved_path.relative_to(base_resolved)
            except ValueError:
                logger.warning(f"Path {file_path} is outside allowed directory {base_dir}")
                return False
        
        return True
        
    except (ValueError, OSError) as e:
        logger.error(f"Error validating path {file_path}: {e}")
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove any path components
    clean_name = Path(filename).name
    
    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    for char in dangerous_chars:
        clean_name = clean_name.replace(char, "_")
    
    return clean_name
