from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db, Schedule, Course
from app.scheduler.job_manager import schedule_course_sync, remove_course_schedule

router = APIRouter(prefix="/api/schedule", tags=["schedule"])

class ScheduleCreate(BaseModel):
    course_id: str
    cron_expression: str

@router.get("/")
def list_schedules(db: Session = Depends(get_db)):
    """List all active schedules."""
    schedules = db.query(Schedule).join(Course).all()

    result = []
    for s in schedules:
        result.append({
            "id": s.id,
            "course_id": s.course_id,
            "course_name": s.course.name if s.course else "Unknown",
            "cron_expression": s.cron_expression,
            "is_active": s.is_active
        })
    return result

@router.post("/")
def create_schedule(sched: ScheduleCreate, db: Session = Depends(get_db)):
    """Create or update a schedule for a course."""
    course = db.query(Course).filter(Course.id == sched.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check existing
    db_sched = db.query(Schedule).filter(Schedule.course_id == sched.course_id).first()
    if db_sched:
        db_sched.cron_expression = sched.cron_expression
        db_sched.is_active = True
    else:
        db_sched = Schedule(
            course_id=sched.course_id,
            cron_expression=sched.cron_expression,
            is_active=True
        )
        db.add(db_sched)

    db.commit()

    # Update apscheduler
    schedule_course_sync(sched.course_id, sched.cron_expression)

    return {"status": "success", "message": "Schedule updated"}

@router.delete("/{course_id}")
def delete_schedule(course_id: str, db: Session = Depends(get_db)):
    """Remove schedule for a course."""
    sched = db.query(Schedule).filter(Schedule.course_id == course_id).first()
    if sched:
        db.delete(sched)
        db.commit()

    remove_course_schedule(course_id)
    return {"status": "success"}
