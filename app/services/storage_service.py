"""Storage service for managing file organization."""

import shutil
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.models import DocumentType
from app.utils.logger import get_logger

logger = get_logger()


class StorageService:
    """Service for managing file storage and organization."""

    def __init__(self):
        """Initialize storage service."""
        self.settings = get_settings()
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all required directories exist."""
        self.settings.invoices_path.mkdir(parents=True, exist_ok=True)
        self.settings.others_path.mkdir(parents=True, exist_ok=True)
        self.settings.temp_path.mkdir(parents=True, exist_ok=True)
        logger.info("Storage directories initialized")

    def get_temp_path(self, filename: str) -> Path:
        """
        Get path for temporary file storage.

        Args:
            filename: Name of the file

        Returns:
            Path object for temporary storage
        """
        return self.settings.temp_path / filename

    def move_to_destination(
        self, source_path: Path, document_type: DocumentType, filename: Optional[str] = None
    ) -> str:
        """
        Move file to appropriate destination based on classification.

        Args:
            source_path: Source file path
            document_type: Classification result
            filename: Optional custom filename (defaults to source filename)

        Returns:
            Full path to destination file
        """
        try:
            # Determine destination folder
            if document_type == DocumentType.INVOICE:
                dest_folder = self.settings.invoices_path
                logger.info(f"Moving {source_path.name} to invoices folder")
            else:
                dest_folder = self.settings.others_path
                logger.info(f"Moving {source_path.name} to others folder")

            # Use provided filename or source filename
            dest_filename = filename or source_path.name
            dest_path = dest_folder / dest_filename

            # Handle duplicate filenames
            if dest_path.exists():
                base = dest_path.stem
                ext = dest_path.suffix
                counter = 1
                while dest_path.exists():
                    dest_path = dest_folder / f"{base}_{counter}{ext}"
                    counter += 1
                logger.info(f"Renamed to {dest_path.name} to avoid conflict")

            # Move the file
            shutil.move(str(source_path), str(dest_path))
            logger.info(f"File moved to {dest_path}")

            return str(dest_path)

        except Exception as e:
            logger.error(f"Error moving file: {e}")
            raise

    def cleanup_temp_files(self, older_than_seconds: int = 3600):
        """
        Clean up old temporary files.

        Args:
            older_than_seconds: Remove files older than this many seconds
        """
        try:
            import time
            current_time = time.time()
            removed_count = 0

            for file_path in self.settings.temp_path.glob("*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > older_than_seconds:
                        file_path.unlink()
                        removed_count += 1

            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} temporary files")

        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
