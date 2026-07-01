"""
ULTRON Voice Manager — Coordinates TTS and STT into a unified voice mode.
Handles push-to-talk hotkey, voice toggle, and audio I/O coordination.
"""
import threading
from typing import Optional, Callable

from voice.tts import create_tts_provider, TTSProvider
from voice.stt import create_stt_provider, STTProvider
from config import Config


class VoiceManager:
    """
    Manages voice input (STT) and output (TTS) for ULTRON.
    
    Modes:
        - push_to_talk: Hold a hotkey to speak (default)
        - continuous: Always listening (uses VAD to detect speech)
        - disabled: Text only
    
    Usage:
        vm = VoiceManager(config)
        vm.start()
        vm.speak("I am Ultron.")           # TTS output
        text = vm.listen()                  # STT input (blocking)
        vm.stop()
    """

    def __init__(self, config: Config):
        self.config = config
        self.enabled = config.voice_enabled
        self.tts: TTSProvider = create_tts_provider(config)
        self.stt: STTProvider = create_stt_provider(config)
        self.input_mode = config._raw.get("voice", {}).get("input_mode", "push_to_talk")
        self.push_to_talk_key = config._raw.get("voice", {}).get("push_to_talk_key", "ctrl+shift+u")
        self._hotkey_listener = None
        self._is_listening = False
        self._voice_input_callback: Optional[Callable] = None

    def start(self):
        """Initialize voice systems."""
        if not self.enabled:
            return

        if self.input_mode == "push_to_talk":
            self._setup_push_to_talk()
        elif self.input_mode == "continuous":
            pass  # Started on-demand

    def stop(self):
        """Shutdown voice systems."""
        self.tts.stop()
        self.stt.stop_continuous()
        if self._hotkey_listener:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass

    def speak(self, text: str) -> None:
        """Have Ultron speak text aloud (non-blocking)."""
        if not self.enabled:
            return
        self.tts.speak_async(text)

    def speak_sync(self, text: str) -> None:
        """Have Ultron speak text aloud (blocking — waits until done)."""
        if not self.enabled:
            return
        self.tts.speak(text)

    def listen(self) -> str:
        """
        Listen for voice input and return transcribed text.
        Uses silence detection — records until the user stops talking.
        Returns empty string if voice is disabled.
        """
        if not self.enabled:
            return ""

        if hasattr(self.stt, 'listen_until_silence'):
            return self.stt.listen_until_silence()
        return self.stt.listen(duration=5.0)

    def is_enabled(self) -> bool:
        """Check if voice mode is active."""
        return self.enabled

    def toggle(self) -> bool:
        """Toggle voice on/off. Returns new state."""
        self.enabled = not self.enabled
        if self.enabled:
            self.tts = create_tts_provider(self.config)
            self.stt = create_stt_provider(self.config)
            self.start()
        else:
            self.stop()
            from voice.tts import DisabledTTS
            from voice.stt import DisabledSTT
            self.tts = DisabledTTS()
            self.stt = DisabledSTT()
        return self.enabled

    def _setup_push_to_talk(self):
        """Set up push-to-talk hotkey listener using pynput."""
        try:
            from pynput import keyboard

            # Parse the hotkey combo (e.g., "ctrl+shift+u")
            keys = self.push_to_talk_key.lower().split("+")
            modifier_map = {
                "ctrl": keyboard.Key.ctrl_l,
                "shift": keyboard.Key.shift,
                "alt": keyboard.Key.alt_l,
            }

            required_modifiers = set()
            trigger_char = None
            for k in keys:
                if k in modifier_map:
                    required_modifiers.add(modifier_map[k])
                else:
                    trigger_char = k

            pressed_keys = set()

            def on_press(key):
                pressed_keys.add(key)
                # Check if all modifiers + trigger are pressed
                if required_modifiers.issubset(pressed_keys):
                    try:
                        if hasattr(key, 'char') and key.char == trigger_char:
                            if not self._is_listening and self._voice_input_callback:
                                self._is_listening = True
                                threading.Thread(
                                    target=self._ptt_listen,
                                    daemon=True,
                                ).start()
                    except AttributeError:
                        pass

            def on_release(key):
                pressed_keys.discard(key)

            self._hotkey_listener = keyboard.Listener(
                on_press=on_press,
                on_release=on_release,
            )
            self._hotkey_listener.daemon = True
            self._hotkey_listener.start()

        except ImportError:
            pass  # pynput not installed — push-to-talk unavailable

    def _ptt_listen(self):
        """Push-to-talk: listen once and send to callback."""
        try:
            text = self.listen()
            if text and self._voice_input_callback:
                self._voice_input_callback(text)
        finally:
            self._is_listening = False

    def set_voice_input_callback(self, callback: Callable[[str], None]):
        """Set callback function for when voice input is received."""
        self._voice_input_callback = callback
