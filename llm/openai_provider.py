import json
from openai import OpenAI


class OpenAIProvider:
    """Wraps the OpenAI SDK. Tool format is passed through unchanged."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self._client = OpenAI()

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> "OpenAIResponse":
        kwargs = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        response = self._client.chat.completions.create(**kwargs)
        return OpenAIResponse(response.choices[0].message)


class OpenAIResponse:
    """Normalised response wrapper for OpenAI."""

    def __init__(self, message):
        self._message = message

    @property
    def content(self) -> str | None:
        return self._message.content

    @property
    def tool_calls(self):
        return self._message.tool_calls or []

    def tool_result_message(self, tool_call_id: str, content: str) -> dict:
        return {"role": "tool", "tool_call_id": tool_call_id, "content": content}

    def assistant_message(self) -> dict:
        entry: dict = {"role": "assistant", "content": self._message.content}
        if self._message.tool_calls:
            entry["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in self._message.tool_calls
            ]
        return entry

    @staticmethod
    def parse_tool_call(tc) -> tuple[str, str, dict]:
        """Returns (tool_call_id, name, parsed_args)."""
        return tc.id, tc.function.name, json.loads(tc.function.arguments)
