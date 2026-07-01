"""
Safety — Action audit logger.
Every action Ultron takes is recorded. Accountability — his and yours.
"""
import json
import logging
from datetime import datetime
from pathlib import Path


class ActionLogger:
    """Logs all actions taken by ULTRON to a local file."""

    def __init__(self, log_path: str = "logs/ultron_actions.log"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger("ultron.actions")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.FileHandler(str(self.log_path), encoding="utf-8")
            handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            self.logger.addHandler(handler)

    def log(self, action_type: str, parameters: dict, result: str,
            confirmed: bool = True):
        """Log an action with full details."""
        entry = {
            "action": action_type,
            "params": parameters,
            "result": result[:500],  # Truncate long results
            "confirmed": confirmed,
            "timestamp": datetime.now().isoformat(),
        }
        self.logger.info(json.dumps(entry, ensure_ascii=False))

    def log_proactive(self, event_type: str, message: str):
        """Log a proactive message that was delivered."""
        entry = {
            "action": "proactive_message",
            "event_type": event_type,
            "message": message[:300],
            "timestamp": datetime.now().isoformat(),
        }
        self.logger.info(json.dumps(entry, ensure_ascii=False))

    def log_error(self, context: str, error: str):
        """Log an error."""
        entry = {
            "action": "error",
            "context": context,
            "error": str(error)[:500],
            "timestamp": datetime.now().isoformat(),
        }
        self.logger.info(json.dumps(entry, ensure_ascii=False))

    def close(self):
        """Close all handlers."""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
