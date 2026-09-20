from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.auth.google_oauth import NotAuthenticatedError, credentials_version
from app.database import get_db, Course
from app.scraper.classroom_api import ClassroomClient
from app.scheduler.job_manager import sync_course
from typing import List, Dict, Any

router = APIRouter(prefix="/api/courses", tags=["courses"])

_cached_client = None
_cached_client_version = -1

def get_classroom_client():
    """Reuse one API client, but rebuild it after a new sign-in."""
    global _cached_client, _cached_client_version
    version = credentials_version()
    if _cached_client is None or _cached_client_version != version:
        _cached_client = ClassroomClient()
        _cached_client_version = version
    return _cached_client

@router.get("/")
def list_courses(db: Session = Depends(get_db)):
    """Get all courses from Google Classroom and merge with DB tracked status."""
    try:
        client = get_classroom_client()
        g_courses = client.list_courses()
    except NotAuthenticatedError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    db_courses = {c.id: c for c in db.query(Course).all()}

    result = []
    for gc in g_courses:
        course_id = gc.get("id")
        tracked = False
        last_synced = None

        if course_id in db_courses:
            tracked = db_courses[course_id].is_tracked
            last_synced = db_courses[course_id].last_synced

        result.append({
            "id": course_id,
            "name": gc.get("name"),
            "section": gc.get("section", ""),
            "is_tracked": tracked,
            "last_synced": last_synced
        })

    return result

@router.post("/sync/all")
def trigger_sync_all(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually trigger a sync for all tracked courses."""
    tracked_courses = db.query(Course).filter(Course.is_tracked == True).all()

    if not tracked_courses:
        return {"status": "success", "message": "No tracked courses found"}

    for course in tracked_courses:
        background_tasks.add_task(sync_course, course.id)

    return {"status": "success", "message": f"Sync started for {len(tracked_courses)} courses"}

@router.post("/{course_id}/track")
def track_course(course_id: str, name: str, section: str = "", db: Session = Depends(get_db)):
    """Enable or disable tracking for a course."""
    course = db.query(Course).filter(Course.id == course_id).first()

    if not course:
        course = Course(id=course_id, name=name, section=section, is_tracked=True)
        db.add(course)
    else:
        course.is_tracked = not course.is_tracked

    db.commit()
    return {"status": "success", "is_tracked": course.is_tracked}

@router.post("/{course_id}/sync")
def trigger_sync(course_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually trigger a sync for a tracked course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course or not course.is_tracked:
        raise HTTPException(status_code=400, detail="Course must be tracked before syncing")

    background_tasks.add_task(sync_course, course_id)
    return {"status": "success", "message": "Sync started in background"}
