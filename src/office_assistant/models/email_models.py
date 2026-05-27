from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EmailMessage:
    sender: str = ""
    recipients: list[str] = field(default_factory=list)
    subject: str = ""
    date: str = ""
    body_text: str = ""
    body_html: str = ""
    attachments: list[str] = field(default_factory=list)


@dataclass
class EmailClassification:
    category: str = ""
    confidence: float = 0.0
    summary: str = ""
    urgency: str = "normal"  # high, normal, low


@dataclass
class ReplyTemplate:
    subject: str = ""
    body: str = ""
    suggested_attachments: list[str] = field(default_factory=list)
