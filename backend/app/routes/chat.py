"""Chat endpoints for LLM interaction with TTS and lip sync pipeline"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import logging
import os
import base64

from services.llm_service import llm_service
from services.tts_service import tts_service
from services.lip_sync_service import lip_sync_service

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 512
    use_knowledge_base: bool = True


class ChatResponse(BaseModel):
    response: str
    model: str
    tokens_used: int
    source: str  # gpt, ollama, knowledge_base


class SpeakRequest(BaseModel):
    """Full pipeline request: user text → LLM → TTS → lip sync"""
    text: str
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 256


@router.post("/generate", response_model=ChatResponse)
async def generate_response(request: ChatRequest):
    """Generate a response using the configured LLM (Ollama or GPT)."""
    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        result = await llm_service.generate_response(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            model=request.model,
        )
        return ChatResponse(
            response=result["response"],
            model=result["model"],
            tokens_used=result["tokens"],
            source=llm_service.provider,
        )
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speak")
async def speak(request: SpeakRequest):
    """
    Full avatar speaking pipeline:
    1. Send user text to Ollama/GPT → get response
    2. Convert response to speech via Edge-TTS (Indian female voice)
    3. Generate lip sync cues via Rhubarb
    4. Return response text + audio (base64) + mouth cues
    
    The frontend plays the audio and animates lip sync simultaneously.
    """
    try:
        # 1. Get LLM response
        messages = [{"role": "user", "content": request.text}]
        llm_result = await llm_service.generate_response(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            model=request.model,
        )
        response_text = llm_result["response"]
        logger.info(f"LLM response: {response_text[:100]}...")

        # 2. Generate TTS audio
        audio_path = await tts_service.synthesize(response_text)
        logger.info(f"TTS audio: {audio_path}")

        # 3. Generate lip sync cues from the audio
        lip_sync = await lip_sync_service.generate_lip_sync(
            audio_path=audio_path,
            text=response_text,
        )
        logger.info(f"Lip sync: {len(lip_sync.get('mouthCues', []))} cues")

        # 4. Read audio file and encode as base64
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        # Determine MIME type
        mime = "audio/mpeg" if audio_path.endswith(".mp3") else "audio/wav"

        return {
            "status": "success",
            "response_text": response_text,
            "audio_data": f"data:{mime};base64,{audio_b64}",
            "audio_duration": lip_sync.get("duration", 0),
            "mouth_cues": lip_sync.get("mouthCues", []),
            "model": llm_result["model"],
            "tokens": llm_result["tokens"],
        }

    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Speak pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_response(request: ChatRequest):
    """Stream a response (WebSocket upgrade — placeholder)."""
    raise HTTPException(status_code=501, detail="Streaming not yet implemented")


class AnimateRequest(BaseModel):
    """Temi mode: receive pre-generated audio, return lip sync cues only."""
    audio_base64: str  # base64-encoded audio (mp3 or wav)
    mime_type: str = "audio/mpeg"  # audio/mpeg or audio/wav
    text: Optional[str] = None  # optional transcript for better lip sync


@router.post("/animate")
async def animate(request: AnimateRequest):
    """
    Temi integration endpoint:
    - Accepts audio from Temi's own TTS (base64-encoded)
    - Generates lip sync cues via Rhubarb
    - Returns audio data URI + mouth cues for the avatar
    
    The Kotlin app calls this after getting a response from Temi's
    knowledge base and generating speech with Temi's TTS.
    """
    import tempfile
    try:
        # Decode audio
        audio_bytes = base64.b64decode(request.audio_base64)
        suffix = ".mp3" if "mpeg" in request.mime_type else ".wav"

        # Write to temp file for Rhubarb
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            audio_path = tmp.name

        # Generate lip sync cues
        lip_sync = await lip_sync_service.generate_lip_sync(
            audio_path=audio_path,
            text=request.text or "",
        )
        logger.info(f"[Temi] Lip sync: {len(lip_sync.get('mouthCues', []))} cues")

        # Clean up temp file
        try:
            os.unlink(audio_path)
        except OSError:
            pass

        audio_data_uri = f"data:{request.mime_type};base64,{request.audio_base64}"

        return {
            "status": "success",
            "audio_data": audio_data_uri,
            "audio_duration": lip_sync.get("duration", 0),
            "mouth_cues": lip_sync.get("mouthCues", []),
        }

    except Exception as e:
        logger.error(f"Animate pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_available_models():
    """Get list of available LLM models"""
    return {
        "models": [
            {"name": "gpt-4", "provider": "openai", "active": llm_service.provider == "gpt"},
            {"name": "llama3:8b", "provider": "ollama", "active": llm_service.provider == "ollama"},
        ]
    }
