from __future__ import annotations

from pathlib import Path

from office_assistant.backends.base import LLMBackend
from office_assistant.backends.schema import Message
from office_assistant.core.skill_base import BaseSkill
from office_assistant.core.skill_registry import register_skill
from office_assistant.core.skill_result import SkillResult
from office_assistant.models.report import Report, ReportSection

REPORT_PROMPTS = {
    "weekly": {
        "title": "周报",
        "system": "你是一个专业的周报撰写助手。根据用户提供的零散工作内容，生成结构化的周报。\n\n"
                  "周报应包含以下部分：\n"
                  "1. 本周工作摘要\n"
                  "2. 主要成果与进展\n"
                  "3. 遇到的问题与挑战\n"
                  "4. 下周工作计划\n\n"
                  "用专业、清晰的中文撰写，突出量化成果。",
    },
    "daily": {
        "title": "日报",
        "system": "你是一个专业的日报撰写助手。根据用户提供的零散工作内容，生成简洁的日报。\n\n"
                  "日报应包含：\n"
                  "1. 今日完成事项\n"
                  "2. 明日计划\n"
                  "3. 需要协调的事项\n\n"
                  "简洁有力，用 bullet points 呈现。",
    },
    "performance": {
        "title": "述职报告",
        "system": "你是一个专业的述职报告撰写助手。根据用户提供的工作内容，生成述职报告。\n\n"
                  "述职报告应包含：\n"
                  "1. 工作综述\n"
                  "2. 核心成果（量化数据）\n"
                  "3. 能力成长\n"
                  "4. 不足与改进\n"
                  "5. 未来规划\n\n"
                  "正式、专业，突出个人贡献和价值。",
    },
}

STYLE_PROMPTS = {
    "professional": "用专业、正式的商务语言。",
    "casual": "用轻松、口语化的风格，适合团队内部分享。",
    "academic": "用学术论文风格，结构严谨，引用规范。",
}


@register_skill
class ReportWritingSkill(BaseSkill):
    name = "report"
    description = "输入零散工作内容，自动生成周报/日报/述职文案"
    keywords = ["周报", "日报", "述职", "报告", "总结", "report", "weekly", "daily"]
    required_inputs = {
        "content": {"type": "str", "help": "工作内容（可以是零散的描述）"},
        "report_type": {"type": "str", "help": "报告类型: weekly/daily/performance"},
    }

    def execute(self, backend: LLMBackend, **kwargs) -> SkillResult:
        content = kwargs["content"]
        report_type = kwargs.get("report_type", "weekly")
        style = kwargs.get("style", "professional")
        content_file = kwargs.get("content_file")

        # Read from file if provided
        if content_file:
            from office_assistant.utils.file_io import read_text
            file_content = read_text(Path(content_file))
            content = f"{content}\n\n{file_content}"

        prompt = REPORT_PROMPTS.get(report_type, REPORT_PROMPTS["weekly"])

        try:
            report = self._generate_report(backend, content, prompt, style)
            text_output = self._format_output(report)
            files = self._save_output(report, report_type)

            return SkillResult(
                success=True,
                skill_name=self.name,
                data={"report": report},
                text_output=text_output,
                files_generated=files,
                metadata={"report_type": report_type, "style": style},
            )
        except Exception as e:
            return SkillResult(
                success=False,
                skill_name=self.name,
                errors=[str(e)],
            )

    def _generate_report(
        self,
        backend: LLMBackend,
        content: str,
        prompt: dict,
        style: str,
    ) -> Report:
        style_instruction = STYLE_PROMPTS.get(style, STYLE_PROMPTS["professional"])

        messages = [
            Message(role="system", content=f"{prompt['system']}\n\n风格要求: {style_instruction}"),
            Message(role="user", content=f"以下是我的工作内容，请生成{prompt['title']}：\n\n{content}"),
        ]

        response = backend.generate(messages, temperature=0.7, max_tokens=4096)

        # Parse response into sections
        sections = self._parse_sections(response.content)

        return Report(
            title=prompt["title"],
            sections=sections,
            raw_text=response.content,
        )

    def _parse_sections(self, text: str) -> list[ReportSection]:
        import re
        sections = []
        # Split on markdown headings
        pattern = r"^#{1,3}\s+(.+)$"
        parts = re.split(f"({pattern})", text, flags=re.MULTILINE)

        current_title = ""
        for i, part in enumerate(parts):
            heading_match = re.match(pattern, part)
            if heading_match:
                current_title = heading_match.group(1)
            elif part.strip() and current_title:
                sections.append(ReportSection(title=current_title, content=part.strip()))
                current_title = ""

        if not sections:
            sections.append(ReportSection(title="报告内容", content=text))

        return sections

    def _format_output(self, report: Report) -> str:
        lines = [f"# {report.title}", ""]
        for section in report.sections:
            lines.append(f"## {section.title}")
            lines.append(section.content)
            lines.append("")
        return "\n".join(lines)

    def _save_output(
        self,
        report: Report,
        report_type: str,
    ) -> list[Path]:
        from datetime import date
        from pathlib import Path

        from office_assistant.config import load_config
        from office_assistant.utils.file_io import resolve_output_path, write_text

        config = load_config()
        out_dir = Path(config.output.output_dir)
        today = date.today().isoformat()
        filename = f"{report_type}_{today}"

        md_path = resolve_output_path(out_dir, filename, ".md")
        write_text(md_path, self._format_output(report))
        return [md_path]
