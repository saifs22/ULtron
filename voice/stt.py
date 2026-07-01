"""
ULTRON Speech-to-Text — Ultron listens.
Uses faster-whisper for local transcription. Push-to-talk or continuous mode.
"""
import threading
import queue
import time
import numpy as np
from typing import Optional, Callable

from providers.base import STTProvider


class WhisperSTT(STTProvider):
    """Local speech-to-text using faster-whisper (CTranslate2-based)."""

    def __init__(self, model_size: str = "base.en", device: str = "cpu"):
        from faster_whisper import WhisperModel
        self.model = WhisperModel(model_size, device=device, compute_type="int8")
        self._sample_rate = 16000
        self._running = False
        self._continuous_thread: Optional[threading.Thread] = None

    @property
    def name(self) -> str:
        return f"Whisper ({self.model})"

    def listen(self, duration: float = 5.0) -> str:
        """Record audio for a fixed duration and transcribe."""
        audio = self._record_audio(duration)
        return self._transcribe(audio)

    def listen_until_silence(self, silence_threshold: float = 0.01,
                              silence_duration: float = 1.5,
                              max_duration: float = 30.0) -> str:
        """Record audio until silence is detected, then transcribe."""
        import sounddevice as sd

        chunks = []
        silent_time = 0.0
        total_time = 0.0
        chunk_duration = 0.5  # Process in 500ms chunks

        print("  [MIC] Listening... (speak now)", flush=True)

        while total_time < max_duration:
            audio_chunk = sd.rec(
                int(chunk_duration * self._sample_rate),
                samplerate=self._sample_rate,
                channels=1,
                dtype="float32",
            )
            sd.wait()
            chunks.append(audio_chunk)
            total_time += chunk_duration

            # Check if this chunk is silent
            rms = np.sqrt(np.mean(audio_chunk ** 2))
            if rms < silence_threshold:
                silent_time += chunk_duration
            else:
                silent_time = 0.0

            # If silence lasted long enough and we have some speech, stop
            if silent_time >= silence_duration and total_time > 2.0:
                break

        if not chunks:
            return ""

        print("  [MIC] Processing...", flush=True)
        audio = np.concatenate(chunks, axis=0)
        return self._transcribe(audio)

    def start_continuous(self, callback: Callable[[str], None]) -> None:
        """Start continuous listening with callback for each transcription."""
        self._running = True
        self._continuous_thread = threading.Thread(
            target=self._continuous_loop,
            args=(callback,),
            daemon=True,
        )
        self._continuous_thread.start()

    def stop_continuous(self) -> None:
        """Stop continuous listening."""
        self._running = False
        if self._continuous_thread:
            self._continuous_thread.join(timeout=3)
            self._continuous_thread = None

    def _continuous_loop(self, callback: Callable[[str], None]) -> None:
        """Background loop for continuous listening."""
        while self._running:
            try:
                text = self.listen_until_silence(max_duration=15.0)
                if text.strip():
                    callback(text.strip())
            except Exception as e:
                print(f"  [STT ERROR] {e}")
                time.sleep(1)

    def _record_audio(self, duration: float) -> np.ndarray:
        """Record audio for a specified duration."""
        import sounddevice as sd
        print(f"  [MIC] Recording for {duration}s...", flush=True)
        audio = sd.rec(
            int(duration * self._sample_rate),
            samplerate=self._sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        print("  [MIC] Processing...", flush=True)
        return audio

    def _transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio array using faster-whisper."""
        # faster-whisper expects float32 mono audio
        if audio.ndim > 1:
            audio = audio.flatten()

        segments, info = self.model.transcribe(
            audio,
            beam_size=5,
            language="en",
            vad_filter=True,
        )

        text = " ".join(seg.text.strip() for seg in segments)
        return text.strip()


class DisabledSTT(STTProvider):
    """No-op STT when voice input is disabled."""

    @property
    def name(self) -> str:
        return "disabled"

    def listen(self, duration: float = 5.0) -> str:
        return ""

    def start_continuous(self, callback) -> None:
        pass

    def stop_continuous(self) -> None:
        pass


def create_stt_provider(config) -> STTProvider:
    """Factory function — create STT provider based on config."""
    if not config.voice_enabled:
        return DisabledSTT()

    provider = config.stt_provider

    if provider == "whisper":
        try:
            return WhisperSTT(model_size=config.whisper_model)
        except ImportError:
            print("  [WARN] faster-whisper not installed. Voice input disabled.")
            print("  [WARN] Install with: pip install faster-whisper sounddevice")
            return DisabledSTT()

    return DisabledSTT()
