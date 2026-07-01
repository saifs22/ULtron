"""
LLM Provider implementations.
Currently supports: Claude (Anthropic API), Ollama (local).
Future: llama-cpp-python, custom local models.
"""
import json
from typing import Optional, Generator

from providers.base import LLMProvider


class ClaudeProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", max_tokens: int = 4096):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.default_max_tokens = max_tokens

    @property
    def name(self) -> str:
        return f"Claude ({self.model})"

    def chat(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: Optional[list[dict]] = None,
        max_tokens: int = 4096,
    ) -> dict:
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens or self.default_max_tokens,
            "system": system_prompt,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        response = self.client.messages.create(**kwargs)

        # Parse response
        text = None
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                text = block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        return {
            "text": text,
            "tool_calls": tool_calls if tool_calls else None,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        }

    def stream_chat(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: Optional[list[dict]] = None,
        max_tokens: int = 4096,
    ) -> Generator[str, None, None]:
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens or self.default_max_tokens,
            "system": system_prompt,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider. For future use with local models."""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    @property
    def name(self) -> str:
        return f"Ollama ({self.model})"

    def chat(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: Optional[list[dict]] = None,
        max_tokens: int = 4096,
    ) -> dict:
        import requests

        # Ollama uses a different message format — prepend system as first message
        ollama_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            ollama_messages.append({
                "role": msg["role"],
                "content": msg["content"] if isinstance(msg["content"], str)
                           else json.dumps(msg["content"]),
            })

        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }

        # Note: Ollama tool support is limited — pass tools if model supports it
        if tools:
            payload["tools"] = self._convert_tools_to_ollama(tools)

        resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        message = data.get("message", {})
        tool_calls_raw = message.get("tool_calls")
        tool_calls = None
        if tool_calls_raw:
            tool_calls = [
                {
                    "id": f"ollama_{i}",
                    "name": tc["function"]["name"],
                    "input": tc["function"]["arguments"],
                }
                for i, tc in enumerate(tool_calls_raw)
            ]

        return {
            "text": message.get("content"),
            "tool_calls": tool_calls,
            "stop_reason": "tool_use" if tool_calls else "end_turn",
            "usage": {
                "input_tokens": data.get("prompt_eval_count", 0),
                "output_tokens": data.get("eval_count", 0),
            },
        }

    def stream_chat(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: Optional[list[dict]] = None,
        max_tokens: int = 4096,
    ) -> Generator[str, None, None]:
        import requests

        ollama_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            ollama_messages.append({
                "role": msg["role"],
                "content": msg["content"] if isinstance(msg["content"], str)
                           else json.dumps(msg["content"]),
            })

        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True,
            "options": {"num_predict": max_tokens},
        }

        resp = requests.post(f"{self.base_url}/api/chat", json=payload, stream=True, timeout=120)
        resp.raise_for_status()

        for line in resp.iter_lines():
            if line:
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content

    @staticmethod
    def _convert_tools_to_ollama(tools: list[dict]) -> list[dict]:
        """Convert Anthropic tool format to Ollama function format."""
        ollama_tools = []
        for tool in tools:
            ollama_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {}),
                },
            })
        return ollama_tools


def create_llm_provider(config) -> LLMProvider:
    """Factory function — creates the appropriate LLM provider from config."""
    provider = config.llm_provider

    if provider == "claude":
        if not config.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Claude provider. Set it in .env")
        return ClaudeProvider(
            api_key=config.anthropic_api_key,
            model=config.model,
            max_tokens=config.max_tokens,
        )
    elif provider == "ollama":
        return OllamaProvider(
            model=config.ollama_model,
            base_url=config.ollama_base_url,
        )
    elif provider == "local":
        raise NotImplementedError(
            "Local LLM provider not yet implemented. "
            "Use 'ollama' provider with a local model, or set llm.active to 'claude'."
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
