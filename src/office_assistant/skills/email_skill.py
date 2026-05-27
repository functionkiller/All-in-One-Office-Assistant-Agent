from __future__ import annotations

from pathlib import Path

from office_assistant.backends.base import LLMBackend
from office_assistant.backends.schema import Message
from office_assistant.core.skill_base import BaseSkill
from office_assistant.core.skill_registry import register_skill
from office_assistant.core.skill_result import SkillResult
from office_assistant.models.email_models import (
    EmailClassification,
    EmailMessage,
    ReplyTemplate,
)

CLASSIFY_SYSTEM_PROMPT = """你是一个邮件智能分类助手。分析邮件内容并将其分类。

分类类别: {categories}

输出 JSON 格式:
```json
{{"category": "类别名", "confidence": 0.95, "summary": "一句话摘要", "urgency": "high/normal/low"}}
```

只输出 JSON，不要其他文本。"""

REPLY_SYSTEM_PROMPT = """你是一个专业的邮件回复助手。根据原始邮件内容，生成回复模板。

回复应:
1. 礼貌得体、简洁清晰
2. 直接回应该邮件的核心问题/请求
3. 用{tone}的语气

输出格式:
```
主题: <回复主题>
正文:
<回复内容>
```"""


def _parse_eml(file_path: Path) -> EmailMessage:
    import mailparser

    mail = mailparser.parse_from_file(str(file_path))

    return EmailMessage(
        sender=mail.from_[0][1] if mail.from_ else "",
        recipients=[r[1] for r in mail.to] if mail.to else [],
        subject=mail.subject or "",
        date=str(mail.date) if mail.date else "",
        body_text=mail.text_plain[0] if mail.text_plain else "",
        body_html=mail.text_html[0] if mail.text_html else "",
        attachments=[a["filename"] for a in mail.attachments if a.get("filename")],
    )


@register_skill
class EmailSkill(BaseSkill):
    name = "email"
    description = "邮件智能分类、自动回复模板生成"
    keywords = ["邮件", "分类", "回复", "email", "mail", "reply"]
    required_inputs = {
        "input_file": {"type": "str", "help": "邮件文件路径 (.eml)"},
    }

    def execute(self, backend: LLMBackend, **kwargs) -> SkillResult:
        input_file = Path(kwargs["input_file"])
        operation = kwargs.get("operation", "classify-and-reply")
        tone = kwargs.get("tone", "professional")
        custom_instructions = kwargs.get("custom_instructions", "")

        if not input_file.exists():
            return SkillResult(
                success=False,
                skill_name=self.name,
                errors=[f"文件不存在: {input_file}"],
            )

        try:
            email = _parse_eml(input_file)

            if operation == "classify":
                classification = self._classify(backend, email)
                return SkillResult(
                    success=True,
                    skill_name=self.name,
                    data={"email": email, "classification": classification},
                    text_output=self._format_classification(email, classification),
                )

            elif operation == "reply":
                reply = self._generate_reply(backend, email, tone, custom_instructions)
                return SkillResult(
                    success=True,
                    skill_name=self.name,
                    data={"email": email, "reply": reply},
                    text_output=self._format_reply(email, reply),
                )

            else:  # classify-and-reply
                classification = self._classify(backend, email)
                reply = self._generate_reply(backend, email, tone, custom_instructions)
                text = (
                    self._format_classification(email, classification)
                    + "\n\n"
                    + self._format_reply(email, reply)
                )

                return SkillResult(
                    success=True,
                    skill_name=self.name,
                    data={
                        "email": email,
                        "classification": classification,
                        "reply": reply,
                    },
                    text_output=text,
                    files_generated=self._save_reply(email, reply),
                )
        except Exception as e:
            return SkillResult(
                success=False,
                skill_name=self.name,
                errors=[str(e)],
            )

    def _classify(self, backend: LLMBackend, email: EmailMessage) -> EmailClassification:
        from office_assistant.config import load_config
        config = load_config()
        categories = "\n".join(f"- {c}" for c in config.skills.email.classification_categories)

        system = CLASSIFY_SYSTEM_PROMPT.format(categories=categories)
        user = f"发件人: {email.sender}\n主题: {email.subject}\n正文:\n{email.body_text[:3000]}"

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]
        response = backend.generate(messages, temperature=0.3, max_tokens=512)

        import json
        import re
        json_match = re.search(r"\{[\s\S]*\}", response.content)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                return EmailClassification(
                    category=data.get("category", "其他"),
                    confidence=data.get("confidence", 0.0),
                    summary=data.get("summary", ""),
                    urgency=data.get("urgency", "normal"),
                )
            except json.JSONDecodeError:
                pass

        return EmailClassification(category="其他", summary="无法分类")

    def _generate_reply(
        self,
        backend: LLMBackend,
        email: EmailMessage,
        tone: str,
        custom_instructions: str,
    ) -> ReplyTemplate:
        system = REPLY_SYSTEM_PROMPT.format(tone=tone)
        user = (
            f"原始邮件:\n"
            f"发件人: {email.sender}\n"
            f"主题: {email.subject}\n"
            f"正文:\n{email.body_text[:3000]}"
        )
        if custom_instructions:
            user += f"\n\n额外指示: {custom_instructions}"

        messages = [
            Message(role="system", content=system),
            Message(role="user", content=user),
        ]
        response = backend.generate(messages, temperature=0.7, max_tokens=2048)

        # Parse subject and body from response
        subject = email.subject
        body = response.content
        for line in response.content.split("\n"):
            if line.startswith("主题:") or line.startswith("Subject:"):
                subject = line.split(":", 1)[-1].strip()
                break

        # Remove the subject line from body
        for prefix in ("主题:", "Subject:"):
            if body.startswith(prefix):
                _, body = body.split("\n", 1)
                body = body.strip()
                break

        return ReplyTemplate(subject=subject, body=body)

    def _format_classification(self, email: EmailMessage, classification: EmailClassification) -> str:
        urgency_icon = {"high": "🔴", "normal": "🟡", "low": "🟢"}
        icon = urgency_icon.get(classification.urgency, "🟡")
        return (
            f"# 邮件分类\n\n"
            f"**发件人**: {email.sender}\n"
            f"**主题**: {email.subject}\n"
            f"**类别**: {classification.category}\n"
            f"**紧急度**: {icon} {classification.urgency}\n"
            f"**置信度**: {classification.confidence:.0%}\n"
            f"**摘要**: {classification.summary}"
        )

    def _format_reply(self, email: EmailMessage, reply: ReplyTemplate) -> str:
        return (
            f"# 回复模板\n\n"
            f"**原始邮件**: {email.subject}\n"
            f"**回复主题**: {reply.subject}\n\n"
            f"**回复正文**:\n\n{reply.body}"
        )

    def _save_reply(self, email: EmailMessage, reply: ReplyTemplate) -> list[Path]:
        from office_assistant.config import load_config
        from office_assistant.utils.file_io import resolve_output_path, write_text

        config = load_config()
        out_dir = Path(config.output.output_dir)
        safe_subject = reply.subject.replace("/", "_").replace("\\", "_")[:50]
        path = resolve_output_path(out_dir, f"reply_{safe_subject}", ".txt")
        write_text(path, reply.body)
        return [path]
