from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from office_assistant.utils.formatters import (
    print_error,
    print_file_output,
    print_markdown,
    print_success,
    print_title,
)

app = typer.Typer(help="报告生成 - 周报/日报/述职报告")


@app.command(name="weekly")
def weekly(
    content: list[str] = typer.Argument(..., help="工作内容描述"),
    content_file: Optional[Path] = typer.Option(
        None, "--file", "-f",
        help="从文件读取工作内容",
    ),
    style: str = typer.Option(
        "professional", "--style", "-s",
        help="报告风格: professional/casual/academic",
    ),
    backend: Optional[str] = typer.Option(
        None, "--backend", "-b",
        help="LLM 后端 (claude/openai/ollama)",
    ),
):
    """生成周报。

    示例:
        office-assistant report weekly "完成了登录模块、修复了3个bug、参加了需求评审"
        office-assistant report weekly -f work_notes.txt --style casual
    """
    _generate_report("weekly", " ".join(content), content_file, style, backend)


@app.command(name="daily")
def daily(
    content: list[str] = typer.Argument(..., help="今日工作内容"),
    content_file: Optional[Path] = typer.Option(
        None, "--file", "-f",
        help="从文件读取工作内容",
    ),
    style: str = typer.Option(
        "professional", "--style", "-s",
        help="报告风格: professional/casual/academic",
    ),
    backend: Optional[str] = typer.Option(
        None, "--backend", "-b",
        help="LLM 后端 (claude/openai/ollama)",
    ),
):
    """生成日报。"""
    _generate_report("daily", " ".join(content), content_file, style, backend)


@app.command(name="performance")
def performance(
    content: list[str] = typer.Argument(..., help="工作内容描述"),
    content_file: Optional[Path] = typer.Option(
        None, "--file", "-f",
        help="从文件读取工作内容",
    ),
    style: str = typer.Option(
        "professional", "--style", "-s",
        help="报告风格: professional/casual/academic",
    ),
    backend: Optional[str] = typer.Option(
        None, "--backend", "-b",
        help="LLM 后端 (claude/openai/ollama)",
    ),
):
    """生成述职报告。"""
    _generate_report("performance", " ".join(content), content_file, style, backend)


def _generate_report(
    report_type: str,
    content: str,
    content_file: Optional[Path],
    style: str,
    backend_name: Optional[str],
) -> None:
    import office_assistant.skills  # noqa: F401
    from office_assistant.config import load_config
    from office_assistant.backends import create_backend
    from office_assistant.core.skill_registry import SkillRegistry

    try:
        config = load_config()
    except Exception as e:
        print_error(f"配置加载失败: {e}")
        raise typer.Exit(code=1)

    backend_name = backend_name or config.llm.default_backend
    try:
        llm = create_backend(backend_name, config)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(code=1)

    skill = SkillRegistry.get("report")
    if skill is None:
        print_error("报告生成技能未加载")
        raise typer.Exit(code=1)

    type_names = {"weekly": "周报", "daily": "日报", "performance": "述职报告"}
    print_title(f"生成{type_names.get(report_type, '报告')}")

    params: dict = {
        "content": content,
        "report_type": report_type,
        "style": style,
    }
    if content_file:
        params["content_file"] = str(content_file)

    result = skill.execute(llm, **params)

    if result.success:
        if result.text_output:
            print_markdown(result.text_output)
        if result.files_generated:
            print_file_output(result.files_generated)
        print_success("报告生成完成")
    else:
        for err in result.errors:
            print_error(err)
        raise typer.Exit(code=1)
