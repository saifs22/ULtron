"""
ULTRON Text-to-Speech — Ultron's voice.
Supports: pyttsx3 (offline), ElevenLabs (premium online), or disabled.
Implements the TTSProvider interface from providers/base.py.
"""
import threading
from providers.base import TTSProvider


class Pyttsx3TTS(TTSProvider):
    """Offline TTS using pyttsx3. Robotic but functional."""

    def __init__(self, rate: int = 150, volume: float = 0.9):
        import pyttsx3
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", rate)
        self._engine.setProperty("volume", volume)

        # Try to select the deepest available voice
        voices = self._engine.getProperty("voices")
        # Prefer male voices — typically index 0 on Windows (David)
        for v in voices:
            if "male" in v.name.lower() or "david" in v.name.lower():
                self._engine.setProperty("voice", v.id)
                break

        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return "pyttsx3 (offline)"

    def speak(self, text: str) -> None:
        """Speak text aloud (blocking)."""
        with self._lock:
            self._engine.say(text)
            self._engine.runAndWait()

    def speak_async(self, text: str) -> None:
        """Speak text in a background thread."""
        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()

    def stop(self) -> None:
        """Stop current speech."""
        try:
            self._engine.stop()
        except Exception:
            pass


class ElevenLabsTTS(TTSProvider):
    """Premium online TTS using ElevenLabs API. Sounds incredible."""

    def __init__(self, api_key: str, voice_id: str = "",
                 model: str = "eleven_multilingual_v2",
                 stability: float = 0.65, similarity: float = 0.80,
                 style: float = 0.35):
        from elevenlabs.client import ElevenLabs

        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        self.model = model
        self.voice_settings = {
            "stability": stability,
            "similarity_boost": similarity,
            "style": style,
        }
        self._lock = threading.Lock()

        # If no voice_id specified, try to find or create a deep male voice
        if not self.voice_id:
            self.voice_id = self._find_default_voice()

    @property
    def name(self) -> str:
        return "ElevenLabs (online)"

    def _find_default_voice(self) -> str:
        """Find a suitable default voice — deep, male, authoritative."""
        try:
            voices = self.client.voices.get_all()
            # Look for voices with deep/male characteristics
            preferred = ["daniel", "adam", "arnold", "clyde", "james"]
            for voice in voices.voices:
                if voice.name.lower() in preferred:
                    return voice.voice_id
            # Fallback to first available
            if voices.voices:
                return voices.voices[0].voice_id
        except Exception:
            pass
        return ""

    def speak(self, text: str) -> None:
        """Speak text using ElevenLabs (blocking — generates and plays audio)."""
        if not self.voice_id:
            return

        with self._lock:
            try:
                import io
                from elevenlabs import VoiceSettings

                audio = self.client.generate(
                    text=text,
                    voice=self.voice_id,
                    model=self.model,
                    voice_settings=VoiceSettings(
                        stability=self.voice_settings["stability"],
                        similarity_boost=self.voice_settings["similarity_boost"],
                        style=self.voice_settings["style"],
                    ),
                )

                # Collect all audio chunks
                audio_bytes = b"".join(audio)

                # Play using pygame
                self._play_audio_bytes(audio_bytes)
            except Exception as e:
                print(f"  [TTS ERROR] {e}")

    def speak_async(self, text: str) -> None:
        """Speak in background thread."""
        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()

    def stop(self) -> None:
        """Stop playback."""
        try:
            import pygame.mixer
            pygame.mixer.music.stop()
        except Exception:
            pass

    @staticmethod
    def _play_audio_bytes(audio_bytes: bytes):
        """Play raw audio bytes using pygame."""
        import io
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            sound = pygame.mixer.Sound(io.BytesIO(audio_bytes))
            sound.play()
            # Wait for playback to finish
            import time
            while pygame.mixer.get_busy():
                time.sleep(0.1)
        except ImportError:
            # Fallback: save to temp file and play with system
            import tempfile
            import subprocess
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name
            import platform
            if platform.system() == "Windows":
                import os
                os.startfile(temp_path)


class DisabledTTS(TTSProvider):
    """No-op TTS when voice is disabled."""

    @property
    def name(self) -> str:
        return "disabled"

    def speak(self, text: str) -> None:
        pass

    def speak_async(self, text: str) -> None:
        pass

    def stop(self) -> None:
        pass


def create_tts_provider(config) -> TTSProvider:
    """Factory function — create TTS provider based on config."""
    if not config.voice_enabled:
        return DisabledTTS()

    provider = config.tts_provider

    if provider == "pyttsx3":
        try:
            return Pyttsx3TTS(rate=config.tts_rate, volume=config.tts_volume)
        except ImportError:
            print("  [WARN] pyttsx3 not installed. Voice disabled.")
            return DisabledTTS()

    elif provider == "elevenlabs":
        if not config.elevenlabs_api_key:
            print("  [WARN] ELEVENLABS_API_KEY not set. Falling back to pyttsx3.")
            try:
                return Pyttsx3TTS(rate=config.tts_rate, volume=config.tts_volume)
            except ImportError:
                return DisabledTTS()
        try:
            return ElevenLabsTTS(
                api_key=config.elevenlabs_api_key,
                voice_id=config.elevenlabs_voice_id,
            )
        except ImportError:
            print("  [WARN] elevenlabs package not installed. Voice disabled.")
            return DisabledTTS()

    return DisabledTTS()
