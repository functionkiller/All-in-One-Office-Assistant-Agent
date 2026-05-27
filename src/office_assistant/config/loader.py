from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

from office_assistant.config.schema import AppConfig


def _substitute_env(value: str) -> str:
    """Replace ${VAR_NAME} with environment variable values."""
    pattern = re.compile(r"\$\{(\w+)\}")

    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    return pattern.sub(replacer, value)


def _walk_dict(data: dict) -> dict:
    """Recursively substitute env vars in all string values."""
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = _substitute_env(value)
        elif isinstance(value, dict):
            result[key] = _walk_dict(value)
        elif isinstance(value, list):
            result[key] = [
                _substitute_env(v) if isinstance(v, str) else v for v in value
            ]
        else:
            result[key] = value
    return result


def _apply_env_overrides(config: dict) -> dict:
    """Apply OA_* environment variable overrides to config."""
    env_map = {
        "OA_LLM_DEFAULT_BACKEND": ("llm", "default_backend"),
        "OA_LLM_ROUTER_BACKEND": ("llm", "router_backend"),
        "OA_LLM_ROUTER_MODEL": ("llm", "router_model"),
        "OA_CLAUDE_MODEL": ("llm", "backends", "claude", "model"),
        "OA_OPENAI_MODEL": ("llm", "backends", "openai", "model"),
        "OA_OLLAMA_MODEL": ("llm", "backends", "ollama", "model"),
        "OA_OLLAMA_HOST": ("llm", "backends", "ollama", "host"),
        "OA_WHISPER_MODEL_SIZE": ("whisper", "model_size"),
        "OA_WHISPER_DEVICE": ("whisper", "device"),
        "OA_OUTPUT_DIR": ("output", "output_dir"),
    }

    for env_var, path in env_map.items():
        value = os.environ.get(env_var)
        if value is not None:
            target = config
            for key in path[:-1]:
                target = target.setdefault(key, {})
            target[path[-1]] = value

    return config


def _search_config_paths() -> list[Path]:
    """Return ordered list of config file search paths."""
    paths = [
        Path("config.yaml"),
        Path.home() / ".office-assistant" / "config.yaml",
    ]
    if os.name == "nt":
        paths.append(
            Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData"))
            / "office-assistant"
            / "config.yaml"
        )
    else:
        paths.append(Path("/etc/office-assistant/config.yaml"))
    return paths


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load and validate application configuration.

    Priority:
    1. Explicit config_path argument
    2. ./config.yaml
    3. ~/.office-assistant/config.yaml
    4. System-wide path
    5. Environment variable overrides (OA_*)
    """
    load_dotenv()

    if config_path is None:
        for path in _search_config_paths():
            if path.exists():
                config_path = path
                break

    if config_path is None or not config_path.exists():
        raise FileNotFoundError(
            "No config file found. Create config.yaml or place one at "
            f"{Path.home() / '.office-assistant' / 'config.yaml'}"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    raw = _walk_dict(raw)
    raw = _apply_env_overrides(raw)

    return AppConfig(**raw)
