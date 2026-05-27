from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DataSummary:
    row_count: int
    column_count: int
    columns: list[str]
    dtypes: dict[str, str]
    missing_counts: dict[str, int]
    numeric_stats: dict[str, dict[str, float]] = field(default_factory=dict)
    analysis_text: str = ""
