from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from office_assistant.backends.schema import LLMResponse
from office_assistant.config.schema import (
    AppConfig,
    ClaudeConfig,
    LLMBackendsConfig,
    LLMConfig,
    OllamaConfig,
    OpenAIConfig,
    OutputConfig,
    SkillsConfig,
    WhisperConfig,
)


@pytest.fixture
def sample_config() -> AppConfig:
    return AppConfig(
        llm=LLMConfig(
            default_backend="claude",
            backends=LLMBackendsConfig(
                claude=ClaudeConfig(api_key="test-key", model="claude-test"),
                openai=OpenAIConfig(api_key="test-key", model="gpt-test"),
                ollama=OllamaConfig(host="http://localhost:11434", model="test-model"),
            ),
        ),
        whisper=WhisperConfig(model_size="tiny", device="cpu"),
        skills=SkillsConfig(),
        output=OutputConfig(output_dir="./test_output"),
    )


@pytest.fixture
def mock_llm_response() -> LLMResponse:
    return LLMResponse(
        content="Test response",
        model="test-model",
        finish_reason="stop",
    )


@pytest.fixture
def mock_backend(mock_llm_response: LLMResponse) -> MagicMock:
    backend = MagicMock()
    backend.generate.return_value = mock_llm_response
    backend.model = "test-model"
    return backend


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [28, 35, 42],
        "department": ["Engineering", "Product", "Design"],
    })
    path = tmp_path / "test_data.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def sample_eml(tmp_path: Path) -> Path:
    eml_content = """From: sender@example.com
To: recipient@example.com
Subject: Meeting Tomorrow
Date: Mon, 27 May 2025 10:00:00 +0800
Content-Type: text/plain; charset=utf-8

Hi,

Can we meet tomorrow at 2pm to discuss the Q2 roadmap?

Thanks,
Alice
"""
    path = tmp_path / "test_email.eml"
    path.write_text(eml_content, encoding="utf-8")
    return path
