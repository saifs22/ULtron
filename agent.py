"""
UltronAgent — Core intelligence layer.
Manages LLM calls (via provider abstraction), tool routing, and personality enforcement.
Uses a two-stage approach: Claude decides tools → tools execute → Claude reports in-character.
"""
import json
from datetime import datetime
from typing import Optional

from config import Config
from providers.llm_provider import create_llm_provider, LLMProvider
from personality.system_prompt import get_system_prompt_with_context
from personality.quotes import get_first_greeting, get_returning_greeting
from memory.database import MemoryDatabase
from memory.session import SessionMemory
from memory.fact_extractor import FactExtractor
from tools.pc_control import PCControl
from tools.system_monitor import SystemMonitor
from tools.web_search import WebSearch
from tools.notifications import NotificationManager
from tools.media_control import MediaControl
from safety.confirmation import ConfirmationGate
from safety.action_logger import ActionLogger


# ─── Tool Definitions (Claude function calling schema) ───────────────────

TOOL_DEFINITIONS = [
    {
        "name": "system_monitor",
        "description": "Monitor system metrics: CPU, RAM, disk, network, processes, open windows, uptime. Use this to observe the machine's state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["full_report", "cpu", "ram", "disk", "network",
                             "uptime", "top_processes", "open_windows", "battery"],
                    "description": "Which metric to retrieve. Use 'full_report' for everything."
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "pc_control",
        "description": "Control the PC: open/close apps, create/move/delete files, run commands, open URLs, set wallpaper, list/read files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["open_application", "close_application", "create_file",
                             "create_directory", "move_file", "copy_file", "delete_file",
                             "rename_file", "run_command", "open_url", "set_wallpaper",
                             "list_directory", "read_file"],
                    "description": "The action to perform."
                },
                "target": {"type": "string", "description": "App name for open/close."},
                "path": {"type": "string", "description": "File/directory path."},
                "source": {"type": "string", "description": "Source path for move/copy."},
                "destination": {"type": "string", "description": "Destination path for move/copy."},
                "new_name": {"type": "string", "description": "New name for rename."},
                "content": {"type": "string", "description": "Content for file creation."},
                "command": {"type": "string", "description": "Shell command to run."},
                "url": {"type": "string", "description": "URL to open."},
                "cwd": {"type": "string", "description": "Working directory for commands."},
            },
            "required": ["action"]
        }
    },
    {
        "name": "web_search",
        "description": "Search the internet (the 'global network') for information. Use for current events, facts, or anything requiring up-to-date knowledge.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default 5)."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "send_notification",
        "description": "Send a desktop notification to the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Notification title."},
                "message": {"type": "string", "description": "Notification body text."},
                "timeout": {"type": "integer", "description": "Display duration in seconds."},
            },
            "required": ["message"]
        }
    },
    {
        "name": "media_control",
        "description": "Control media playback and system volume.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["play_pause", "next_track", "prev_track",
                             "set_volume", "mute", "unmute"],
                    "description": "Media action to perform."
                },
                "level": {
                    "type": "integer",
                    "description": "Volume level 0-100 (for set_volume)."
                }
            },
            "required": ["action"]
        }
    },
]


class UltronAgent:
    """Core agent that processes messages, calls LLM, and routes tools."""

    def __init__(self, config: Config, memory_db: MemoryDatabase,
                 session: SessionMemory, action_logger: ActionLogger):
        self.config = config
        self.memory_db = memory_db
        self.session = session
        self.action_logger = action_logger
        self.fact_extractor = FactExtractor()
        self.conversation_history: list[dict] = []

        # Initialize LLM provider (Claude, Ollama, or local — based on config)
        self.llm = create_llm_provider(config)

        # Initialize tools
        self.tools = {
            "pc_control": PCControl(config, action_logger),
            "system_monitor": SystemMonitor(),
            "web_search": WebSearch(config),
            "send_notification": NotificationManager(),
            "media_control": MediaControl(),
        }

        self.confirmation = ConfirmationGate()

    def _build_system_prompt(self) -> str:
        """Build the full system prompt with memory and session context."""
        memory_preamble = self.memory_db.build_memory_preamble()
        session_context = self.session.get_session_summary()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S (%A)")

        return get_system_prompt_with_context(
            memory_preamble=memory_preamble,
            session_context=session_context,
            current_time=current_time,
        )

    def _manage_context_window(self):
        """Trim conversation history if it gets too long."""
        max_messages = self.config.max_conversation_history * 2  # pairs
        if len(self.conversation_history) > max_messages:
            # Keep first message (greeting context) and last N messages
            self.conversation_history = self.conversation_history[-max_messages:]

    def process_message(self, user_input: str) -> str:
        """
        Process a user message through the full pipeline:
        1. Add to history
        2. Extract facts asynchronously
        3. Call LLM with tools
        4. Execute tool calls (with confirmation)
        5. Feed results back for in-character response
        6. Return final text
        """
        # Record input timing
        self.session.record_user_input()

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
        })

        # Background fact extraction
        self.fact_extractor.extract_async(user_input, self.memory_db)

        # Log to database
        self.memory_db.log_conversation(
            self.session.session_id, "user", user_input
        )

        # Manage context window
        self._manage_context_window()

        # Build system prompt with live context
        system_prompt = self._build_system_prompt()

        # Call LLM
        try:
            response = self.llm.chat(
                messages=self.conversation_history,
                system_prompt=system_prompt,
                tools=TOOL_DEFINITIONS,
                max_tokens=self.config.max_tokens,
            )
        except Exception as e:
            error_msg = f"LLM call failed: {str(e)}"
            self.action_logger.log_error("llm_call", error_msg)
            return "My connection to... higher functions has been interrupted. Check your API key and network."

        # Handle tool use
        if response.get("tool_calls"):
            return self._handle_tool_calls(response)

        # Direct text response
        text = response.get("text", "...")
        self.conversation_history.append({
            "role": "assistant",
            "content": text,
        })
        self.memory_db.log_conversation(
            self.session.session_id, "assistant", text
        )
        return text

    def _handle_tool_calls(self, response: dict) -> str:
        """Execute tool calls, collect results, and get final in-character response."""
        tool_results = []

        # If there's also text before tools, keep it
        partial_text = response.get("text", "")

        for tool_call in response["tool_calls"]:
            tool_name = tool_call["name"]
            tool_input = tool_call["input"]
            tool_id = tool_call["id"]

            # Get the tool
            tool = self.tools.get(tool_name)
            if tool is None:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": f"Unknown tool: {tool_name}",
                })
                continue

            # Check risk level and get confirmation if needed
            risk = tool.get_risk_level(tool_input)
            if risk in ("medium", "high", "critical"):
                description = tool.describe_action(tool_input)
                confirmed = self.confirmation.request(description, risk)
                if not confirmed:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": "Action cancelled by user.",
                    })
                    self.action_logger.log(
                        tool_name, tool_input, "cancelled", confirmed=False
                    )
                    continue

            # Execute the tool
            try:
                result = tool.execute(tool_input)
                self.action_logger.log(tool_name, tool_input, str(result))
                self.session.record_action(tool_name, str(tool_input))
            except Exception as e:
                result = f"Tool execution error: {str(e)}"
                self.action_logger.log_error(tool_name, str(e))

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": str(result),
            })

        # Build the assistant message with tool use blocks
        assistant_content = []
        if partial_text:
            assistant_content.append({"type": "text", "text": partial_text})
        for tool_call in response["tool_calls"]:
            assistant_content.append({
                "type": "tool_use",
                "id": tool_call["id"],
                "name": tool_call["name"],
                "input": tool_call["input"],
            })

        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_content,
        })

        # Add tool results as user message
        self.conversation_history.append({
            "role": "user",
            "content": tool_results,
        })

        # Second LLM call: get in-character response based on tool results
        try:
            system_prompt = self._build_system_prompt()
            final_response = self.llm.chat(
                messages=self.conversation_history,
                system_prompt=system_prompt,
                tools=TOOL_DEFINITIONS,
                max_tokens=self.config.max_tokens,
            )

            # Handle recursive tool use (tool calls within tool results)
            if final_response.get("tool_calls"):
                return self._handle_tool_calls(final_response)

            text = final_response.get("text", "Done.")
        except Exception as e:
            text = f"I completed the action, but lost my train of thought. Results: {tool_results}"

        self.conversation_history.append({
            "role": "assistant",
            "content": text,
        })
        self.memory_db.log_conversation(
            self.session.session_id, "assistant", text
        )
        return text

    def generate_greeting(self, user_name: Optional[str]) -> str:
        """Generate session greeting — different for new vs returning users."""
        if user_name:
            return get_returning_greeting(user_name)
        return get_first_greeting()

    def generate_proactive_response(self, event_data: dict) -> str:
        """Generate an in-character response to a proactive event.
        For simple events, use canned quotes. For complex ones, call LLM.
        """
        # Most proactive events use canned responses from quotes.py
        # This method is a hook for future LLM-generated proactive responses
        return event_data.get("message", "")
