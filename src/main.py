from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.core.config import get_settings
from src.core.logging import setup_logging
import logging

# Initialize settings and logging
settings = get_settings()
setup_logging()
logger = logging.getLogger("chat_api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events: Startup and Shutdown logic.
    Use this for connecting to DBs, Redis, etc.
    """
    logger.info("Application starting up...")
    
    yield
    
    logger.info("Application shutting down...")

def create_app() -> FastAPI:
    """
    Factory function to create the FastAPI application.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan
    )
    
    # Root endpoint for health check
    @app.get("/")
    async def root():
        return {
            "message": "Headless Chat API is running", 
            "docs": "/docs"
        }
        
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    # entry point for debugging
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
