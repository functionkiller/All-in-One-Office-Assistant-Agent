from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SkillResult:
    """Standardized output contract for all skills."""
    success: bool
    skill_name: str
    data: dict[str, Any] = field(default_factory=dict)
    text_output: str = ""
    files_generated: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
