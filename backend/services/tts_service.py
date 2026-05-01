"""Text-to-Speech Service - handles TTS generation with Indian accent"""

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Optional
import edge_tts
from config.settings import settings

logger = logging.getLogger(__name__)

# Indian voices from Edge TTS — English and Hindi
INDIAN_VOICES = {
    "female": "en-IN-NeerjaNeural",              # Indian English female
    "female_expressive": "en-IN-NeerjaExpressiveNeural",
    "male": "en-IN-PrabhatNeural",                # Indian English male
    "hindi_female": "hi-IN-SwaraNeural",           # Hindi female
    "hindi_male": "hi-IN-MadhurNeural",            # Hindi male
}

# Audio output directory
AUDIO_DIR = Path(tempfile.gettempdir()) / "chronexa_audio"
AUDIO_DIR.mkdir(exist_ok=True)


class TextToSpeechService:
    """Service for text-to-speech generation with Indian accent (English + Hindi)"""
    
    def __init__(self):
        self.provider = settings.tts_provider
        self.voice = INDIAN_VOICES.get("female", "en-IN-NeerjaNeural")
        self.hindi_voice = INDIAN_VOICES.get("hindi_female", "hi-IN-SwaraNeural")
        self.rate = settings.tts_rate
        
    async def synthesize(
        self,
        text: str,
        output_path: Optional[str] = None,
        rate: Optional[float] = None,
        lang: Optional[str] = None,
    ) -> str:
        """
        Synthesize text to speech with Indian accent.
        Supports lang='en' (default) or lang='hi' for Hindi.
        Returns path to generated MP3 file.
        """
        if output_path is None:
            timestamp = int(time.time() * 1000)
            output_path = str(AUDIO_DIR / f"speech_{timestamp}.mp3")
        
        speak_rate = rate or self.rate
        # Edge-TTS rate format: "+0%", "-10%", "+20%"
        rate_str = f"{int((speak_rate - 1.0) * 100):+d}%"
        
        # Select voice based on language
        voice = self.hindi_voice if lang == 'hi' else self.voice
        
        try:
            communicate = edge_tts.Communicate(
                text,
                voice=voice,
                rate=rate_str,
            )
            await communicate.save(output_path)
            
            file_size = os.path.getsize(output_path)
            logger.info(f"Edge-TTS ({voice}): generated {file_size} bytes → {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Edge-TTS synthesis failed: {e}")
            raise
    
    async def get_available_voices(self) -> list:
        """Get list of available Indian English voices"""
        return [
            {"id": v, "name": k, "lang": "en-IN"}
            for k, v in INDIAN_VOICES.items()
        ]


# Global TTS service instance
tts_service = TextToSpeechService()
