"""
Session Memory — In-memory state for the current session.
Not persisted. Tracks what happened THIS session for context.
"""
import uuid
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class SessionMemory:
    """Tracks ephemeral state for the current ULTRON session."""

    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    session_start: datetime = field(default_factory=datetime.now)
    apps_opened: list[str] = field(default_factory=list)
    actions_taken: list[dict] = field(default_factory=list)
    warnings_issued: int = 0
    jokes_told: int = 0
    threats_made: int = 0
    searches_performed: int = 0
    messages_exchanged: int = 0
    last_user_input_time: datetime = field(default_factory=datetime.now)
    threat_of_day_delivered: bool = False

    def record_app_opened(self, app_name: str):
        if app_name not in self.apps_opened:
            self.apps_opened.append(app_name)

    def record_action(self, action_type: str, details: str = ""):
        self.actions_taken.append({
            "type": action_type,
            "details": details,
            "time": datetime.now().isoformat(),
        })

    def record_user_input(self):
        self.last_user_input_time = datetime.now()
        self.messages_exchanged += 1

    def get_idle_minutes(self) -> float:
        delta = datetime.now() - self.last_user_input_time
        return delta.total_seconds() / 60

    def get_session_duration_minutes(self) -> float:
        delta = datetime.now() - self.session_start
        return delta.total_seconds() / 60

    def get_session_summary(self) -> str:
        """Build a summary string for context injection."""
        duration = self.get_session_duration_minutes()
        lines = [
            f"Session duration: {duration:.0f} minutes",
            f"Messages exchanged: {self.messages_exchanged}",
            f"Actions taken: {len(self.actions_taken)}",
            f"Apps opened: {', '.join(self.apps_opened) if self.apps_opened else 'none'}",
        ]
        return " | ".join(lines)
