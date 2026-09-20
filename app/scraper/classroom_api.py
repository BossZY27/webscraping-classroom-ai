from googleapiclient.discovery import build
from app.auth.google_oauth import get_credentials
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ClassroomClient:
    def __init__(self):
        self.creds = get_credentials()
        self.service = build('classroom', 'v1', credentials=self.creds)

    def list_courses(self) -> List[Dict[str, Any]]:
        """List all courses the user is enrolled in."""
        courses = []
        page_token = None

        while True:
            response = self.service.courses().list(
                pageToken=page_token,
                pageSize=100
            ).execute()

            if 'courses' in response:
                courses.extend(response['courses'])

            page_token = response.get('nextPageToken', None)
            if not page_token:
                break

        return courses

    def get_coursework(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all coursework (assignments) for a course."""
        coursework = []
        page_token = None

        while True:
            try:
                response = self.service.courses().courseWork().list(
                    courseId=course_id,
                    pageToken=page_token,
                    pageSize=100
                ).execute()

                if 'courseWork' in response:
                    coursework.extend(response['courseWork'])

                page_token = response.get('nextPageToken', None)
                if not page_token:
                    break
            except Exception as e:
                logger.error(f"Error fetching coursework for {course_id}: {e}")
                break

        return coursework

    def get_announcements(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all announcements for a course."""
        announcements = []
        page_token = None

        while True:
            try:
                response = self.service.courses().announcements().list(
                    courseId=course_id,
                    pageToken=page_token,
                    pageSize=100
                ).execute()

                if 'announcements' in response:
                    announcements.extend(response['announcements'])

                page_token = response.get('nextPageToken', None)
                if not page_token:
                    break
            except Exception as e:
                logger.error(f"Error fetching announcements for {course_id}: {e}")
                break

        return announcements

    def extract_materials_from_item(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract Google Drive materials from a coursework or announcement item."""
        materials = []
        if 'materials' in item:
            for material in item['materials']:
                if 'driveFile' in material:
                    drive_file = material['driveFile']['driveFile']
                    materials.append({
                        'id': drive_file.get('id'),
                        'title': drive_file.get('title'),
                        'alternateLink': drive_file.get('alternateLink'),
                        'source_item_id': item.get('id'),
                        'source_type': 'coursework' if 'workType' in item else 'announcement',
                        'updateTime': item.get('updateTime', item.get('creationTime'))
                    })
        return materials

    def get_all_materials(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all materials from both coursework and announcements."""
        all_materials = []

        # From coursework
        coursework = self.get_coursework(course_id)
        for work in coursework:
            all_materials.extend(self.extract_materials_from_item(work))

        # From announcements
        announcements = self.get_announcements(course_id)
        for ann in announcements:
            all_materials.extend(self.extract_materials_from_item(ann))

        return all_materials
