from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import logging
import sys

from config.settings import settings
from app.routes import chat, avatar, health, knowledge_base, settings as settings_routes

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ChroNexa AI Avatar API",
    description="AI Avatar API for Temi Robot with LLM support, lip sync, and text-to-speech",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(avatar.router, prefix="/api/avatar", tags=["Avatar"])
app.include_router(knowledge_base.router, prefix="/api/kb", tags=["Knowledge Base"])
app.include_router(settings_routes.router, prefix="/api/settings", tags=["Settings"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ChroNexa AI Avatar API",
        "version": "0.1.0",
        "status": "running"
    }

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"Starting ChroNexa AI Avatar API (LLM: {settings.llm_provider})")
    logger.info(f"Debug mode: {settings.debug}")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down ChroNexa AI Avatar API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
