from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from office_assistant.backends.schema import LLMResponse, Message, ToolDefinition


class LLMBackend(ABC):
    """Unified interface for all LLM backends."""

    @abstractmethod
    def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Synchronous text generation."""
        ...

    @abstractmethod
    def generate_stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Iterator[str]:
        """Streaming text generation, yields text chunks."""
        ...

    @abstractmethod
    def validate_connection(self) -> bool:
        """Test that the backend is reachable and configured correctly."""
        ...
