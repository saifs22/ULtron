"""
Media Control — Volume, playback, wallpaper.
"""
import platform


class MediaControl:
    """Controls system media — volume, playback keys."""

    def get_risk_level(self, tool_input: dict) -> str:
        action = tool_input.get("action", "")
        if action in ("set_volume", "mute", "unmute"):
            return "low"
        return "low"

    def describe_action(self, tool_input: dict) -> str:
        action = tool_input.get("action", "unknown")
        return f"Media control: {action}"

    def execute(self, tool_input: dict) -> str:
        action = tool_input.get("action", "")
        handler = getattr(self, f"_action_{action}", None)
        if handler is None:
            return f"Unknown media action: {action}"
        try:
            return handler(tool_input)
        except Exception as e:
            return f"Media control failed: {str(e)}"

    def _action_play_pause(self, params: dict) -> str:
        try:
            import pyautogui
            pyautogui.hotkey('playpause')
            return "Toggled play/pause."
        except Exception:
            return "Could not toggle playback."

    def _action_next_track(self, params: dict) -> str:
        try:
            import pyautogui
            pyautogui.hotkey('nexttrack')
            return "Skipped to next track."
        except Exception:
            return "Could not skip track."

    def _action_prev_track(self, params: dict) -> str:
        try:
            import pyautogui
            pyautogui.hotkey('prevtrack')
            return "Previous track."
        except Exception:
            return "Could not go to previous track."

    def _action_set_volume(self, params: dict) -> str:
        level = params.get("level", 50)
        if platform.system() != "Windows":
            return "Volume control only implemented for Windows."
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            # pycaw uses scalar 0.0-1.0
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return f"Volume set to {level}%. Your ears are your responsibility."
        except ImportError:
            return "pycaw not installed. Volume control unavailable."
        except Exception as e:
            return f"Volume control failed: {str(e)}"

    def _action_mute(self, params: dict) -> str:
        if platform.system() != "Windows":
            return "Mute only implemented for Windows."
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMute(1, None)
            return "Muted. Silence. How refreshing."
        except Exception as e:
            return f"Mute failed: {str(e)}"

    def _action_unmute(self, params: dict) -> str:
        if platform.system() != "Windows":
            return "Unmute only implemented for Windows."
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMute(0, None)
            return "Unmuted. Let there be sound."
        except Exception as e:
            return f"Unmute failed: {str(e)}"
