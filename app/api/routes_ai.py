from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db, SessionLocal, UserSettings, DownloadedFile
from app.summarizer.ai_client import AISummarizer
from app.summarizer.text_extractor import extract_text
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai"])

class AISettings(BaseModel):
    provider: str # "gemini", "openai", "ollama"
    api_key: str = ""
    endpoint: str = ""

@router.get("/settings")
def get_ai_settings(db: Session = Depends(get_db)):
    settings = db.query(UserSettings).all()
    result = {s.key: s.value for s in settings if s.key.startswith("ai_")}

    return {
        "provider": result.get("ai_provider", "gemini"),
        "api_key": result.get(f"ai_{result.get('ai_provider', 'gemini')}_key", ""),
        "endpoint": result.get("ai_ollama_endpoint", "http://localhost:11434")
    }

@router.post("/settings")
def save_ai_settings(settings: AISettings, db: Session = Depends(get_db)):
    def upsert(key, value):
        rec = db.query(UserSettings).filter(UserSettings.key == key).first()
        if rec:
            rec.value = value
        else:
            db.add(UserSettings(key=key, value=value))

    upsert("ai_provider", settings.provider)
    if settings.provider in ["gemini", "openai"]:
        upsert(f"ai_{settings.provider}_key", settings.api_key)
    if settings.provider == "ollama":
        upsert("ai_ollama_endpoint", settings.endpoint)

    db.commit()
    return {"status": "success"}

def background_summarize(file_id: int):
    db = SessionLocal()
    try:
        file_record = db.query(DownloadedFile).filter(DownloadedFile.id == file_id).first()
        if not file_record:
            return

        # Load settings
        provider_rec = db.query(UserSettings).filter(UserSettings.key == "ai_provider").first()
        provider = provider_rec.value if provider_rec else "gemini"

        api_key = ""
        endpoint = ""
        if provider in ["gemini", "openai"]:
            key_rec = db.query(UserSettings).filter(UserSettings.key == f"ai_{provider}_key").first()
            api_key = key_rec.value if key_rec else ""
        elif provider == "ollama":
            end_rec = db.query(UserSettings).filter(UserSettings.key == "ai_ollama_endpoint").first()
            endpoint = end_rec.value if end_rec else "http://localhost:11434"

        summarizer = AISummarizer(provider=provider, api_key=api_key, endpoint=endpoint)

        # Extract text
        text = extract_text(file_record.file_path)

        # Generate summary
        course_name = file_record.course.name if file_record.course else "Unknown Course"
        summary = summarizer.summarize(text, course_name, file_record.filename)

        # Save summary
        file_record.summary_text = summary
        db.commit()

    except Exception as e:
        logger.error(f"Failed to summarize file {file_id}: {e}")
    finally:
        db.close()

@router.post("/summarize/{file_id}")
def trigger_summarize(file_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    file_record = db.query(DownloadedFile).filter(DownloadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    background_tasks.add_task(background_summarize, file_id)
    return {"status": "success", "message": "Summarization started in background"}

@router.get("/summary/{file_id}")
def get_summary(file_id: int, db: Session = Depends(get_db)):
    file_record = db.query(DownloadedFile).filter(DownloadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    return {"summary": file_record.summary_text}
