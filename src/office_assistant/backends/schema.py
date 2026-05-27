from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)
    model: str = ""
    finish_reason: str = ""
