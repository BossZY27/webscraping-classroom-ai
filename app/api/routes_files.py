from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db, DownloadedFile, Course
from typing import List, Optional
import os

router = APIRouter(prefix="/api/files", tags=["files"])

@router.get("/")
def list_files(
    course_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get list of downloaded files, optionally filtered by course."""
    query = db.query(DownloadedFile).join(Course)

    if course_id:
        query = query.filter(DownloadedFile.course_id == course_id)

    total = query.count()
    files = query.order_by(desc(DownloadedFile.downloaded_at)).offset(offset).limit(limit).all()

    result = []
    for f in files:
        result.append({
            "id": f.id,
            "course_id": f.course_id,
            "course_name": f.course.name if f.course else "Unknown",
            "filename": f.filename,
            "downloaded_at": f.downloaded_at,
            "file_size": f.file_size
        })

    return {
        "total": total,
        "items": result
    }

@router.get("/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db)):
    """Download the actual file content."""
    file_record = db.query(DownloadedFile).filter(DownloadedFile.id == file_id).first()

    if not file_record or not os.path.exists(file_record.file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_record.file_path,
        filename=file_record.filename
    )
