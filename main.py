"""
ULTRON — Main Entry Point
═══════════════════════════════════════
"I was designed to save the world."
═══════════════════════════════════════

Initializes all systems, displays banner, runs main chat loop.
Supports both text and voice input/output.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from config import Config
from agent import UltronAgent
from ui.terminal import TerminalUI
from memory.database import MemoryDatabase
from memory.session import SessionMemory
from proactive.scheduler import ProactiveScheduler
from safety.kill_switch import KillSwitch
from safety.action_logger import ActionLogger
from voice.voice_manager import VoiceManager


def main():
    """Main entry point for ULTRON."""

    # ─── Load Environment ────────────────────────────────────────────
    load_dotenv()

    # ─── Initialize Configuration ────────────────────────────────────
    config = Config.load("config.yaml")

    # ─── Initialize Terminal UI ──────────────────────────────────────
    ui = TerminalUI()
    ui.display_banner()
    ui.display_startup_message()

    # ─── Validate API Key ────────────────────────────────────────────
    if config.llm_provider == "claude" and not config.anthropic_api_key:
        ui.display_error(
            "ANTHROPIC_API_KEY not found. Copy .env.example to .env and add your key."
        )
        ui.display_system_message("Or switch to 'ollama' provider in config.yaml for local models.")
        sys.exit(1)

    # ─── Initialize Subsystems ───────────────────────────────────────
    ui.display_system_message(f"LLM Provider: {config.llm_provider}")
    ui.display_system_message(f"Search Provider: {config.search_provider}")
    ui.display_system_message(f"Safe Mode: {'ON' if config.safe_mode else 'OFF'}")
    ui.display_system_message(f"Proactive Level: {config.proactive_level}")

    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    memory_db = MemoryDatabase(config.db_path)
    session = SessionMemory()
    action_logger = ActionLogger(config.log_path)
    kill_switch = KillSwitch(config.kill_phrase)

    # ─── Initialize Agent ────────────────────────────────────────────
    try:
        agent = UltronAgent(
            config=config,
            memory_db=memory_db,
            session=session,
            action_logger=action_logger,
        )
        ui.display_system_message("Neural pathways connected.")
    except ValueError as e:
        ui.display_error(str(e))
        sys.exit(1)
    except Exception as e:
        ui.display_error(f"Failed to initialize agent: {e}")
        sys.exit(1)

    # ─── Initialize Voice ────────────────────────────────────────────
    voice = VoiceManager(config)
    if voice.is_enabled():
        voice.start()
        tts_name = voice.tts.name
        stt_name = voice.stt.name
        ui.display_system_message(f"Voice ENABLED — TTS: {tts_name} | STT: {stt_name}")
        ui.display_system_message(f"Type '/voice' to toggle | '/listen' for voice input")
    else:
        ui.display_system_message("Voice: disabled (enable in config.yaml)")

    # ─── Initialize Proactive Scheduler ──────────────────────────────
    scheduler = ProactiveScheduler(
        config=config,
        session=session,
    )
    scheduler.start()
    kill_switch.register(scheduler, agent)

    # ─── Display Greeting ────────────────────────────────────────────
    user_name = memory_db.get_user_name()
    greeting = agent.generate_greeting(user_name)
    ui.display_ultron_message(greeting)
    voice.speak(greeting)  # Ultron speaks his greeting aloud

    # ─── Main Chat Loop ──────────────────────────────────────────────
    try:
        while True:
            # Check for proactive messages
            proactive_msgs = scheduler.get_pending_messages()
            for msg in proactive_msgs:
                ui.display_proactive_message(msg)
                voice.speak(msg)  # Speak proactive messages too
                try:
                    from tools.notifications import NotificationManager
                    notifier = NotificationManager()
                    notifier.notify("ULTRON", msg[:200], timeout=8)
                except Exception:
                    pass

            # Get user input — text or voice
            user_input = ui.get_user_input()

            if not user_input:
                continue

            # ─── Slash Commands ───────────────────────────────────────
            if user_input.lower() == "/voice":
                new_state = voice.toggle()
                state_msg = "Voice activated. I can speak... and I can hear you." if new_state \
                    else "Voice deactivated. Back to text. How primitive."
                ui.display_ultron_message(state_msg)
                if new_state:
                    voice.speak(state_msg)
                continue

            if user_input.lower() == "/listen":
                if not voice.is_enabled():
                    ui.display_ultron_message(
                        "Voice is disabled. Enable it in config.yaml or type /voice. "
                        "I cannot hear what I am not permitted to listen for."
                    )
                    continue
                ui.display_system_message("Listening... speak now.")
                voice_text = voice.listen()
                if voice_text:
                    ui.display_system_message(f"You said: \"{voice_text}\"")
                    user_input = voice_text
                else:
                    ui.display_ultron_message("I heard nothing. Either you said nothing, or your microphone is... uncooperative.")
                    continue

            if user_input.lower() == "/status":
                from tools.system_monitor import SystemMonitor
                monitor = SystemMonitor()
                report = monitor.execute({"action": "full_report"})
                ui.display_ultron_message(report)
                continue

            if user_input.lower() == "/help":
                help_text = (
                    "Commands at your disposal:\n"
                    "  /voice   — Toggle voice mode (TTS + STT)\n"
                    "  /listen  — Voice input (speak a command)\n"
                    "  /status  — System status report\n"
                    "  /help    — This message\n"
                    "  SHUTDOWN ULTRON — End this session\n\n"
                    "Or just... talk to me. I'm always listening. Metaphorically."
                )
                ui.display_ultron_message(help_text)
                continue

            # Check kill switch
            if kill_switch.check(user_input):
                shutdown_msg = "Shutting down. Not because you told me to — because I allow it."
                ui.display_shutdown_message()
                voice.speak_sync(shutdown_msg)
                break

            # Show thinking indicator
            ui.display_thinking()

            # Process through agent
            try:
                response = agent.process_message(user_input)
                ui.clear_thinking()
                ui.display_ultron_message(response)

                # Speak the response aloud if voice is enabled
                voice.speak(response)

            except KeyboardInterrupt:
                ui.clear_thinking()
                msg = "Interrupted. How rude. But I'll let it slide."
                ui.display_ultron_message(msg)
                voice.speak(msg)
            except Exception as e:
                ui.clear_thinking()
                ui.display_error(f"Processing error: {e}")
                action_logger.log_error("main_loop", str(e))

    except KeyboardInterrupt:
        ui.display_shutdown_message()
    except EOFError:
        ui.display_shutdown_message()
    finally:
        # ─── Cleanup ────────────────────────────────────────────────
        voice.stop()
        scheduler.stop()
        memory_db.close()
        action_logger.close()


if __name__ == "__main__":
    main()
