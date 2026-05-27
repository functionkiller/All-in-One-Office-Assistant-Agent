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

app = typer.Typer(help="表格处理 - 格式转换、数据清洗、分析")


@app.command(name="convert")
def convert(
    input_file: Path = typer.Argument(..., help="输入文件路径"),
    output_format: str = typer.Option(
        ..., "--to", "-t",
        help="目标格式 (xlsx/csv/json/html)",
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="输出文件路径（默认同目录同名）",
    ),
):
    """文件格式互转。

    支持格式: xlsx, xls, csv, tsv, json, parquet

    示例:
        office-assistant spreadsheet convert data.csv --to xlsx
        office-assistant spreadsheet convert data.xlsx --to json -o output.json
    """
    import office_assistant.skills  # noqa: F401
    from office_assistant.core.skill_registry import SkillRegistry

    if not input_file.exists():
        print_error(f"文件不存在: {input_file}")
        raise typer.Exit(code=1)

    skill = SkillRegistry.get("spreadsheet")
    if skill is None:
        print_error("表格处理技能未加载")
        raise typer.Exit(code=1)

    print_title("表格格式转换")

    # We use a dummy backend since convert doesn't need LLM
    from office_assistant.config import load_config
    from office_assistant.backends import create_backend

    config = load_config()
    llm = create_backend(config.llm.default_backend, config)

    result = skill.execute(
        llm,
        input_file=str(input_file),
        operation="convert",
        output_format=output_format,
    )

    if result.success:
        print(result.text_output)
        if result.files_generated:
            print_file_output(result.files_generated)
        print_success("转换完成")
    else:
        for err in result.errors:
            print_error(err)
        raise typer.Exit(code=1)


@app.command(name="clean")
def clean(
    input_file: Path = typer.Argument(..., help="输入文件路径"),
    drop_duplicates: bool = typer.Option(
        True, "--dedup/--no-dedup",
        help="删除重复行",
    ),
    fill_missing: bool = typer.Option(
        False, "--fill/--no-fill",
        help="填充缺失值",
    ),
    normalize_dates: bool = typer.Option(
        False, "--normalize-dates/--no-normalize-dates",
        help="规范化日期列",
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="输出文件路径",
    ),
):
    """数据清洗。

    示例:
        office-assistant spreadsheet clean data.xlsx
        office-assistant spreadsheet clean data.csv --fill --normalize-dates
    """
    import office_assistant.skills  # noqa: F401
    from office_assistant.config import load_config
    from office_assistant.backends import create_backend
    from office_assistant.core.skill_registry import SkillRegistry

    if not input_file.exists():
        print_error(f"文件不存在: {input_file}")
        raise typer.Exit(code=1)

    skill = SkillRegistry.get("spreadsheet")
    if skill is None:
        print_error("表格处理技能未加载")
        raise typer.Exit(code=1)

    print_title("数据清洗")

    config = load_config()
    llm = create_backend(config.llm.default_backend, config)

    operations = []
    if not drop_duplicates and not fill_missing and not normalize_dates:
        operations = []  # default: drop_duplicates + strip + standardize
    else:
        if drop_duplicates:
            operations.append("drop_duplicates")
        operations.append("strip_whitespace")
        operations.append("standardize_columns")
        if fill_missing:
            operations.append("fill_missing")
        if normalize_dates:
            operations.append("normalize_dates")

    result = skill.execute(
        llm,
        input_file=str(input_file),
        operation="clean",
        clean_operations=operations,
    )

    if result.success:
        print(result.text_output)
        if result.files_generated:
            print_file_output(result.files_generated)
        print_success("清洗完成")
    else:
        for err in result.errors:
            print_error(err)
        raise typer.Exit(code=1)


@app.command(name="analyze")
def analyze(
    input_file: Path = typer.Argument(..., help="输入文件路径"),
    backend: Optional[str] = typer.Option(
        None, "--backend", "-b",
        help="LLM 后端 (claude/openai/ollama)",
    ),
):
    """数据分析 - 生成数据概览和 AI 洞察。

    示例:
        office-assistant spreadsheet analyze sales.xlsx
    """
    import office_assistant.skills  # noqa: F401
    from office_assistant.config import load_config
    from office_assistant.backends import create_backend
    from office_assistant.core.skill_registry import SkillRegistry

    if not input_file.exists():
        print_error(f"文件不存在: {input_file}")
        raise typer.Exit(code=1)

    skill = SkillRegistry.get("spreadsheet")
    if skill is None:
        print_error("表格处理技能未加载")
        raise typer.Exit(code=1)

    print_title(f"数据分析: {input_file.name}")

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
        operation="analyze",
    )

    if result.success:
        if result.text_output:
            print_markdown(result.text_output)
        print_success("分析完成")
    else:
        for err in result.errors:
            print_error(err)
        raise typer.Exit(code=1)
