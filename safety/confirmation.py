"""
Safety — User confirmation gates for risky actions.
Ultron threatens, but always asks before acting.
"""
from ui.terminal import TerminalUI


class ConfirmationGate:
    """Manages user confirmations for actions of varying risk levels."""

    def __init__(self):
        self.ui = TerminalUI()
        self._session_permissions: dict[str, bool] = {}

    def request(self, action_description: str, risk_level: str) -> bool:
        """Request user confirmation for an action.
        
        Risk levels:
            low     — Execute immediately, no confirmation needed
            medium  — Single confirmation
            high    — Explicit 'yes' required, action previewed
            critical — Double confirmation with countdown
        """
        if risk_level == "low":
            return True

        self.ui.display_action_preview(action_description, risk_level)

        if risk_level == "medium":
            return self.ui.display_confirmation_prompt(
                "Allow this action?"
            )

        if risk_level == "high":
            first = self.ui.display_confirmation_prompt(
                "This is a high-risk action. Are you sure?"
            )
            return first

        if risk_level == "critical":
            first = self.ui.display_confirmation_prompt(
                "CRITICAL ACTION. This could significantly affect your system. Confirm?"
            )
            if not first:
                return False
            import time
            print("  Countdown: ", end="", flush=True)
            for i in range(5, 0, -1):
                print(f"{i}... ", end="", flush=True)
                time.sleep(1)
            print()
            second = self.ui.display_confirmation_prompt(
                "Final confirmation. Proceed?"
            )
            return second

        return False

    def grant_session_permission(self, action_type: str):
        """Grant permission for an action type for the rest of this session."""
        self._session_permissions[action_type] = True

    def has_session_permission(self, action_type: str) -> bool:
        """Check if action type has session-level permission."""
        return self._session_permissions.get(action_type, False)
