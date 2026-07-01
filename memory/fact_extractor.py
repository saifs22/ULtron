"""
Fact Extractor — Pulls key facts from user messages for long-term memory.
Runs asynchronously so it doesn't slow down the conversation.
"""
import threading
import re
from typing import Optional


class FactExtractor:
    """Extracts facts from user messages and stores them in memory."""

    # Simple pattern-based extraction (no LLM call needed for common facts)
    PATTERNS = {
        "user_name": [
            r"(?:my name is|i'm|i am|call me)\s+([A-Z][a-z]+)",
            r"(?:name's)\s+([A-Z][a-z]+)",
        ],
        "preferred_editor": [
            r"(?:i use|i prefer|my editor is|i code in)\s+(vscode|vim|neovim|emacs|sublime|pycharm|intellij|notepad\+\+)",
        ],
        "preferred_language": [
            r"(?:i (?:mainly |mostly )?(?:code|program|write|develop) in)\s+(\w+)",
            r"(?:my (?:main |favorite |preferred )?(?:language|lang) is)\s+(\w+)",
        ],
        "os_preference": [
            r"(?:i use|i'm on|running)\s+(windows|linux|mac|macos|ubuntu|arch|fedora|debian)",
        ],
    }

    def __init__(self, llm_provider=None):
        self.llm_provider = llm_provider  # For advanced extraction (future)

    def extract_async(self, user_message: str, memory_db) -> None:
        """Run extraction in a background thread."""
        thread = threading.Thread(
            target=self._extract_and_store,
            args=(user_message, memory_db),
            daemon=True,
        )
        thread.start()

    def _extract_and_store(self, message: str, memory_db) -> None:
        """Extract facts from message and store in database."""
        facts = self.extract_facts(message)
        for key, value in facts.items():
            memory_db.store_fact(key, value, confidence=0.9, source="extracted")

    def extract_facts(self, message: str) -> dict[str, str]:
        """Extract facts from a user message using pattern matching."""
        facts = {}
        for fact_key, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    facts[fact_key] = match.group(1).strip()
                    break
        return facts
