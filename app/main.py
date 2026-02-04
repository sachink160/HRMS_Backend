from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import engine
from app.models import Base
from app.routes import auth, users, leaves, holidays, admin, email, employees, tasks, tracker, logs, time_corrections
from app.logger import log_info, log_error
from app.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.response import APIResponse
from app.storage import STORAGE_TYPE
from app.scheduler import start_scheduler, shutdown_scheduler, scheduler
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    log_info("Starting HRMS Backend Application")
    # Note: Database schema is managed through Alembic migrations
    # Run: python run_alembic_migration.py upgrade head
    # to ensure database is up to date
    
    # Start scheduler for automated tasks
    try:
        start_scheduler()
        log_info("Scheduler initialization completed")
    except Exception as e:
        log_error(f"Failed to start scheduler during application startup: {str(e)}", exc_info=e)
        # Don't raise - allow application to start even if scheduler fails
    
    yield
    
    # Shutdown
    log_info("Shutting down HRMS Backend Application")
    try:
        shutdown_scheduler()
    except Exception as e:
        log_error(f"Error shutting down scheduler: {str(e)}", exc_info=e)

# Create FastAPI app
app = FastAPI(
    title="HRMS Backend API",
    description="A comprehensive Human Resource Management System backend built with FastAPI and PostgreSQL",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register exception handlers for standardized error responses
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(leaves.router)
app.include_router(holidays.router)
app.include_router(admin.router)
app.include_router(email.router)
app.include_router(employees.router)
app.include_router(tasks.router)
app.include_router(tracker.router)
app.include_router(logs.router)
app.include_router(time_corrections.router)

# Mount static files for uploaded documents (only for local storage)
# For S3 storage, files are served directly from S3 URLs
if STORAGE_TYPE == "local":
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    log_info("Local file storage enabled - static files mounted at /uploads")
else:
    log_info(f"S3 storage enabled - files will be served from S3 bucket")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return APIResponse.success(
        data={
            "message": "HRMS Backend API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        message="HRMS Backend API is running"
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return APIResponse.success(
        data={"status": "healthy"},
        message="HRMS Backend is running"
    )

@app.get("/scheduler/status")
async def scheduler_status():
    """Check scheduler status and jobs."""
    try:
        jobs = []
        if scheduler.running:
            for job in scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                    "trigger": str(job.trigger)
                })
        
        return APIResponse.success(
            data={
                "scheduler_running": scheduler.running,
                "jobs": jobs,
                "job_count": len(jobs)
            },
            message="Scheduler status retrieved"
        )
    except Exception as e:
        log_error(f"Error getting scheduler status: {str(e)}", exc_info=e)
        return APIResponse.internal_error(message="Failed to get scheduler status")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
