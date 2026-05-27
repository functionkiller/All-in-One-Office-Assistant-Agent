from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReportSection:
    title: str
    content: str


@dataclass
class Report:
    title: str = ""
    sections: list[ReportSection] = field(default_factory=list)
    raw_text: str = ""
