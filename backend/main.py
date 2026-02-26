from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from config import settings, get_settings
from database import init_db, get_db
from schemas import SuccessResponse, ErrorResponse
from tasks.scheduled_tasks import get_scheduler, start_scheduler, stop_scheduler
from routes import domains, portfolio, exports
import models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Domain Finder Pro...")
    init_db()
    logger.info("Database initialized")

    # Start scheduled tasks
    try:
        db_session = next(get_db())
        start_scheduler(db_session)
        logger.info("Scheduled tasks started")
    except Exception as e:
        logger.warning(f"Could not start scheduler: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Domain Finder Pro...")
    try:
        stop_scheduler()
        logger.info("Scheduled tasks stopped")
    except Exception as e:
        logger.warning(f"Error stopping scheduler: {e}")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Automated Domain Discovery & Investment Analysis Tool",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route modules
app.include_router(domains.router)
app.include_router(portfolio.router)
app.include_router(exports.router)

# ===== Health Check Endpoints =====

@app.get("/health", response_model=SuccessResponse)
def health_check():
    """Health check endpoint"""
    return SuccessResponse(
        success=True,
        message="Domain Finder Pro is running",
        data={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "timestamp": datetime.now().isoformat(),
        }
    )

@app.get("/api/health")
def api_health_check():
    """API health check"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
    }

# ===== Admin/Debug Endpoints =====

@app.post("/api/admin/manual-scrape")
def manual_scrape_trigger(db: Session = Depends(get_db)):
    """
    Manually trigger daily scrape job (for testing)

    WARNING: Only use for development/testing
    """
    from tasks.scheduled_tasks import TaskScheduler

    try:
        TaskScheduler.daily_scrape_job(db)
        return {
            "success": True,
            "message": "Manual scrape job completed",
        }
    except Exception as e:
        logger.error(f"Manual scrape error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scrape failed: {str(e)}",
        )

@app.get("/api/scheduler/status")
def scheduler_status():
    """Get scheduler status"""
    scheduler = get_scheduler()
    return {
        "running": scheduler.is_running,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in scheduler.scheduler.get_jobs()
        ] if scheduler.is_running else [],
    }

# Root endpoint
@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Domain Finder Pro API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
