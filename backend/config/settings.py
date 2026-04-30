from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # LLM Configuration
    llm_provider: str = "ollama"  # gpt or ollama
    gpt_api_key: Optional[str] = None
    gpt_model: str = "gpt-4"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3:8b"
    
    # Knowledge Base Configuration
    strapi_url: str = "http://localhost:1337"
    strapi_api_token: Optional[str] = None
    qa_database_url: str = "sqlite:///./qa_database.db"
    
    # Text-to-Speech Configuration
    tts_provider: str = "edge-tts"  # edge-tts or pyttsx3
    tts_voice: str = "hi-IN"  # Indian voice
    tts_accent: str = "indian"
    tts_rate: float = 0.9
    
    # Lip Sync Configuration
    rhubarb_path: str = "/Users/chiefaiofficer/.local/bin/rhubarb"
    audio_sample_rate: int = 22050
    
    # Server Configuration
    avatar_mode: str = "standalone"  # standalone (full pipeline) or temi (receive audio from Temi)
    debug: bool = False
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3003", "http://localhost:8080", "*"]
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    
    # Database Configuration
    database_url: str = "sqlite:///./chronexa.db"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
