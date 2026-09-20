import os
import io
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from app.auth.google_oauth import get_credentials
from typing import Dict, Any, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)

class DriveDownloader:
    def __init__(self):
        self.creds = get_credentials()
        self.service = build('drive', 'v3', credentials=self.creds)
        self.base_download_dir = "downloads"

    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get file metadata from Drive API."""
        try:
            return self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, modifiedTime, size, md5Checksum"
            ).execute()
        except Exception as e:
            logger.error(f"Error getting metadata for {file_id}: {e}")
            return {}

    def get_export_mime_type(self, mime_type: str) -> Tuple[Optional[str], Optional[str]]:
        """Determine export format for Google Workspace documents."""
        # Map Google Workspace formats to exportable formats
        export_map = {
            'application/vnd.google-apps.document': ('application/pdf', '.pdf'),
            'application/vnd.google-apps.spreadsheet': ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx'),
            'application/vnd.google-apps.presentation': ('application/pdf', '.pdf'),
        }
        return export_map.get(mime_type, (None, None))

    def _get_unique_path(self, file_path: str) -> str:
        """Ensure file path is unique by appending _1, _2 etc if it exists."""
        if not os.path.exists(file_path):
            return file_path

        base, ext = os.path.splitext(file_path)
        counter = 1
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1

        return f"{base}_{counter}{ext}"

    def download_file(self, file_id: str, course_name: str, file_metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Download a file from Drive.
        Returns the absolute path to the downloaded file.
        """
        if not file_metadata:
            file_metadata = self.get_file_metadata(file_id)

        if not file_metadata:
            return None

        mime_type = file_metadata.get('mimeType', '')
        original_name = file_metadata.get('name', f'file_{file_id}')

        # Clean course name for folder path using regex to preserve Thai characters
        clean_course_name = re.sub(r'[<>:"/\\|?*]', '_', course_name).strip()
        today_date = datetime.now().strftime('%Y-%m-%d')

        # Create directory
        save_dir = os.path.join(self.base_download_dir, clean_course_name, today_date)
        os.makedirs(save_dir, exist_ok=True)

        export_mime, ext = self.get_export_mime_type(mime_type)

        if export_mime:
            # It's a Google Workspace document, need to export
            if not original_name.endswith(ext):
                file_name = f"{original_name}{ext}"
            else:
                file_name = original_name

            file_path = os.path.join(save_dir, file_name)
            file_path = self._get_unique_path(file_path)

            try:
                request = self.service.files().export_media(fileId=file_id, mimeType=export_mime)
                self._download_request(request, file_path)
                return file_path
            except Exception as e:
                logger.error(f"Error exporting file {file_id}: {e}")
                return None
        else:
            # Regular file, direct download
            file_name = original_name
            file_path = os.path.join(save_dir, file_name)
            file_path = self._get_unique_path(file_path)

            try:
                request = self.service.files().get_media(fileId=file_id)
                self._download_request(request, file_path)
                return file_path
            except Exception as e:
                logger.error(f"Error downloading file {file_id}: {e}")
                return None

    def _download_request(self, request, file_path: str):
        """Helper to execute the download request in chunks."""
        with io.FileIO(file_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                # print(f"Download {int(status.progress() * 100)}%.")
