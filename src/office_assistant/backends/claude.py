from __future__ import annotations

import json
from collections.abc import Iterator

import anthropic

from office_assistant.backends.base import LLMBackend
from office_assistant.backends.schema import (
    LLMResponse,
    Message,
    ToolCall,
    ToolDefinition,
)
from office_assistant.config.schema import ClaudeConfig


class ClaudeBackend(LLMBackend):
    def __init__(self, config: ClaudeConfig):
        self.client = anthropic.Anthropic(api_key=config.api_key)
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
        api_messages, system_prompt = self._convert_messages(messages)
        api_tools = self._convert_tools(tools) if tools else None

        kwargs = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if api_tools:
            kwargs["tools"] = api_tools

        response = self.client.messages.create(**kwargs)
        return self._convert_response(response)

    def generate_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Iterator[str]:
        api_messages, system_prompt = self._convert_messages(messages)
        api_tools = self._convert_tools(tools) if tools else None

        kwargs = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if api_tools:
            kwargs["tools"] = api_tools

        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text

    def validate_connection(self) -> bool:
        try:
            self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception:
            return False

    def _convert_messages(self, messages: list[Message]) -> tuple[list[dict], str | None]:
        """Convert normalized messages to Anthropic API format.
        Returns (api_messages, system_prompt)."""
        system_prompt = None
        api_messages = []
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
                continue

            entry: dict = {"role": msg.role, "content": msg.content}

            if msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
                entry["role"] = "user"

            if msg.tool_calls:
                entry["content"] = [
                    {
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    }
                    for tc in msg.tool_calls
                ]

            api_messages.append(entry)
        return api_messages, system_prompt

    def _convert_tools(self, tools: list[ToolDefinition]) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
            }
            for t in tools
        ]

    def _convert_response(self, response) -> LLMResponse:
        content = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else json.loads(block.input),
                    )
                )

        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=usage,
            model=response.model,
            finish_reason=response.stop_reason,
        )
