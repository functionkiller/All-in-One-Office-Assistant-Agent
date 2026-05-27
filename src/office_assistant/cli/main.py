from __future__ import annotations

from typing import Optional

import typer

from office_assistant.cli import config_cmd, email_cmd, meeting_cmd, report_cmd, spreadsheet_cmd
from office_assistant.utils.formatters import (
    console,
    print_error,
    print_file_output,
    print_info,
    print_markdown,
    print_success,
    print_title,
)

app = typer.Typer(
    name="office-assistant",
    help="全能办公助手 - All-in-One Office Assistant Agent",
    rich_markup_mode="rich",
)

app.add_typer(meeting_cmd.app, name="meeting", help="会议纪要 - 录音转文字、提炼纪要、提取待办")
app.add_typer(report_cmd.app, name="report", help="报告生成 - 周报/日报/述职报告")
app.add_typer(spreadsheet_cmd.app, name="spreadsheet", help="表格处理 - 格式转换、数据清洗、分析")
app.add_typer(email_cmd.app, name="email", help="邮件处理 - 智能分类、回复模板")
app.add_typer(config_cmd.app, name="config", help="配置管理 - 查看和修改配置")


@app.command(name="ask")
def ask(
    prompt: list[str] = typer.Argument(..., help="自然语言描述你的需求"),
    backend: Optional[str] = typer.Option(
        None, "--backend", "-b",
        help="LLM 后端指定 (claude/openai/ollama)",
    ),
):
    """自然语言交互：用说话的方式描述需求，Agent 自动识别意图并路由到对应技能。

    示例:
        office-assistant ask "帮我整理上周的会议录音 meeting.mp3"
        office-assistant ask "把这周的工作内容写成周报：完成了A功能、修复了B bug、参加了C会议"
        office-assistant ask "把 data.csv 转成 xlsx 格式"
        office-assistant ask "帮我看看这封邮件是不是紧急的"
    """
    user_input = " ".join(prompt)

    # Import skills to trigger registration
    import office_assistant.skills  # noqa: F401
    from office_assistant.config import load_config
    from office_assistant.backends import create_backend, create_router_backend
    from office_assistant.core.router import AgentRouter
    from office_assistant.core.skill_registry import SkillRegistry

    try:
        config = load_config()
    except Exception as e:
        print_error(f"配置加载失败: {e}")
        raise typer.Exit(code=1)

    try:
        router_backend = create_router_backend(config)
    except Exception as e:
        print_error(f"后端初始化失败: {e}")
        raise typer.Exit(code=1)

    # For execution of the skill, use the specified or default backend
    if backend:
        try:
            exec_backend = create_backend(backend, config)
        except ValueError as e:
            print_error(str(e))
            raise typer.Exit(code=1)
    else:
        exec_backend = create_backend(config.llm.default_backend, config)

    router = AgentRouter(router_backend)

    print_info(f"正在分析您的需求... (路由: {router_backend.model}, 执行: {exec_backend.model})")

    # Route to determine which skill
    route_result = router.route(user_input)

    if route_result.clarification_needed:
        print_info(f"需要更多信息: {route_result.clarification_question}")
        raise typer.Exit()

    skill_name = route_result.skill
    skill = SkillRegistry.get(skill_name)
    if skill is None:
        available = [s.name for s in SkillRegistry.list_all()]
        print_error(f"未找到技能 '{skill_name}'。可用技能: {', '.join(available)}")
        raise typer.Exit(code=1)

    print_info(f"识别意图: [{skill_name}] {skill.description} (置信度: {route_result.confidence:.0%})")

    # Execute with the execution backend
    result = skill.execute(exec_backend, **route_result.parameters)

    if result.success:
        print_title(f"执行结果 - {skill_name}")
        if result.text_output:
            print_markdown(result.text_output)
        if result.files_generated:
            print_file_output(result.files_generated)
        print_success("执行完成")
    else:
        for err in result.errors:
            print_error(err)
        raise typer.Exit(code=1)


def main():
    app()


if __name__ == "__main__":
    main()
