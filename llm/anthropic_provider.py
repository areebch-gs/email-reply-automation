import json
import os
import anthropic


class AnthropicProvider:
    """
    Wraps the Anthropic SDK with the same interface as OpenAIProvider.

    Handles two key differences internally:
      1. Tool schema: OpenAI uses "parameters", Claude uses "input_schema"
      2. Message format: system messages are a separate arg, tool results
         are user-turn content blocks rather than a "tool" role
    """

    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.model = model
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
        self._client = anthropic.Anthropic(api_key=api_key)

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> "AnthropicResponse":
        system, conversation = self._split_system(messages)
        claude_messages = self._convert_messages(conversation)
        claude_tools = self._convert_tools(tools) if tools else []

        kwargs = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": claude_messages,
        }
        if system:
            kwargs["system"] = system
        if claude_tools:
            kwargs["tools"] = claude_tools

        response = self._client.messages.create(**kwargs)
        return AnthropicResponse(response)

    # ── Internal translation helpers ──────────────────────────────────────────

    @staticmethod
    def _split_system(messages: list[dict]) -> tuple[str, list[dict]]:
        """Extract the system message (Claude takes it as a separate param)."""
        system = ""
        rest = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                rest.append(m)
        return system, rest

    @staticmethod
    def _convert_messages(messages: list[dict]) -> list[dict]:
        """Convert normalised messages to Claude's wire format."""
        converted = []
        for m in messages:
            role = m["role"]

            if role == "assistant":
                content = []
                if m.get("content"):
                    content.append({"type": "text", "text": m["content"]})
                for tc in m.get("tool_calls", []):
                    content.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "input": json.loads(tc["function"]["arguments"]),
                    })
                converted.append({"role": "assistant", "content": content})

            elif role == "tool":
                # Claude expects tool results as a user turn
                converted.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": m["tool_call_id"],
                        "content": m["content"],
                    }],
                })

            else:
                converted.append({"role": role, "content": m["content"]})

        return converted

    @staticmethod
    def _convert_tools(tools: list[dict]) -> list[dict]:
        """Convert OpenAI tool schema to Claude tool schema."""
        claude_tools = []
        for t in tools:
            fn = t["function"]
            claude_tools.append({
                "name": fn["name"],
                "description": fn.get("description", ""),
                "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
            })
        return claude_tools


class AnthropicResponse:
    """Normalised response wrapper for Claude — matches OpenAIResponse interface."""

    def __init__(self, response):
        self._response = response
        self._tool_blocks = [b for b in response.content if b.type == "tool_use"]
        self._text_blocks = [b for b in response.content if b.type == "text"]

    @property
    def content(self) -> str | None:
        return self._text_blocks[0].text if self._text_blocks else None

    @property
    def tool_calls(self):
        return self._tool_blocks

    def tool_result_message(self, tool_call_id: str, content: str) -> dict:
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content,
        }

    def assistant_message(self) -> dict:
        entry: dict = {"role": "assistant", "content": self.content}
        if self._tool_blocks:
            entry["tool_calls"] = [
                {
                    "id": b.id,
                    "type": "function",
                    "function": {"name": b.name, "arguments": json.dumps(b.input)},
                }
                for b in self._tool_blocks
            ]
        return entry

    @staticmethod
    def parse_tool_call(tc) -> tuple[str, str, dict]:
        """Returns (tool_call_id, name, parsed_args)."""
        return tc.id, tc.name, tc.input
