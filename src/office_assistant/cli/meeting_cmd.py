from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from office_assistant.utils.formatters import (
    console,
    print_error,
    print_file_output,
    print_markdown,
    print_success,
    print_title,
)

app = typer.Typer(help="会议纪要 - 录音转文字、提炼纪要、提取待办")


@app.command(name="transcribe")
def transcribe(
    audio_file: Path = typer.Argument(..., help="音频文件路径"),
    language: Optional[str] = typer.Option(
        None, "--language", "-l",
        help="语言代码 (zh/en/auto)，默认 auto",
    ),
    extract_todos: bool = typer.Option(
        True, "--todos/--no-todos",
        help="是否提取待办事项",
    ),
    backend: Optional[str] = typer.Option(
        None, "--backend", "-b",
        help="LLM 后端 (claude/openai/ollama)",
    ),
):
    """将会议录音转文字，自动提炼纪要和待办事项。

    示例:
        office-assistant meeting transcribe meeting.mp3
        office-assistant meeting transcribe meeting.mp3 -l zh --backend openai
    """
    import office_assistant.skills  # noqa: F401
    from office_assistant.config import load_config
    from office_assistant.backends import create_backend
    from office_assistant.core.skill_registry import SkillRegistry

    if not audio_file.exists():
        print_error(f"音频文件不存在: {audio_file}")
        raise typer.Exit(code=1)

    try:
        config = load_config()
    except Exception as e:
        print_error(f"配置加载失败: {e}")
        raise typer.Exit(code=1)

    backend_name = backend or config.llm.default_backend
    try:
        llm = create_backend(backend_name, config)
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(code=1)

    skill = SkillRegistry.get("meeting")
    if skill is None:
        print_error("会议纪要技能未加载")
        raise typer.Exit(code=1)

    print_title("会议纪要 - 开始处理")
    print(f"[bold]音频文件:[/bold] {audio_file}")
    print(f"[bold]后端:[/bold] {backend_name} ({llm.model})")

    params: dict = {"audio_file": str(audio_file)}
    if language:
        params["language"] = language

    with console.status("[bold cyan]正在转录音频..."):
        result = skill.execute(llm, **params)

    if result.success:
        if result.text_output:
            print_markdown(result.text_output)
        if result.files_generated:
            print_file_output(result.files_generated)
        print_success("处理完成")
    else:
        for err in result.errors:
            print_error(err)
        raise typer.Exit(code=1)
