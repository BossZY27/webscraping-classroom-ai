from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db, DownloadedFile, Course
from app.summarizer.text_extractor import extract_text
import os
import zipfile
from datetime import datetime

router = APIRouter(prefix="/api/export", tags=["export"])

EXPORT_DIR = "downloads/exports"

@router.get("/{course_id}/zip")
def export_course_zip(course_id: str, db: Session = Depends(get_db)):
    """Export all downloaded files for a course as a ZIP file."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    files = db.query(DownloadedFile).filter(DownloadedFile.course_id == course_id).all()
    if not files:
        raise HTTPException(status_code=404, detail="No files found for this course")

    os.makedirs(EXPORT_DIR, exist_ok=True)
    zip_filename = f"{course.name.replace(' ', '_')}_files_{datetime.now().strftime('%Y%m%d%H%M')}.zip"
    zip_path = os.path.join(EXPORT_DIR, zip_filename)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in files:
            if os.path.exists(f.file_path):
                zipf.write(f.file_path, arcname=f.filename)

    return FileResponse(
        path=zip_path,
        filename=zip_filename,
        media_type="application/zip"
    )

@router.get("/{course_id}/text")
def export_course_text(course_id: str, db: Session = Depends(get_db)):
    """Extract text from all files for a course and combine into a single Markdown file."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    files = db.query(DownloadedFile).filter(DownloadedFile.course_id == course_id).all()
    if not files:
        raise HTTPException(status_code=404, detail="No files found for this course")

    os.makedirs(EXPORT_DIR, exist_ok=True)
    txt_filename = f"{course.name.replace(' ', '_')}_combined_{datetime.now().strftime('%Y%m%d%H%M')}.md"
    txt_path = os.path.join(EXPORT_DIR, txt_filename)

    with open(txt_path, 'w', encoding='utf-8') as out_f:
        out_f.write(f"# Course Materials: {course.name}\n\n")

        for f in files:
            if os.path.exists(f.file_path):
                out_f.write(f"## File: {f.filename}\n\n")
                text = extract_text(f.file_path)
                out_f.write(text if text else "*[No text could be extracted from this file]*")
                out_f.write("\n\n---\n\n")

    return FileResponse(
        path=txt_path,
        filename=txt_filename,
        media_type="text/markdown"
    )
