"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from solar_analyzer.api.routes import router as api_router
from solar_analyzer.config import settings
from solar_analyzer.data.database import engine
from solar_analyzer.data.models import Base
from solar_analyzer.logging_config import setup_logging, get_logger
from solar_analyzer.visualization.dashboard import router as dashboard_router

# Initialize logging
setup_logging()
logger = get_logger("solar_analyzer.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Solar Analyzer application", version=settings.app_version)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Solar Analyzer application")
    await engine.dispose()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

# Include dashboard routes
app.include_router(dashboard_router)

# Mount static files
app.mount("/static", StaticFiles(directory="src/solar_analyzer/static"), name="static")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


def main():
    """Run the application."""
    import uvicorn

    uvicorn.run(
        "solar_analyzer.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )


if __name__ == "__main__":
    main()