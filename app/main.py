from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import settings

from contextlib import asynccontextmanager
import logging
from fastapi.responses import RedirectResponse
from app.auth.google_oauth import get_redirect_uri
from app.database import init_db
from app.scheduler.job_manager import start_scheduler
from app.api import routes_auth, routes_courses, routes_files, routes_schedule, routes_ai, routes_export

# Configure the root logger here so module-level loggers are visible under
# uvicorn too (uvicorn only configures its own loggers).
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    # Start background scheduler
    start_scheduler()
    logger.info(
        "Google OAuth redirect URI: %s (register this exact value under "
        "Google Cloud Console > Credentials > your OAuth client)",
        get_redirect_uri(),
    )
    yield
    # Cleanup on shutdown if needed

app = FastAPI(
    title="Google Classroom Scraper",
    description="Automated Google Classroom file downloader and scraper",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(routes_auth.router)
app.include_router(routes_courses.router)
app.include_router(routes_files.router)
app.include_router(routes_schedule.router)
app.include_router(routes_ai.router)
app.include_router(routes_export.router)

@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")

# Mount static files for dashboard
# We will create this directory later
try:
    app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")
except RuntimeError:
    # Handle the case where static directory doesn't exist yet
    pass

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
