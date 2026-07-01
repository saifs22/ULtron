"""
Safety — Kill switch.
Typing the kill phrase stops everything. Immediately. Gracefully.
"""
import signal
import sys


class KillSwitch:
    """Emergency shutdown handler for ULTRON."""

    def __init__(self, kill_phrase: str = "SHUTDOWN ULTRON"):
        self.kill_phrase = kill_phrase.upper()
        self._scheduler = None
        self._agent = None

    def register(self, scheduler=None, agent=None):
        """Register components that need cleanup on shutdown."""
        self._scheduler = scheduler
        self._agent = agent

        # Also register Ctrl+C handler
        signal.signal(signal.SIGINT, self._signal_handler)

    def check(self, user_input: str) -> bool:
        """Check if user input matches the kill phrase."""
        return user_input.strip().upper() == self.kill_phrase

    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C for emergency stop."""
        print("\n\n  [EMERGENCY SHUTDOWN] Ctrl+C detected. Stopping all systems...")
        self.execute_shutdown()
        sys.exit(0)

    def execute_shutdown(self):
        """Execute graceful shutdown of all components."""
        if self._scheduler:
            try:
                self._scheduler.stop()
            except Exception:
                pass
