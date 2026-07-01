"""
Provider Abstraction Layer — Base classes.
Allows swapping between cloud APIs (Claude, ElevenLabs) and local models
(Ollama, llama.cpp, Piper TTS, Whisper) via config.yaml.
"""
from abc import ABC, abstractmethod
from typing import Optional, Generator


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: Optional[list[dict]] = None,
        max_tokens: int = 4096,
    ) -> dict:
        """
        Send a chat completion request.

        Returns:
            dict with keys:
                - "text": str or None (text response)
                - "tool_calls": list[dict] or None (tool use requests)
                - "stop_reason": str ("end_turn", "tool_use", etc.)
                - "usage": dict with "input_tokens", "output_tokens"
        """
        ...

    @abstractmethod
    def stream_chat(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: Optional[list[dict]] = None,
        max_tokens: int = 4096,
    ) -> Generator[str, None, None]:
        """Stream a chat response token by token."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging."""
        ...


class TTSProvider(ABC):
    """Abstract base class for Text-to-Speech providers."""

    @abstractmethod
    def speak(self, text: str) -> None:
        """Speak text aloud (blocking)."""
        ...

    @abstractmethod
    def speak_async(self, text: str) -> None:
        """Speak text aloud (non-blocking)."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop current speech."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


class STTProvider(ABC):
    """Abstract base class for Speech-to-Text providers."""

    @abstractmethod
    def listen(self, duration: float = 5.0) -> str:
        """Listen for speech and return transcription."""
        ...

    @abstractmethod
    def start_continuous(self, callback) -> None:
        """Start continuous listening with callback for each transcription."""
        ...

    @abstractmethod
    def stop_continuous(self) -> None:
        """Stop continuous listening."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...
