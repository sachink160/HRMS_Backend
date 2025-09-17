from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import engine
from app.models import Base
from app.routes import auth, users, leaves, holidays, trackers, admin
from app.logger import log_info, log_error
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    log_info("Starting HRMS Backend Application")
    try:
        # Create database tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log_info("Database tables created successfully")
    except Exception as e:
        log_error(f"Database initialization error: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    log_info("Shutting down HRMS Backend Application")

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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(leaves.router)
app.include_router(holidays.router)
app.include_router(trackers.router)
app.include_router(admin.router)

# Mount static files for uploaded documents
if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "HRMS Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "HRMS Backend is running"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
