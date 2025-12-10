from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv
import time
from contextlib import asynccontextmanager
from app.logger import log_info, log_error

load_dotenv()

# Database URL (default points to MySQL via aiomysql)
DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

# Create async engine with optimized settings
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Disable SQL logging in production
    pool_size=20,           # Increased pool size for better concurrency
    max_overflow=30,        # Allow overflow connections
    pool_pre_ping=True,     # Validate connections before use
    pool_recycle=3600,      # Recycle connections every hour
    pool_timeout=30,        # Connection timeout in seconds
    connect_args={
        "charset": "utf8mb4",
        "sql_mode": "STRICT_ALL_TABLES",
    },
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Query performance monitoring
@asynccontextmanager
async def monitor_query(query_name: str):
    """Monitor database query performance."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        if duration > 1.0:  # Log slow queries (>1 second)
            log_error(f"Slow query '{query_name}': {duration:.2f}s")
        elif duration > 0.5:  # Log medium queries (>500ms)
            log_info(f"Query '{query_name}': {duration:.2f}s")

# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
