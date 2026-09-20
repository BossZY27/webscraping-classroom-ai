import hashlib
import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import DownloadedFile
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return ""

class FileDeduplicator:
    def __init__(self, db: Session):
        self.db = db

    def check_duplicate(self, drive_file_id: str, drive_modified_at_str: Optional[str] = None) -> bool:
        """
        Check if a file with this ID is already downloaded and hasn't been modified.
        """
        file_record = self.db.query(DownloadedFile).filter(
            DownloadedFile.drive_file_id == drive_file_id
        ).first()

        if not file_record:
            return False

        if not drive_modified_at_str:
            return True # File exists, no modified date to compare

        try:
            # Parse Google Drive timestamp, e.g., "2023-01-15T08:30:00.000Z"
            # Replace Z with +00:00 for fromisoformat compatibility in older python versions
            clean_time_str = drive_modified_at_str.replace("Z", "+00:00")
            drive_modified_at = datetime.fromisoformat(clean_time_str).replace(tzinfo=None)

            # If the remote file is newer than our record, it's not a duplicate (needs update)
            if not file_record.drive_modified_at or drive_modified_at > file_record.drive_modified_at:
                return False

            return True
        except Exception as e:
            logger.warning(f"Error parsing date {drive_modified_at_str}: {e}")
            return True # Default to assuming it's a duplicate if we can't parse date

    def register_file(self,
                      course_id: str,
                      drive_file_id: str,
                      filename: str,
                      file_path: str,
                      mime_type: Optional[str] = None,
                      file_size: Optional[int] = None,
                      drive_modified_at_str: Optional[str] = None) -> DownloadedFile:
        """Register a newly downloaded file in the database."""

        # Calculate hash
        file_hash = calculate_sha256(file_path)

        drive_modified_at = None
        if drive_modified_at_str:
            try:
                clean_time_str = drive_modified_at_str.replace("Z", "+00:00")
                drive_modified_at = datetime.fromisoformat(clean_time_str).replace(tzinfo=None)
            except Exception:
                pass

        # Check if record already exists (maybe we're updating it)
        file_record = self.db.query(DownloadedFile).filter(
            DownloadedFile.drive_file_id == drive_file_id
        ).first()

        if file_record:
            # Update existing
            file_record.filename = filename
            file_record.file_path = file_path
            file_record.sha256_hash = file_hash
            if mime_type: file_record.mime_type = mime_type
            if file_size: file_record.file_size = file_size
            if drive_modified_at: file_record.drive_modified_at = drive_modified_at
            file_record.downloaded_at = datetime.now(timezone.utc)
        else:
            # Create new
            file_record = DownloadedFile(
                course_id=course_id,
                drive_file_id=drive_file_id,
                filename=filename,
                file_path=file_path,
                sha256_hash=file_hash,
                mime_type=mime_type,
                file_size=file_size,
                drive_modified_at=drive_modified_at
            )
            self.db.add(file_record)

        self.db.commit()
        self.db.refresh(file_record)
        return file_record
