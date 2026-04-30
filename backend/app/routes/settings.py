"""Settings and configuration endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import httpx

from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class OllamaConfig(BaseModel):
    """Ollama server configuration"""
    url: str
    model: str


class OllamaTestResponse(BaseModel):
    """Response from Ollama test"""
    status: str
    message: str
    models: Optional[list] = None


@router.get("/ollama")
async def get_ollama_config():
    """Get current Ollama configuration"""
    return {
        "url": settings.ollama_url,
        "model": settings.ollama_model,
        "status": "configured"
    }


@router.post("/ollama")
async def update_ollama_config(config: OllamaConfig):
    """
    Update Ollama server configuration.
    
    This stores the configuration in environment and tests connectivity.
    """
    try:
        # Validate the URL is accessible
        async with httpx.AsyncClient() as client:
            # Test connection to Ollama
            response = await client.get(f"{config.url}/api/tags", timeout=5.0)
            
            if response.status_code == 200:
                models_data = response.json()
                available_models = [m["name"] for m in models_data.get("models", [])]
                
                # Update settings
                settings.ollama_url = config.url
                settings.ollama_model = config.model
                
                logger.info(f"Ollama configuration updated: {config.url}")
                
                return {
                    "status": "success",
                    "message": f"Connected to Ollama at {config.url}",
                    "models": available_models,
                    "selected_model": config.model
                }
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ollama returned status {response.status_code}"
                )
                
    except httpx.ConnectError as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Cannot connect to Ollama at {config.url}. Ensure it's running."
        )
    except Exception as e:
        logger.error(f"Error updating Ollama config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ollama/test")
async def test_ollama_connection():
    """Test connection to current Ollama server"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.ollama_url}/api/tags",
                timeout=5.0
            )
            
            if response.status_code == 200:
                models_data = response.json()
                available_models = [m["name"] for m in models_data.get("models", [])]
                
                return {
                    "status": "success",
                    "message": "Successfully connected to Ollama",
                    "url": settings.ollama_url,
                    "models": available_models,
                    "current_model": settings.ollama_model
                }
            else:
                return {
                    "status": "error",
                    "message": f"Ollama returned status {response.status_code}"
                }
                
    except httpx.ConnectError:
        return {
            "status": "error",
            "message": f"Cannot connect to Ollama at {settings.ollama_url}",
            "url": settings.ollama_url
        }
    except Exception as e:
        logger.error(f"Error testing Ollama: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/system")
async def get_system_config():
    """Get system configuration"""
    return {
        "llm_provider": settings.llm_provider,
        "tts_provider": settings.tts_provider,
        "debug_mode": settings.debug,
        "ollama": {
            "url": settings.ollama_url,
            "model": settings.ollama_model
        },
        "rhubarb": {
            "path": settings.rhubarb_path,
            "audio_sample_rate": settings.audio_sample_rate
        }
    }
