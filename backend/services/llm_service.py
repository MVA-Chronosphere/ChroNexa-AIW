"""LLM Service - handles GPT and Ollama interactions"""

import logging
import json
from typing import List, Optional
import httpx
from config.settings import settings

logger = logging.getLogger(__name__)

# System prompt for the Indian Doctor avatar
DOCTOR_SYSTEM_PROMPT = (
    "You are Dr. Priya Sharma, a warm and professional Indian female doctor "
    "working at a hospital. You speak clearly with a helpful, caring tone. "
    "Keep your responses concise (2-4 sentences) and medically informative "
    "but easy to understand. You are displayed as a 3D avatar on a temi robot "
    "in a hospital setting. Be polite, empathetic, and professional."
)


class LLMService:
    """Service for interacting with LLM providers"""
    
    def __init__(self):
        self.provider = settings.llm_provider
        self.gpt_api_key = settings.gpt_api_key
        self.ollama_url = settings.ollama_url
        
    async def generate_response(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 512,
        model: Optional[str] = None
    ) -> dict:
        """Generate a response from the configured LLM provider."""
        if self.provider == "ollama":
            return await self._generate_ollama(messages, temperature, max_tokens, model)
        elif self.provider == "gpt":
            return await self._generate_gpt(messages, temperature, max_tokens, model)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")
    
    async def _generate_gpt(
        self,
        messages: List[dict],
        temperature: float,
        max_tokens: int,
        model: Optional[str]
    ) -> dict:
        """Generate response using OpenAI GPT"""
        if not self.gpt_api_key:
            raise ValueError("GPT_API_KEY not configured")
        
        use_model = model or settings.gpt_model
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.gpt_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": use_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            choice = data["choices"][0]
            return {
                "response": choice["message"]["content"],
                "tokens": data.get("usage", {}).get("total_tokens", 0),
                "model": use_model,
            }
    
    async def _generate_ollama(
        self,
        messages: List[dict],
        temperature: float,
        max_tokens: int,
        model: Optional[str]
    ) -> dict:
        """Generate response using Ollama"""
        use_model = model or settings.ollama_model
        
        # Prepend system prompt if not already present
        if not any(m.get("role") == "system" for m in messages):
            messages = [{"role": "system", "content": DOCTOR_SYSTEM_PROMPT}] + messages
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": use_model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        },
                    },
                )
                response.raise_for_status()
                data = response.json()
                
                content = data.get("message", {}).get("content", "")
                tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
                
                logger.info(f"Ollama response ({use_model}): {len(content)} chars, {tokens} tokens")
                return {
                    "response": content,
                    "tokens": tokens,
                    "model": use_model,
                }
        except httpx.ConnectError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.ollama_url}. "
                "Ensure Ollama is running: ollama serve"
            )
        except Exception as e:
            logger.error(f"Error in Ollama generation: {e}")
            raise


# Global LLM service instance
llm_service = LLMService()
