from __future__ import annotations

from collections.abc import Iterator

from ollama import Client

from office_assistant.backends.base import LLMBackend
from office_assistant.backends.schema import (
    LLMResponse,
    Message,
    ToolCall,
    ToolDefinition,
)
from office_assistant.config.schema import OllamaConfig


class OllamaBackend(LLMBackend):
    def __init__(self, config: OllamaConfig):
        self.client = Client(host=config.host)
        self.model = config.model
        self.default_max_tokens = config.max_tokens
        self.default_temperature = config.temperature
        self.keep_alive = config.keep_alive

    def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        api_messages = self._convert_messages(messages)
        api_tools = self._convert_tools(tools) if tools else None

        kwargs = {
            "model": self.model,
            "messages": api_messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens or self.default_max_tokens,
            },
        }
        if api_tools:
            kwargs["tools"] = api_tools

        response = self.client.chat(**kwargs)
        return self._convert_response(response)

    def generate_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Iterator[str]:
        api_messages = self._convert_messages(messages)
        api_tools = self._convert_tools(tools) if tools else None

        kwargs = {
            "model": self.model,
            "messages": api_messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens or self.default_max_tokens,
            },
        }
        if api_tools:
            kwargs["tools"] = api_tools

        stream = self.client.chat(**kwargs, stream=True)
        for chunk in stream:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content

    def validate_connection(self) -> bool:
        try:
            self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                options={"num_predict": 10},
            )
            return True
        except Exception:
            return False

    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        result = []
        for msg in messages:
            entry: dict = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "function": {
                            "name": tc.name,
                            "arguments": tc.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]
            result.append(entry)
        return result

    def _convert_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    def _convert_response(self, response) -> LLMResponse:
        message = response.get("message", {})
        content = message.get("content", "")
        tool_calls = []
        for tc in message.get("tool_calls", []):
            tool_calls.append(
                ToolCall(
                    id=tc.get("id", ""),
                    name=tc.get("function", {}).get("name", ""),
                    arguments=tc.get("function", {}).get("arguments", {}),
                )
            )

        usage = {}
        if "prompt_eval_count" in response:
            usage["input_tokens"] = response.get("prompt_eval_count", 0)
        if "eval_count" in response:
            usage["output_tokens"] = response.get("eval_count", 0)

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=usage,
            model=response.get("model", self.model),
            finish_reason=response.get("done_reason", ""),
        )
