"""Health check endpoints"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "ChroNexa AI Avatar API"
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check - ensures all services are initialized"""
    return {
        "status": "ready",
        "service": "ChroNexa AI Avatar API"
    }
