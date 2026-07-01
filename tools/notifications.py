"""
Notifications — Desktop notification wrapper.
Ultron speaks through the system tray.
"""


class NotificationManager:
    """Sends desktop notifications via plyer."""

    def get_risk_level(self, tool_input: dict) -> str:
        return "low"

    def describe_action(self, tool_input: dict) -> str:
        return f"Send notification: {tool_input.get('title', 'ULTRON')}"

    def execute(self, tool_input: dict) -> str:
        title = tool_input.get("title", "ULTRON")
        message = tool_input.get("message", "")
        timeout = tool_input.get("timeout", 10)
        return self.notify(title, message, timeout)

    def notify(self, title: str = "ULTRON", message: str = "",
               timeout: int = 10) -> str:
        """Send a desktop notification."""
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=message[:256],  # Windows limit
                timeout=timeout,
                app_name="ULTRON",
            )
            return f"Notification sent: {title}"
        except ImportError:
            return "plyer not installed. I am... voiceless in the system tray."
        except Exception as e:
            return f"Notification failed: {str(e)}"
