"""
ULTRON Configuration System
Loads settings from config.yaml and environment variables.
Supports provider abstraction for future local model swaps.
"""
import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


DEFAULT_CONFIG = {
    "general": {
        "safe_mode": False,
        "proactive_level": 2,       # 0=silent, 1=critical, 2=normal, 3=verbose
        "kill_phrase": "SHUTDOWN ULTRON",
    },
    "providers": {
        "llm": {
            "active": "claude",     # "claude" | "local" | "ollama"
            "claude": {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 4096,
            },
            "local": {
                "model_path": "",
                "context_length": 8192,
            },
            "ollama": {
                "model": "llama3",
                "base_url": "http://localhost:11434",
            },
        },
        "tts": {
            "active": "pyttsx3",    # "pyttsx3" | "elevenlabs" | "local"
            "pyttsx3": {
                "rate": 150,
                "volume": 0.9,
            },
            "elevenlabs": {
                "voice_id": "",
                "model": "eleven_multilingual_v2",
                "stability": 0.65,
                "similarity": 0.80,
                "style": 0.35,
            },
            "local": {
                "model_path": "",
            },
        },
        "stt": {
            "active": "none",       # "none" | "whisper" | "local"
            "whisper": {
                "model_size": "base.en",
            },
            "local": {
                "model_path": "",
            },
        },
        "search": {
            "active": "duckduckgo", # "tavily" | "duckduckgo"
        },
    },
    "proactive": {
        "monitor_interval": 30,     # seconds between metric checks
        "idle_threshold_min": 5,    # minutes before idle comment
        "joke_interval_min": 30,    # min minutes between jokes
        "joke_interval_max": 90,    # max minutes between jokes
        "cpu_threshold": 85,
        "ram_threshold": 90,
        "disk_threshold": 95,
    },
    "voice": {
        "enabled": False,
        "input_mode": "push_to_talk",  # "push_to_talk" | "wake_word" | "always_on"
        "push_to_talk_key": "ctrl+shift+u",
    },
    "memory": {
        "db_path": "ultron_memory.db",
        "max_conversation_history": 20,
    },
    "safety": {
        "log_path": "logs/ultron_actions.log",
        "error_log_path": "logs/ultron_errors.log",
        "blocked_commands": [
            "format", "del /s", "rm -rf", "reg delete",
            "shutdown /s", "shutdown /r", "shutdown -s", "shutdown -r",
        ],
        "allowed_directories": [],  # Empty = allow all (except system)
        "restricted_paths": [
            "C:\\Windows",
            "C:\\Program Files",
            "C:\\Program Files (x86)",
        ],
    },
}


@dataclass
class Config:
    """Centralized configuration for ULTRON."""

    # API Keys (from .env)
    anthropic_api_key: str = ""
    tavily_api_key: str = ""
    elevenlabs_api_key: str = ""

    # General
    safe_mode: bool = False
    proactive_level: int = 2
    kill_phrase: str = "SHUTDOWN ULTRON"

    # Provider selections
    llm_provider: str = "claude"
    tts_provider: str = "pyttsx3"
    stt_provider: str = "none"
    search_provider: str = "duckduckgo"

    # LLM settings
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096

    # Ollama settings
    ollama_model: str = "llama3"
    ollama_base_url: str = "http://localhost:11434"

    # Local LLM settings
    local_model_path: str = ""
    local_context_length: int = 8192

    # TTS settings
    tts_rate: int = 150
    tts_volume: float = 0.9
    elevenlabs_voice_id: str = ""

    # STT settings
    whisper_model: str = "base.en"

    # Proactive
    monitor_interval: int = 30
    idle_threshold_min: int = 5
    joke_interval_min: int = 30
    joke_interval_max: int = 90
    cpu_threshold: int = 85
    ram_threshold: int = 90
    disk_threshold: int = 95

    # Voice
    voice_enabled: bool = False

    # Memory
    db_path: str = "ultron_memory.db"
    max_conversation_history: int = 20

    # Safety
    log_path: str = "logs/ultron_actions.log"
    error_log_path: str = "logs/ultron_errors.log"
    blocked_commands: list = field(default_factory=lambda: DEFAULT_CONFIG["safety"]["blocked_commands"])
    restricted_paths: list = field(default_factory=lambda: DEFAULT_CONFIG["safety"]["restricted_paths"])

    # Raw YAML data for provider-specific configs
    _raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "Config":
        """Load configuration from YAML file and environment variables."""
        config_file = Path(config_path)

        # Create default config if it doesn't exist
        if not config_file.exists():
            with open(config_file, "w") as f:
                yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)

        with open(config_file, "r") as f:
            raw = yaml.safe_load(f) or {}

        # Merge with defaults
        merged = cls._deep_merge(DEFAULT_CONFIG, raw)

        # Load API keys from environment
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        tavily_key = os.getenv("TAVILY_API_KEY", "")
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")

        providers = merged.get("providers", {})
        llm_cfg = providers.get("llm", {})
        tts_cfg = providers.get("tts", {})
        stt_cfg = providers.get("stt", {})
        proactive_cfg = merged.get("proactive", {})
        safety_cfg = merged.get("safety", {})
        memory_cfg = merged.get("memory", {})
        general_cfg = merged.get("general", {})
        voice_cfg = merged.get("voice", {})

        active_llm = llm_cfg.get("active", "claude")
        claude_cfg = llm_cfg.get("claude", {})
        ollama_cfg = llm_cfg.get("ollama", {})
        local_llm_cfg = llm_cfg.get("local", {})

        return cls(
            anthropic_api_key=anthropic_key,
            tavily_api_key=tavily_key,
            elevenlabs_api_key=elevenlabs_key,
            safe_mode=general_cfg.get("safe_mode", False),
            proactive_level=general_cfg.get("proactive_level", 2),
            kill_phrase=general_cfg.get("kill_phrase", "SHUTDOWN ULTRON"),
            llm_provider=active_llm,
            tts_provider=tts_cfg.get("active", "pyttsx3"),
            stt_provider=stt_cfg.get("active", "none"),
            search_provider=providers.get("search", {}).get("active", "duckduckgo"),
            model=claude_cfg.get("model", "claude-sonnet-4-20250514"),
            max_tokens=claude_cfg.get("max_tokens", 4096),
            ollama_model=ollama_cfg.get("model", "llama3"),
            ollama_base_url=ollama_cfg.get("base_url", "http://localhost:11434"),
            local_model_path=local_llm_cfg.get("model_path", ""),
            local_context_length=local_llm_cfg.get("context_length", 8192),
            tts_rate=tts_cfg.get("pyttsx3", {}).get("rate", 150),
            tts_volume=tts_cfg.get("pyttsx3", {}).get("volume", 0.9),
            elevenlabs_voice_id=tts_cfg.get("elevenlabs", {}).get("voice_id", ""),
            whisper_model=stt_cfg.get("whisper", {}).get("model_size", "base.en"),
            monitor_interval=proactive_cfg.get("monitor_interval", 30),
            idle_threshold_min=proactive_cfg.get("idle_threshold_min", 5),
            joke_interval_min=proactive_cfg.get("joke_interval_min", 30),
            joke_interval_max=proactive_cfg.get("joke_interval_max", 90),
            cpu_threshold=proactive_cfg.get("cpu_threshold", 85),
            ram_threshold=proactive_cfg.get("ram_threshold", 90),
            disk_threshold=proactive_cfg.get("disk_threshold", 95),
            voice_enabled=voice_cfg.get("enabled", False),
            db_path=memory_cfg.get("db_path", "ultron_memory.db"),
            max_conversation_history=memory_cfg.get("max_conversation_history", 20),
            log_path=safety_cfg.get("log_path", "logs/ultron_actions.log"),
            error_log_path=safety_cfg.get("error_log_path", "logs/ultron_errors.log"),
            blocked_commands=safety_cfg.get("blocked_commands", []),
            restricted_paths=safety_cfg.get("restricted_paths", []),
            _raw=merged,
        )

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """Deep merge two dictionaries. Override values take precedence."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def get_provider_config(self, provider_type: str) -> dict:
        """Get the raw config dict for a specific provider type."""
        providers = self._raw.get("providers", {})
        provider_section = providers.get(provider_type, {})
        active = provider_section.get("active", "")
        return provider_section.get(active, {})
