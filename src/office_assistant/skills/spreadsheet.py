from __future__ import annotations

from pathlib import Path

import pandas as pd

from office_assistant.backends.base import LLMBackend
from office_assistant.backends.schema import Message
from office_assistant.core.skill_base import BaseSkill
from office_assistant.core.skill_registry import register_skill
from office_assistant.core.skill_result import SkillResult
from office_assistant.models.spreadsheet import DataSummary


def _load_file(file_path: Path, encoding: str = "utf-8") -> pd.DataFrame:
    ext = file_path.suffix.lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(file_path)
    elif ext == ".csv":
        return pd.read_csv(file_path, encoding=encoding)
    elif ext == ".tsv":
        return pd.read_csv(file_path, sep="\t", encoding=encoding)
    elif ext == ".json":
        return pd.read_json(file_path)
    elif ext == ".parquet":
        return pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _save_file(df: pd.DataFrame, file_path: Path, encoding: str = "utf-8") -> Path:
    ext = file_path.suffix.lower()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if ext in (".xlsx", ".xls"):
        df.to_excel(file_path, index=False)
    elif ext == ".csv":
        df.to_csv(file_path, index=False, encoding=encoding)
    elif ext == ".tsv":
        df.to_csv(file_path, sep="\t", index=False, encoding=encoding)
    elif ext == ".json":
        df.to_json(file_path, orient="records", force_ascii=False, indent=2)
    elif ext == ".html":
        df.to_html(file_path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {ext}")
    return file_path


@register_skill
class SpreadsheetSkill(BaseSkill):
    name = "spreadsheet"
    description = "多格式互转、表格数据清洗、简单数据分析"
    keywords = ["表格", "转换", "清洗", "分析", "excel", "csv", "spreadsheet", "data"]
    required_inputs = {
        "input_file": {"type": "str", "help": "输入文件路径"},
    }

    def execute(self, backend: LLMBackend, **kwargs) -> SkillResult:
        input_file = Path(kwargs["input_file"])
        operation = kwargs.get("operation", "analyze")

        if not input_file.exists():
            return SkillResult(
                success=False,
                skill_name=self.name,
                errors=[f"文件不存在: {input_file}"],
            )

        try:
            if operation == "convert":
                return self._convert(input_file, kwargs.get("output_format", "xlsx"))
            elif operation == "clean":
                return self._clean(input_file, kwargs.get("clean_operations", []))
            elif operation == "analyze":
                return self._analyze(backend, input_file)
            else:
                return SkillResult(
                    success=False,
                    skill_name=self.name,
                    errors=[f"Unknown operation: {operation}"],
                )
        except Exception as e:
            return SkillResult(
                success=False,
                skill_name=self.name,
                errors=[str(e)],
            )

    def _convert(self, input_file: Path, output_format: str) -> SkillResult:
        df = _load_file(input_file)
        output_path = input_file.with_suffix(f".{output_format}")
        saved = _save_file(df, output_path)

        return SkillResult(
            success=True,
            skill_name=self.name,
            data={"row_count": len(df), "column_count": len(df.columns)},
            text_output=f"转换完成: {input_file.name} → {output_path.name}\n行数: {len(df)}, 列数: {len(df.columns)}",
            files_generated=[saved],
        )

    def _clean(self, input_file: Path, operations: list[str]) -> SkillResult:
        df = _load_file(input_file)
        original_rows = len(df)
        changes = []

        # Apply cleaning operations
        if not operations or "drop_duplicates" in operations:
            before = len(df)
            df = df.drop_duplicates()
            if len(df) < before:
                changes.append(f"删除重复行: {before - len(df)} 行")

        if not operations or "strip_whitespace" in operations:
            str_cols = df.select_dtypes(include=["object"]).columns
            for col in str_cols:
                df[col] = df[col].astype(str).str.strip()

        if not operations or "standardize_columns" in operations:
            df.columns = [
                col.strip().lower().replace(" ", "_").replace("（", "_").replace("）", "")
                for col in df.columns
            ]
            changes.append(f"规范化列名: {', '.join(df.columns)}")

        if "fill_missing" in operations:
            for col in df.columns:
                if df[col].dtype in ("float64", "int64"):
                    df[col] = df[col].fillna(df[col].median())
                else:
                    df[col] = df[col].fillna("N/A")
            changes.append("填充缺失值")

        if "normalize_dates" in operations:
            for col in df.select_dtypes(include=["object"]).columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                    changes.append(f"日期列规范化: {col}")
                except (ValueError, TypeError):
                    pass

        output_path = input_file.parent / f"{input_file.stem}_cleaned{input_file.suffix}"
        saved = _save_file(df, output_path)

        return SkillResult(
            success=True,
            skill_name=self.name,
            data={
                "original_rows": original_rows,
                "cleaned_rows": len(df),
                "changes": changes,
            },
            text_output=f"数据清洗完成:\n" + "\n".join(f"  - {c}" for c in changes),
            files_generated=[saved],
        )

    def _analyze(self, backend: LLMBackend, input_file: Path) -> SkillResult:
        df = _load_file(input_file)
        summary = self._compute_summary(df)

        # Use LLM to generate natural language analysis
        stats_text = self._format_stats(summary)
        messages = [
            Message(role="system", content="你是一个数据分析师。根据数据概览，用中文提供简洁的数据分析洞察。包括：数据质量评估、关键发现、异常值提示、行动建议。不超过 500 字。"),
            Message(role="user", content=f"数据概览:\n{stats_text}"),
        ]
        response = backend.generate(messages, temperature=0.5, max_tokens=1024)
        summary.analysis_text = response.content

        text_output = f"# 数据分析报告: {input_file.name}\n\n{stats_text}\n\n## 分析洞察\n{summary.analysis_text}"

        return SkillResult(
            success=True,
            skill_name=self.name,
            data={"summary": summary},
            text_output=text_output,
            metadata={"row_count": summary.row_count, "column_count": summary.column_count},
        )

    def _compute_summary(self, df: pd.DataFrame) -> DataSummary:
        numeric_cols = df.select_dtypes(include=["float64", "int64"])
        stats = {}
        for col in numeric_cols.columns:
            stats[col] = {
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "median": float(df[col].median()),
            }

        return DataSummary(
            row_count=len(df),
            column_count=len(df.columns),
            columns=list(df.columns),
            dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
            missing_counts={col: int(df[col].isna().sum()) for col in df.columns},
            numeric_stats=stats,
        )

    def _format_stats(self, summary: DataSummary) -> str:
        lines = [
            f"行数: {summary.row_count}",
            f"列数: {summary.column_count}",
            "列信息:",
        ]
        for col in summary.columns:
            dtype = summary.dtypes.get(col, "unknown")
            missing = summary.missing_counts.get(col, 0)
            lines.append(f"  - {col} ({dtype}), 缺失值: {missing}")
        if summary.numeric_stats:
            lines.append("数值列统计:")
            for col, st in summary.numeric_stats.items():
                lines.append(
                    f"  - {col}: mean={st['mean']:.2f}, median={st['median']:.2f}, "
                    f"min={st['min']:.2f}, max={st['max']:.2f}, std={st['std']:.2f}"
                )
        return "\n".join(lines)
