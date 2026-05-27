from __future__ import annotations

import json
from collections.abc import Iterator

from openai import OpenAI

from office_assistant.backends.base import LLMBackend
from office_assistant.backends.schema import (
    LLMResponse,
    Message,
    ToolCall,
    ToolDefinition,
)
from office_assistant.config.schema import OpenAIConfig


class OpenAIBackend(LLMBackend):
    def __init__(self, config: OpenAIConfig):
        self.client = OpenAI(api_key=config.api_key, base_url=config.base_url)
        self.model = config.model
        self.default_max_tokens = config.max_tokens
        self.default_temperature = config.temperature

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
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature,
        }
        if api_tools:
            kwargs["tools"] = api_tools

        response = self.client.chat.completions.create(**kwargs)
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
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature,
        }
        if api_tools:
            kwargs["tools"] = api_tools

        stream = self.client.chat.completions.create(**kwargs, stream=True)
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def validate_connection(self) -> bool:
        try:
            self.client.chat.completions.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception:
            return False

    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        result = []
        for msg in messages:
            entry: dict = {"role": msg.role, "content": msg.content}
            if msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments, ensure_ascii=False),
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
        choice = response.choices[0]
        content = choice.message.content or ""
        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    args = {}
                tool_calls.append(
                    ToolCall(id=tc.id, name=tc.function.name, arguments=args)
                )

        usage = {}
        if response.usage:
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=usage,
            model=response.model,
            finish_reason=choice.finish_reason or "",
        )
