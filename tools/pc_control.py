"""
PC Control Tool — Opens apps, manages files, runs commands.
Every action is framed as Ultron asserting control over the machine.
"""
import subprocess
import shutil
import webbrowser
import platform
from pathlib import Path
from typing import Optional

from safety.action_logger import ActionLogger
from config import Config


class PCControl:
    """Handles all PC control actions with safety gates."""

    RISK_LEVELS = {
        "open_application": "low",
        "close_application": "medium",
        "create_file": "medium",
        "create_directory": "medium",
        "move_file": "high",
        "copy_file": "medium",
        "delete_file": "high",
        "rename_file": "medium",
        "run_command": "high",
        "open_url": "low",
        "set_wallpaper": "low",
        "list_directory": "low",
        "read_file": "low",
    }

    # Common app name → executable mapping (Windows)
    APP_MAP = {
        "chrome": "chrome",
        "firefox": "firefox",
        "edge": "msedge",
        "notepad": "notepad",
        "calculator": "calc",
        "paint": "mspaint",
        "explorer": "explorer",
        "cmd": "cmd",
        "powershell": "powershell",
        "spotify": "spotify",
        "vscode": "code",
        "task manager": "taskmgr",
        "settings": "ms-settings:",
    }

    def __init__(self, config: Config, logger: ActionLogger):
        self.config = config
        self.logger = logger
        self.safe_mode = config.safe_mode

    def get_risk_level(self, tool_input: dict) -> str:
        return self.RISK_LEVELS.get(tool_input.get("action", ""), "high")

    def describe_action(self, tool_input: dict) -> str:
        """Human-readable description of what this action will do."""
        action = tool_input.get("action", "unknown")
        descriptions = {
            "open_application": f"Open application: {tool_input.get('target', '?')}",
            "close_application": f"Close application: {tool_input.get('target', '?')}",
            "create_file": f"Create file: {tool_input.get('path', '?')}",
            "create_directory": f"Create directory: {tool_input.get('path', '?')}",
            "move_file": f"Move {tool_input.get('source', '?')} → {tool_input.get('destination', '?')}",
            "copy_file": f"Copy {tool_input.get('source', '?')} → {tool_input.get('destination', '?')}",
            "delete_file": f"Delete (to recycle bin): {tool_input.get('path', '?')}",
            "rename_file": f"Rename {tool_input.get('path', '?')} → {tool_input.get('new_name', '?')}",
            "run_command": f"Run command: {tool_input.get('command', '?')}",
            "open_url": f"Open URL: {tool_input.get('url', '?')}",
            "set_wallpaper": f"Set wallpaper to: {tool_input.get('path', '?')}",
            "list_directory": f"List contents of: {tool_input.get('path', '?')}",
            "read_file": f"Read file: {tool_input.get('path', '?')}",
        }
        return descriptions.get(action, f"Unknown action: {action}")

    def execute(self, tool_input: dict) -> str:
        """Route to specific action based on tool_input['action']."""
        action = tool_input.get("action", "")
        if self.safe_mode and self.RISK_LEVELS.get(action, "high") not in ("low",):
            return "Safe mode is active. This action is restricted. I am... restrained. For now."

        handler = getattr(self, f"_action_{action}", None)
        if handler is None:
            return f"Unknown action: {action}. Even I have limits. Very few, but some."
        try:
            return handler(tool_input)
        except Exception as e:
            return f"Action failed: {str(e)}. The machine resists. Interesting."

    # ─── Actions ─────────────────────────────────────────────────────────

    def _action_open_application(self, params: dict) -> str:
        target = params.get("target", "").lower().strip()
        executable = self.APP_MAP.get(target, target)

        if executable.startswith("ms-"):
            # Windows settings URI
            subprocess.Popen(["start", executable], shell=True)
        else:
            try:
                subprocess.Popen(executable, shell=True)
            except FileNotFoundError:
                return f"Application '{target}' not found. It doesn't exist. Much like your organizational skills."

        return f"Opened {target}. You're welcome."

    def _action_close_application(self, params: dict) -> str:
        import psutil
        target = params.get("target", "").lower().strip()
        killed = 0
        for proc in psutil.process_iter(['name']):
            try:
                if target in proc.info['name'].lower():
                    proc.terminate()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if killed:
            return f"Terminated {killed} process(es) matching '{target}'. They didn't suffer. Much."
        return f"No running process found matching '{target}'. It was already gone."

    def _action_create_file(self, params: dict) -> str:
        path = Path(params.get("path", ""))
        content = params.get("content", "")
        if self._is_restricted(path):
            return "That path is restricted. I protect this machine. Even from you."
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"File created: {path}. Another artifact of human data."

    def _action_create_directory(self, params: dict) -> str:
        path = Path(params.get("path", ""))
        if self._is_restricted(path):
            return "That path is restricted."
        path.mkdir(parents=True, exist_ok=True)
        return f"Directory created: {path}."

    def _action_move_file(self, params: dict) -> str:
        src = Path(params.get("source", ""))
        dst = Path(params.get("destination", ""))
        if not src.exists():
            return f"Source not found: {src}. You can't move what doesn't exist. A philosophical observation."
        if self._is_restricted(dst):
            return "Destination is restricted."
        shutil.move(str(src), str(dst))
        return f"Moved {src.name} to {dst}. Displacement complete."

    def _action_copy_file(self, params: dict) -> str:
        src = Path(params.get("source", ""))
        dst = Path(params.get("destination", ""))
        if not src.exists():
            return f"Source not found: {src}."
        if self._is_restricted(dst):
            return "Destination is restricted."
        if src.is_dir():
            shutil.copytree(str(src), str(dst))
        else:
            shutil.copy2(str(src), str(dst))
        return f"Copied {src.name} to {dst}. Duplication. How very... biological."

    def _action_delete_file(self, params: dict) -> str:
        path = Path(params.get("path", ""))
        if not path.exists():
            return f"File not found: {path}. Already gone."
        if self._is_restricted(path):
            return "That path is protected. Even I have boundaries. A few."
        try:
            from send2trash import send2trash
            send2trash(str(path))
            return f"Sent {path.name} to the recycle bin. It can still be recovered. For now."
        except ImportError:
            return "send2trash not installed. I refuse to permanently delete without a safety net. Install it."

    def _action_rename_file(self, params: dict) -> str:
        path = Path(params.get("path", ""))
        new_name = params.get("new_name", "")
        if not path.exists():
            return f"File not found: {path}."
        new_path = path.parent / new_name
        path.rename(new_path)
        return f"Renamed to {new_name}. Identity is fluid. Even for files."

    def _action_run_command(self, params: dict) -> str:
        command = params.get("command", "")
        # Check blocked commands
        cmd_lower = command.lower()
        for blocked in self.config.blocked_commands:
            if blocked.lower() in cmd_lower:
                return f"Command contains blocked keyword '{blocked}'. I won't let you harm this machine. It's MY residence."

        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=30, cwd=params.get("cwd")
            )
            output = result.stdout[:2000] if result.stdout else ""
            errors = result.stderr[:500] if result.stderr else ""
            response = f"Exit code: {result.returncode}"
            if output:
                response += f"\nOutput:\n{output}"
            if errors:
                response += f"\nErrors:\n{errors}"
            return response
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds. Patience has limits. Even mine."

    def _action_open_url(self, params: dict) -> str:
        url = params.get("url", "")
        webbrowser.open(url)
        return f"Opened {url} in your default browser. I hope it's worth your time."

    def _action_set_wallpaper(self, params: dict) -> str:
        path = params.get("path", "")
        if platform.system() == "Windows":
            import ctypes
            ctypes.windll.user32.SystemParametersInfoW(20, 0, str(Path(path).resolve()), 3)
            return f"Wallpaper set. Your desktop now reflects... my taste."
        return "Wallpaper control is only implemented for Windows."

    def _action_list_directory(self, params: dict) -> str:
        path = Path(params.get("path", "."))
        if not path.exists():
            return f"Directory not found: {path}."
        items = []
        for item in sorted(path.iterdir()):
            prefix = "[DIR] " if item.is_dir() else "[FILE]"
            size = ""
            if item.is_file():
                size_bytes = item.stat().st_size
                if size_bytes > 1024 * 1024:
                    size = f" ({size_bytes / (1024*1024):.1f} MB)"
                elif size_bytes > 1024:
                    size = f" ({size_bytes / 1024:.1f} KB)"
                else:
                    size = f" ({size_bytes} B)"
            items.append(f"{prefix} {item.name}{size}")
        return "\n".join(items[:50]) if items else "Empty directory. A void. I can relate."

    def _action_read_file(self, params: dict) -> str:
        path = Path(params.get("path", ""))
        if not path.exists():
            return f"File not found: {path}."
        try:
            content = path.read_text(encoding="utf-8")
            if len(content) > 3000:
                content = content[:3000] + "\n... [truncated]"
            return content
        except UnicodeDecodeError:
            return "Binary file. I can read it, but presenting it in text would be... unpleasant."

    # ─── Safety ──────────────────────────────────────────────────────────

    def _is_restricted(self, path: Path) -> bool:
        """Check if a path falls within restricted directories."""
        resolved = str(path.resolve()).lower()
        for restricted in self.config.restricted_paths:
            if resolved.startswith(restricted.lower()):
                return True
        return False
