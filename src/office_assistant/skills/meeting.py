from __future__ import annotations

from pathlib import Path

from office_assistant.backends.base import LLMBackend
from office_assistant.backends.schema import Message
from office_assistant.core.skill_base import BaseSkill
from office_assistant.core.skill_registry import register_skill
from office_assistant.core.skill_result import SkillResult
from office_assistant.models.meeting import MeetingMinutes, TodoItem


MINUTES_SYSTEM_PROMPT = """你是一个专业的会议纪要提取助手。根据会议录音的转录文本，提取结构化的会议纪要。

请输出格式化的会议纪要，包含以下部分：
1. **会议标题** - 根据内容推断会议主题
2. **会议日期** - 如果文本中有提及
3. **参会人员** - 列出所有提到的参会者
4. **议题** - 列出讨论的主要议题
5. **决策** - 列出会议中做出的所有决定
6. **会议记录** - 详细但精炼的会议内容总结

用中文输出，保持专业、清晰的风格。"""

TODOS_SYSTEM_PROMPT = """你是一个待办事项提取助手。根据会议纪要，提取所有待办事项（Action Items）。

对每个待办事项，提取以下信息：
- 任务描述
- 负责人（如果有提到）
- 截止日期（如果有提到）
- 优先级（high/medium/low，根据上下文判断）

输出 JSON 数组格式：
```json
[{"task": "...", "assignee": "...", "deadline": "...", "priority": "..."}]
```

只输出 JSON，不要其他文本。"""


@register_skill
class MeetingMinutesSkill(BaseSkill):
    name = "meeting"
    description = "会议录音转文字、自动提炼纪要、划分待办事项"
    keywords = ["会议", "纪要", "录音", "转录", "待办", "meeting", "minutes"]
    required_inputs = {
        "audio_file": {"type": "str", "help": "音频文件路径 (mp3/wav/m4a/ogg/flac)"},
        "language": {"type": "str", "help": "语言代码，默认 zh"},
    }

    def execute(self, backend: LLMBackend, **kwargs) -> SkillResult:
        from office_assistant.config import load_config

        audio_path = Path(kwargs["audio_file"])
        language = kwargs.get("language", "zh")

        if not audio_path.exists():
            return SkillResult(
                success=False,
                skill_name=self.name,
                errors=[f"音频文件不存在: {audio_path}"],
            )

        try:
            config = load_config()
            transcriber = WhisperTranscriber(config.whisper)

            transcript = transcriber.transcribe(audio_path, language)

            minutes = self._extract_minutes(backend, transcript.text)
            todos = self._extract_todos(backend, minutes)

            text_output = self._format_output(transcript.text, minutes, todos)
            files = self._save_output(audio_path, minutes, todos, config.output.output_dir)

            return SkillResult(
                success=True,
                skill_name=self.name,
                data={
                    "transcript": transcript,
                    "minutes": minutes,
                    "todos": todos,
                },
                text_output=text_output,
                files_generated=files,
                metadata={"language": transcript.language, "duration": transcript.duration},
            )
        except Exception as e:
            return SkillResult(
                success=False,
                skill_name=self.name,
                errors=[str(e)],
            )

    def _extract_minutes(self, backend: LLMBackend, transcript_text: str) -> MeetingMinutes:
        messages = [
            Message(role="system", content=MINUTES_SYSTEM_PROMPT),
            Message(role="user", content=f"原始转录文本:\n\n{transcript_text}"),
        ]
        response = backend.generate(messages, temperature=0.5, max_tokens=4096)

        # Parse the structured output into MeetingMinutes
        text = response.content
        return MeetingMinutes(
            title=self._extract_section(text, "会议标题"),
            date=self._extract_section(text, "会议日期"),
            attendees=self._extract_list_section(text, "参会人员"),
            topics=self._extract_list_section(text, "议题"),
            decisions=self._extract_list_section(text, "决策"),
            notes=text,
        )

    def _extract_todos(self, backend: LLMBackend, minutes: MeetingMinutes) -> list[TodoItem]:
        import json
        import re

        messages = [
            Message(role="system", content=TODOS_SYSTEM_PROMPT),
            Message(role="user", content=f"会议纪要:\n\n{minutes.notes}"),
        ]
        response = backend.generate(messages, temperature=0.3, max_tokens=2048)

        json_match = re.search(r"\[[\s\S]*\]", response.content)
        if not json_match:
            return []

        try:
            items = json.loads(json_match.group(0))
            return [
                TodoItem(
                    task=item.get("task", ""),
                    assignee=item.get("assignee", ""),
                    deadline=item.get("deadline", ""),
                    priority=item.get("priority", "medium"),
                )
                for item in items
            ]
        except json.JSONDecodeError:
            return []

    def _format_output(
        self,
        transcript: str,
        minutes: MeetingMinutes,
        todos: list[TodoItem],
    ) -> str:
        lines = [
            "# 会议纪要",
            "",
            f"## 会议标题\n{minutes.title}",
            f"## 会议日期\n{minutes.date}",
            f"## 参会人员\n" + "\n".join(f"- {a}" for a in minutes.attendees) if minutes.attendees else "## 参会人员\n（未识别）",
            f"## 议题\n" + "\n".join(f"- {t}" for t in minutes.topics) if minutes.topics else "## 议题\n（未识别）",
            f"## 决策\n" + "\n".join(f"- {d}" for d in minutes.decisions) if minutes.decisions else "## 决策\n（未识别）",
            "## 详细记录",
            minutes.notes,
            "## 待办事项",
        ]
        if todos:
            for i, todo in enumerate(todos, 1):
                lines.append(f"{i}. **{todo.task}**")
                if todo.assignee:
                    lines.append(f"   - 负责人: {todo.assignee}")
                if todo.deadline:
                    lines.append(f"   - 截止日期: {todo.deadline}")
                lines.append(f"   - 优先级: {todo.priority}")
        else:
            lines.append("（无待办事项）")

        lines.append(f"\n---\n*原始转录时长: {minutes.title}*")
        return "\n".join(lines)

    def _save_output(
        self,
        audio_path: Path,
        minutes: MeetingMinutes,
        todos: list[TodoItem],
        output_dir: str,
    ) -> list[Path]:
        from office_assistant.utils.file_io import ensure_dir, resolve_output_path, write_text
        import json

        out_dir = Path(output_dir)
        ensure_dir(out_dir)

        stem = audio_path.stem
        files = []

        md_path = resolve_output_path(out_dir, stem, ".md")
        write_text(md_path, self._format_output("", minutes, todos))
        files.append(md_path)

        todos_path = resolve_output_path(out_dir, f"{stem}_todos", ".json")
        write_text(
            todos_path,
            json.dumps(
                [
                    {
                        "task": t.task,
                        "assignee": t.assignee,
                        "deadline": t.deadline,
                        "priority": t.priority,
                    }
                    for t in todos
                ],
                ensure_ascii=False,
                indent=2,
            ),
        )
        files.append(todos_path)

        return files

    def _extract_section(self, text: str, section_name: str) -> str:
        for line in text.split("\n"):
            if section_name in line:
                content = line.split("##", 1)[-1].strip()
                content = content.replace(f"**{section_name}**", "").strip()
                content = content.lstrip(":：").strip()
                if content:
                    return content
        return ""

    def _extract_list_section(self, text: str, section_name: str) -> list[str]:
        import re
        pattern = rf"{section_name}[\s\S]*?(?=\n##|\Z)"
        match = re.search(pattern, text)
        if not match:
            return []
        section_text = match.group(0)
        items = re.findall(r"[-*]\s+(.+)", section_text)
        return [item.strip() for item in items]


# Import here to avoid circular import - WhisperTranscriber is used in execute()
from office_assistant.audio.transcriber import WhisperTranscriber  # noqa: E402, F811
