from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import yaml

from office_assistant.utils.formatters import print_error, print_info, print_success, print_table

app = typer.Typer(help="配置管理 - 查看和修改配置")


@app.command(name="show")
def show():
    """显示当前配置（敏感信息已脱敏）。"""
    from office_assistant.config import load_config

    try:
        config = load_config()
    except Exception as e:
        print_error(f"配置加载失败: {e}")
        raise typer.Exit(code=1)

    typer.echo(f"[bold]LLM 默认后端:[/bold] {config.llm.default_backend}")
    typer.echo(f"[bold]路由后端:[/bold] {config.llm.router_backend or '(复用默认)'}")

    for name in ["claude", "openai", "ollama"]:
        be = getattr(config.llm.backends, name)
        api_key_display = "***" + be.api_key[-4:] if be.api_key else "(未设置)"
        typer.echo(f"\n[bold]{name} 后端:[/bold]")
        typer.echo(f"  模型: {be.model}")
        typer.echo(f"  API Key: {api_key_display}")

    typer.echo(f"\n[bold]Whisper:[/bold]")
    typer.echo(f"  模型: {config.whisper.model_size}")
    typer.echo(f"  设备: {config.whisper.device}")

    typer.echo(f"\n[bold]输出:[/bold]")
    typer.echo(f"  目录: {config.output.output_dir}")
    typer.echo(f"  保存文件: {config.output.save_output}")


@app.command(name="validate")
def validate(
    config_path: Optional[Path] = typer.Option(
        None, "--config", "-c",
        help="指定配置文件路径",
    ),
):
    """验证配置文件格式。"""
    from office_assistant.config import load_config

    try:
        load_config(config_path)
        print_success("配置文件验证通过")
    except Exception as e:
        print_error(f"配置文件验证失败: {e}")
        raise typer.Exit(code=1)


@app.command(name="path")
def config_path():
    """显示配置文件位置。"""
    from office_assistant.config.loader import _search_config_paths

    paths = _search_config_paths()
    for p in paths:
        status = "✓ 存在" if p.exists() else "✗ 不存在"
        color = "green" if p.exists() else "yellow"
        typer.echo(f"[{color}]{status}[/{color}] {p}")


@app.command(name="init")
def init_config():
    """在当前目录创建默认配置文件。"""
    target = Path("config.yaml")
    if target.exists():
        print_info(f"config.yaml 已存在，跳过。如需覆盖请手动删除后重试。")
        raise typer.Exit()

    default_content = """llm:
  default_backend: claude
  router_backend: null
  router_model: null

  backends:
    claude:
      api_key: ${ANTHROPIC_API_KEY}
      model: claude-sonnet-4-20250514
      max_tokens: 8192
      temperature: 0.7

    openai:
      api_key: ${OPENAI_API_KEY}
      base_url: https://api.openai.com/v1
      model: gpt-4o
      max_tokens: 8192
      temperature: 0.7

    ollama:
      host: http://localhost:11434
      model: qwen3:14b
      max_tokens: 4096
      temperature: 0.7
      keep_alive: 5m

whisper:
  engine: faster-whisper
  model_size: medium
  device: auto
  compute_type: int8
  language: auto
  beam_size: 5
  vad_filter: true

skills:
  meeting:
    default_language: zh
    auto_todo_extraction: true
    output_format: markdown

  report:
    default_style: professional
    default_type: weekly
    section_templates:
      - summary
      - achievements
      - challenges
      - next_steps

  spreadsheet:
    default_output_format: xlsx
    encoding: utf-8
    max_preview_rows: 20

  email:
    reply_tone: professional
    classification_categories:
      - 紧急
      - 会议邀请
      - 工作汇报
      - 一般咨询
      - 垃圾邮件
      - 其他

output:
  format: rich
  color: true
  save_output: true
  output_dir: ./output
"""
    target.write_text(default_content, encoding="utf-8")
    print_success("已在当前目录创建 config.yaml")
    print_info("请编辑 config.yaml 填入你的 API Key，或通过环境变量设置。")
