from __future__ import annotations

from abc import ABC, abstractmethod

from office_assistant.backends.base import LLMBackend
from office_assistant.backends.schema import ToolDefinition
from office_assistant.core.skill_result import SkillResult


class BaseSkill(ABC):
    """Abstract base class for all office assistant skills."""

    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    keywords: list[str] = []
    required_inputs: dict[str, dict[str, str]] = {}

    def get_tools(self) -> list[ToolDefinition]:
        """Optional tools for function calling. Override in subclass if needed."""
        return []

    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters. Raises ValueError on failure."""
        for key, spec in self.required_inputs.items():
            if key not in kwargs:
                raise ValueError(f"Missing required input: {key} ({spec.get('help', '')})")
        return True

    @abstractmethod
    def execute(self, backend: LLMBackend, **kwargs) -> SkillResult:
        """Execute the skill with the given LLM backend."""
        ...
