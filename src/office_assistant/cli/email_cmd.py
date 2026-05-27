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

app = typer.Typer(help="邮件处理 - 智能分类、回复模板")


@app.command(name="classify")
def classify(
    input_file: Path = typer.Argument(..., help="邮件文件路径 (.eml)"),
    backend: Optional[str] = typer.Option(
        None, "--backend", "-b",
        help="LLM 后端 (claude/openai/ollama)",
    ),
):
    """对邮件进行智能分类。

    示例:
        office-assistant email classify email.eml
    """
    import office_assistant.skills  # noqa: F401
    from office_assistant.config import load_config
    from office_assistant.backends import create_backend
    from office_assistant.core.skill_registry import SkillRegistry

    if not input_file.exists():
        print_error(f"文件不存在: {input_file}")
        raise typer.Exit(code=1)

    skill = SkillRegistry.get("email")
    if skill is None:
        print_error("邮件处理技能未加载")
        raise typer.Exit(code=1)

    print_title("邮件分类")

    config = load_config()
    backend_name = backend or config.llm.default_backend
    try:
        llm = create_backend(backend_name, config)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(code=1)

    result = skill.execute(
        llm,
        input_file=str(input_file),
        operation="classify",
    )

    if result.success:
        if result.text_output:
            print_markdown(result.text_output)
        print_success("分类完成")
    else:
        for err in result.errors:
            print_error(err)
        raise typer.Exit(code=1)


@app.command(name="reply")
def reply(
    input_file: Path = typer.Argument(..., help="邮件文件路径 (.eml)"),
    tone: str = typer.Option(
        "professional", "--tone", "-t",
        help="回复语气: professional/friendly/concise",
    ),
    instructions: Optional[str] = typer.Option(
        None, "--instructions", "-i",
        help="额外的回复指示",
    ),
    backend: Optional[str] = typer.Option(
        None, "--backend", "-b",
        help="LLM 后端 (claude/openai/ollama)",
    ),
):
    """生成邮件回复模板。

    示例:
        office-assistant email reply email.eml
        office-assistant email reply email.eml --tone friendly -i "告知对方周三有空的会议时间"
    """
    import office_assistant.skills  # noqa: F401
    from office_assistant.config import load_config
    from office_assistant.backends import create_backend
    from office_assistant.core.skill_registry import SkillRegistry

    if not input_file.exists():
        print_error(f"文件不存在: {input_file}")
        raise typer.Exit(code=1)

    skill = SkillRegistry.get("email")
    if skill is None:
        print_error("邮件处理技能未加载")
        raise typer.Exit(code=1)

    print_title("生成回复模板")

    config = load_config()
    backend_name = backend or config.llm.default_backend
    try:
        llm = create_backend(backend_name, config)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(code=1)

    result = skill.execute(
        llm,
        input_file=str(input_file),
        operation="reply",
        tone=tone,
        custom_instructions=instructions or "",
    )

    if result.success:
        if result.text_output:
            print_markdown(result.text_output)
        if result.files_generated:
            print_file_output(result.files_generated)
        print_success("回复模板生成完成")
    else:
        for err in result.errors:
            print_error(err)
        raise typer.Exit(code=1)
