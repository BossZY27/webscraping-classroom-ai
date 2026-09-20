import os
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from app.config import settings

# Create directory for SQLite DB if it doesn't exist
db_path = settings.DATABASE_URL.replace("sqlite:///", "")
if db_path != ":memory:":
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Course(Base):
    __tablename__ = "courses"

    id = Column(String, primary_key=True, index=True) # Classroom course ID
    name = Column(String, index=True)
    section = Column(String, nullable=True)
    is_tracked = Column(Boolean, default=False)
    last_synced = Column(DateTime, nullable=True)

    files = relationship("DownloadedFile", back_populates="course")
    schedules = relationship("Schedule", back_populates="course")
    logs = relationship("SyncLog", back_populates="course")

class DownloadedFile(Base):
    __tablename__ = "downloaded_files"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String, ForeignKey("courses.id"))
    drive_file_id = Column(String, unique=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    sha256_hash = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    drive_modified_at = Column(DateTime, nullable=True)
    downloaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    summary_text = Column(String, nullable=True) # New column for AI summary

    course = relationship("Course", back_populates="files")

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String, ForeignKey("courses.id"))
    cron_expression = Column(String)
    is_auto_detected = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    next_run = Column(DateTime, nullable=True)

    course = relationship("Course", back_populates="schedules")

class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String, ForeignKey("courses.id"))
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime, nullable=True)
    files_found = Column(Integer, default=0)
    files_downloaded = Column(Integer, default=0)
    files_skipped = Column(Integer, default=0)
    status = Column(String) # "success" / "error"
    error_message = Column(String, nullable=True)

    course = relationship("Course", back_populates="logs")

class UserSettings(Base):
    __tablename__ = "user_settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)
