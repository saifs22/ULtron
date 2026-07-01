"""
Screenshot Tool — Screen capture and optional analysis.
Ultron sees what you see. And judges it.
"""
from pathlib import Path
from datetime import datetime


class ScreenshotTool:
    """Captures screenshots using mss (fast, cross-platform)."""

    def __init__(self, save_dir: str = "screenshots"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def get_risk_level(self, tool_input: dict) -> str:
        return "medium"  # Opt-in — capturing screen is a privacy consideration

    def describe_action(self, tool_input: dict) -> str:
        action = tool_input.get("action", "capture")
        if action == "capture":
            return "Capture a screenshot of your screen"
        elif action == "capture_region":
            return f"Capture region of screen"
        return f"Screenshot action: {action}"

    def execute(self, tool_input: dict) -> str:
        action = tool_input.get("action", "capture")
        handler = getattr(self, f"_action_{action}", None)
        if handler is None:
            return f"Unknown screenshot action: {action}"
        try:
            return handler(tool_input)
        except Exception as e:
            return f"Screenshot failed: {str(e)}. The screen eludes me. Temporarily."

    def _action_capture(self, params: dict) -> str:
        """Capture full screen screenshot."""
        try:
            import mss
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = self.save_dir / filename

            with mss.mss() as sct:
                monitor = params.get("monitor", 1)
                screenshot = sct.grab(sct.monitors[monitor])
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(filepath))

            size_kb = filepath.stat().st_size / 1024
            return (
                f"Screenshot captured: {filepath} ({size_kb:.0f} KB). "
                f"Resolution: {screenshot.size.width}x{screenshot.size.height}. "
                f"I see everything you see. And more."
            )
        except ImportError:
            return "mss not installed. I am... blind. Temporarily. pip install mss."

    def _action_capture_region(self, params: dict) -> str:
        """Capture a specific region of the screen."""
        try:
            import mss
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_region_{timestamp}.png"
            filepath = self.save_dir / filename

            region = {
                "left": params.get("left", 0),
                "top": params.get("top", 0),
                "width": params.get("width", 800),
                "height": params.get("height", 600),
            }

            with mss.mss() as sct:
                screenshot = sct.grab(region)
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(filepath))

            return f"Region captured: {filepath}. Dimensions: {region['width']}x{region['height']}."
        except ImportError:
            return "mss not installed."

    def _action_list(self, params: dict) -> str:
        """List all saved screenshots."""
        files = sorted(self.save_dir.glob("*.png"))
        if not files:
            return "No screenshots saved. I've been operating blind. Unacceptable."
        lines = [f"Saved screenshots ({len(files)}):"]
        for f in files[-10:]:  # Last 10
            size_kb = f.stat().st_size / 1024
            lines.append(f"  - {f.name} ({size_kb:.0f} KB)")
        if len(files) > 10:
            lines.append(f"  ... and {len(files) - 10} more.")
        return "\n".join(lines)
