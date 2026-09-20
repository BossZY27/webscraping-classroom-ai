from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal, Course, SyncLog, Schedule
from app.scraper.classroom_api import ClassroomClient
from app.scraper.drive_downloader import DriveDownloader
from app.scraper.dedup import FileDeduplicator
from datetime import datetime, timezone
import asyncio
import logging

logger = logging.getLogger(__name__)

# Setup scheduler with SQLite job store
jobstores = {
    'default': SQLAlchemyJobStore(url=settings.DATABASE_URL)
}
scheduler = AsyncIOScheduler(jobstores=jobstores)

def sync_course(course_id: str):
    """
    Background job to sync a specific course.
    Needs its own DB session since it runs asynchronously.
    """
    db = SessionLocal()
    try:
        # Check if we should run (course is tracked)
        course = db.query(Course).filter(Course.id == course_id, Course.is_tracked == True).first()
        if not course:
            return

        logger.info(f"Starting auto-sync for course: {course.name}")

        # Create sync log
        sync_log = SyncLog(course_id=course_id, status="running")
        db.add(sync_log)
        db.commit()
        db.refresh(sync_log)

        try:
            client = ClassroomClient()
            downloader = DriveDownloader()
            deduplicator = FileDeduplicator(db)

            materials = client.get_all_materials(course_id)
            sync_log.files_found = len(materials)

            downloaded = 0
            skipped = 0

            for mat in materials:
                file_id = mat.get('id')
                if not file_id:
                    continue

                update_time = mat.get('updateTime')

                if deduplicator.check_duplicate(file_id, update_time):
                    skipped += 1
                    continue

                file_path = downloader.download_file(file_id, course.name)

                if file_path:
                    deduplicator.register_file(
                        course_id=course_id,
                        drive_file_id=file_id,
                        filename=mat.get('title', 'Unknown'),
                        file_path=file_path,
                        drive_modified_at_str=update_time
                    )
                    downloaded += 1
                else:
                    skipped += 1

            sync_log.files_downloaded = downloaded
            sync_log.files_skipped = skipped
            sync_log.status = "success"
            course.last_synced = datetime.now(timezone.utc)

        except Exception as e:
            sync_log.status = "error"
            sync_log.error_message = str(e)
            logger.error(f"Error syncing course {course_id}: {e}")

        finally:
            sync_log.finished_at = datetime.now(timezone.utc)
            db.commit()

    finally:
        db.close()

def schedule_course_sync(course_id: str, cron_expr: str):
    """Add or update a sync job for a course."""
    job_id = f"sync_course_{course_id}"

    # Remove existing if any
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    # Example cron_expr: "0 9 * * 1" (Every Monday at 9:00 AM)
    trigger = CronTrigger.from_crontab(cron_expr)

    scheduler.add_job(
        sync_course,
        trigger=trigger,
        args=[course_id],
        id=job_id,
        replace_existing=True
    )

def remove_course_schedule(course_id: str):
    """Remove a sync job."""
    job_id = f"sync_course_{course_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

def load_schedules_from_db():
    """Load active schedules from database on startup."""
    db = SessionLocal()
    try:
        active_schedules = db.query(Schedule).filter(Schedule.is_active == True).all()
        for sched in active_schedules:
            schedule_course_sync(sched.course_id, sched.cron_expression)
    finally:
        db.close()

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        load_schedules_from_db()
