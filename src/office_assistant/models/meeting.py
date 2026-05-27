from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SegmentInfo:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    text: str
    segments: list[SegmentInfo] = field(default_factory=list)
    language: str = ""
    duration: float = 0.0


@dataclass
class TodoItem:
    task: str
    assignee: str = ""
    deadline: str = ""
    priority: str = "medium"  # high, medium, low


@dataclass
class MeetingMinutes:
    title: str = ""
    date: str = ""
    attendees: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    notes: str = ""
