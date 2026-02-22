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
    from src.core.pubsub import pubsub_manager
    logger.info("Application starting up...")
    await pubsub_manager.connect()
    
    yield
    
    logger.info("Application shutting down...")
    await pubsub_manager.disconnect()

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
        
    # Include Routers
    from src.modules.auth.router import router as auth_router
    from src.modules.users.router import router as users_router
    
    app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
    app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
    
    from src.modules.conversations.router import router as conversations_router
    app.include_router(conversations_router, prefix=f"{settings.API_V1_STR}/conversations", tags=["Conversations"])
    
    from src.modules.messages.router import router as messages_router
    # mount this at /conversations because the paths in messages_router start with /{conversation_id}/messages
    app.include_router(messages_router, prefix=f"{settings.API_V1_STR}/conversations", tags=["Messages"])
    
    from src.modules.realtime.router import router as realtime_router
    app.include_router(realtime_router, tags=["Realtime"])
    
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    # entry point for debugging
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
