from __future__ import annotations

from office_assistant.backends.base import LLMBackend
from office_assistant.backends.claude import ClaudeBackend
from office_assistant.backends.ollama import OllamaBackend
from office_assistant.backends.openai_backend import OpenAIBackend
from office_assistant.config.schema import AppConfig


def create_backend(name: str, config: AppConfig) -> LLMBackend:
    """Create an LLM backend instance by name."""
    if name == "claude":
        return ClaudeBackend(config.llm.backends.claude)
    elif name == "openai":
        return OpenAIBackend(config.llm.backends.openai)
    elif name == "ollama":
        return OllamaBackend(config.llm.backends.ollama)
    raise ValueError(f"Unknown backend: {name}. Use claude, openai, or ollama.")


def create_router_backend(config: AppConfig) -> LLMBackend:
    """Create the backend for intent routing (may differ from default)."""
    router_name = config.llm.router_backend or config.llm.default_backend
    backend = create_backend(router_name, config)
    if config.llm.router_model:
        backend.model = config.llm.router_model
    return backend
