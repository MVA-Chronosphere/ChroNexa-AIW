"""Lip Sync Service - handles Rhubarb integration for mouth shape generation"""

import logging
import subprocess
import json
import asyncio
from pathlib import Path
from typing import Optional, List
from config.settings import settings

logger = logging.getLogger(__name__)


class LipSyncService:
    """Service for generating lip sync data using Rhubarb"""
    
    def __init__(self):
        self.rhubarb_path = settings.rhubarb_path
        self.sample_rate = settings.audio_sample_rate
        self._rhubarb_available = None
        
    def _check_rhubarb(self) -> bool:
        """Check if Rhubarb is installed and accessible"""
        if self._rhubarb_available is not None:
            return self._rhubarb_available
        try:
            result = subprocess.run(
                [self.rhubarb_path, "--version"],
                capture_output=True,
                timeout=5,
            )
            self._rhubarb_available = result.returncode == 0
            if self._rhubarb_available:
                ver = result.stdout.decode().strip()
                logger.info(f"Rhubarb found: {ver}")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._rhubarb_available = False
            logger.warning(f"Rhubarb not found at {self.rhubarb_path}")
        return self._rhubarb_available
        
    async def generate_lip_sync(
        self,
        audio_path: str,
        text: Optional[str] = None,
    ) -> dict:
        """
        Generate Rhubarb mouth cues from an audio file.
        
        Returns dict with 'mouthCues' array:
          [ { "start": 0.00, "end": 0.12, "value": "X" }, ... ]
        These are Rhubarb shapes A-H,X which the frontend maps to Oculus visemes.
        """
        if not self._check_rhubarb():
            logger.warning("Rhubarb not available — generating placeholder cues")
            return self._placeholder_cues(text or "")
        
        # Build rhubarb command
        cmd = [self.rhubarb_path, "-f", "json", "--quiet"]
        
        # If we have the transcript text, pass it for better accuracy
        dialog_file = None
        if text:
            dialog_file = Path(audio_path).with_suffix(".txt")
            dialog_file.write_text(text, encoding="utf-8")
            cmd.extend(["-d", str(dialog_file)])
        
        cmd.append(audio_path)
        
        try:
            logger.info(f"Running Rhubarb: {' '.join(cmd)}")
            proc = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            
            if dialog_file and dialog_file.exists():
                dialog_file.unlink()
            
            if proc.returncode != 0:
                logger.error(f"Rhubarb failed (rc={proc.returncode}): {proc.stderr}")
                return self._placeholder_cues(text or "")
            
            data = json.loads(proc.stdout)
            cues = data.get("mouthCues", [])
            duration = data.get("metadata", {}).get("duration", 0)
            
            logger.info(f"Rhubarb: {len(cues)} mouth cues, {duration:.2f}s duration")
            return {
                "mouthCues": cues,
                "duration": duration,
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Rhubarb timed out")
            return self._placeholder_cues(text or "")
        except json.JSONDecodeError as e:
            logger.error(f"Rhubarb JSON parse error: {e}")
            return self._placeholder_cues(text or "")
        except Exception as e:
            logger.error(f"Rhubarb error: {e}")
            return self._placeholder_cues(text or "")
    
    def _placeholder_cues(self, text: str) -> dict:
        """Generate simple placeholder mouth cues from text length."""
        if not text:
            return {"mouthCues": [], "duration": 0}
        
        # Rough timing: ~4 chars per second, alternate shapes
        chars_per_sec = 4.0
        duration = len(text) / chars_per_sec
        shapes = ["X", "D", "C", "B", "E", "F", "A"]
        cues = []
        words = text.split()
        t = 0.0
        for i, word in enumerate(words):
            word_dur = len(word) / chars_per_sec
            cues.append({
                "start": round(t, 3),
                "end": round(t + word_dur, 3),
                "value": shapes[i % len(shapes)],
            })
            t += word_dur + 0.08  # small gap between words
        
        return {"mouthCues": cues, "duration": round(t, 3)}


# Global lip sync service instance
lip_sync_service = LipSyncService()
