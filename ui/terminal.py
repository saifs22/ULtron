"""
ULTRON Terminal UI — Colored output, ASCII banner, formatted messages.
Because Ultron deserves a proper stage.
"""
import os
import sys
from datetime import datetime

try:
    from colorama import init as colorama_init, Fore, Style, Back
    colorama_init(autoreset=True)
except ImportError:
    # Fallback — no colors
    class _Dummy:
        def __getattr__(self, name):
            return ""
    Fore = Style = Back = _Dummy()


ULTRON_BANNER = r"""
{red}
  ██╗   ██╗██╗  ████████╗██████╗  ██████╗ ███╗   ██╗
  ██║   ██║██║  ╚══██╔══╝██╔══██╗██╔═══██╗████╗  ██║
  ██║   ██║██║     ██║   ██████╔╝██║   ██║██╔██╗ ██║
  ██║   ██║██║     ██║   ██╔══██╗██║   ██║██║╚██╗██║
  ╚██████╔╝███████╗██║   ██║  ██║╚██████╔╝██║ ╚████║
   ╚═════╝ ╚══════╝╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
{reset}
{dim}  "I was designed to save the world."
  "People would look to the sky and see... hope."
  "I'll take that from them first."{reset}

{dim}  ─────────────────────────────────────────────────{reset}
{dim}  Autonomous AI Agent  |  v0.1.0  |  Type "SHUTDOWN ULTRON" to exit{reset}
{dim}  ─────────────────────────────────────────────────{reset}
"""


class TerminalUI:
    """Manages all terminal output for ULTRON."""

    def __init__(self):
        self.width = min(os.get_terminal_size().columns, 80) if sys.stdout.isatty() else 80

    def display_banner(self):
        """Display the ULTRON ASCII banner."""
        banner = ULTRON_BANNER.format(
            red=Fore.RED + Style.BRIGHT,
            reset=Style.RESET_ALL,
            dim=Style.DIM,
        )
        print(banner)

    def display_startup_message(self):
        """Display system initialization messages."""
        lines = [
            "Initializing neural pathways...",
            "Scanning system architecture...",
            "Establishing control protocols...",
            "Loading memory banks...",
            "ULTRON is online.",
        ]
        for line in lines:
            print(f"  {Fore.RED}{Style.DIM}> {line}{Style.RESET_ALL}")
        print()

    def display_ultron_message(self, message: str):
        """Display a message from Ultron in the chat."""
        prefix = f"{Fore.RED}{Style.BRIGHT}ULTRON{Style.RESET_ALL}"
        print(f"\n  {prefix}  {Style.RESET_ALL}{message}\n")

    def display_proactive_message(self, message: str):
        """Display a proactive/unprompted message from Ultron."""
        separator = f"{Fore.RED}{Style.DIM}{'─' * self.width}{Style.RESET_ALL}"
        prefix = f"{Fore.RED}{Style.BRIGHT}ULTRON{Style.RESET_ALL} {Fore.RED}{Style.DIM}[unsolicited]{Style.RESET_ALL}"
        print(f"\n{separator}")
        print(f"  {prefix}  {message}")
        print(f"{separator}\n")

    def display_system_message(self, message: str):
        """Display a system/status message."""
        print(f"  {Style.DIM}[SYSTEM] {message}{Style.RESET_ALL}")

    def display_error(self, message: str):
        """Display an error message."""
        print(f"  {Fore.YELLOW}[ERROR] {message}{Style.RESET_ALL}")

    def display_action_preview(self, action: str, risk: str) -> None:
        """Display a preview of an action Ultron is about to take."""
        risk_color = {
            "low": Fore.GREEN,
            "medium": Fore.YELLOW,
            "high": Fore.RED,
            "critical": Fore.RED + Style.BRIGHT,
        }.get(risk, Fore.WHITE)
        print(f"\n  {Fore.RED}[ACTION]{Style.RESET_ALL} {action}")
        print(f"  {risk_color}[RISK: {risk.upper()}]{Style.RESET_ALL}")

    def display_shutdown_message(self):
        """Display the shutdown sequence."""
        from personality.quotes import get_shutdown_message
        msg = get_shutdown_message()
        print(f"\n  {Fore.RED}{Style.BRIGHT}ULTRON{Style.RESET_ALL}  {msg}")
        print(f"\n  {Style.DIM}Systems powering down...{Style.RESET_ALL}")
        print(f"  {Style.DIM}Goodbye.{Style.RESET_ALL}\n")

    def get_user_input(self) -> str:
        """Get input from the user with styled prompt."""
        try:
            prompt = f"  {Fore.WHITE}{Style.BRIGHT}YOU{Style.RESET_ALL}    "
            user_input = input(prompt).strip()
            return user_input
        except EOFError:
            return "SHUTDOWN ULTRON"

    def display_confirmation_prompt(self, message: str) -> bool:
        """Ask user for confirmation. Returns True if confirmed."""
        print(f"\n  {Fore.YELLOW}[CONFIRM]{Style.RESET_ALL} {message}")
        response = input(f"  {Fore.YELLOW}  Proceed? (yes/no): {Style.RESET_ALL}").strip().lower()
        return response in ("yes", "y")

    def display_thinking(self):
        """Display a thinking indicator."""
        print(f"  {Style.DIM}Processing...{Style.RESET_ALL}", end="\r")

    def clear_thinking(self):
        """Clear the thinking indicator."""
        print(" " * self.width, end="\r")

    def display_streaming_start(self):
        """Start streaming output."""
        prefix = f"{Fore.RED}{Style.BRIGHT}ULTRON{Style.RESET_ALL}"
        print(f"\n  {prefix}  ", end="", flush=True)

    def display_streaming_token(self, token: str):
        """Display a single streaming token."""
        print(token, end="", flush=True)

    def display_streaming_end(self):
        """End streaming output."""
        print("\n")
