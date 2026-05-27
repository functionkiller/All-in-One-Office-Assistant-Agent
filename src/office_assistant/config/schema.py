from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ClaudeConfig(BaseModel):
    api_key: str
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8192
    temperature: float = 0.7


class OpenAIConfig(BaseModel):
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"
    max_tokens: int = 8192
    temperature: float = 0.7


class OllamaConfig(BaseModel):
    host: str = "http://localhost:11434"
    model: str = "qwen3:14b"
    max_tokens: int = 4096
    temperature: float = 0.7
    keep_alive: str = "5m"


class LLMBackendsConfig(BaseModel):
    claude: ClaudeConfig
    openai: OpenAIConfig
    ollama: OllamaConfig


class LLMConfig(BaseModel):
    default_backend: Literal["claude", "openai", "ollama"] = "claude"
    router_backend: Optional[Literal["claude", "openai", "ollama"]] = None
    router_model: Optional[str] = None
    backends: LLMBackendsConfig


class WhisperConfig(BaseModel):
    engine: Literal["faster-whisper", "openai-whisper"] = "faster-whisper"
    model_size: Literal["tiny", "base", "small", "medium", "large-v3"] = "medium"
    device: Literal["auto", "cpu", "cuda"] = "auto"
    compute_type: Literal["float16", "int8", "int8_float16"] = "int8"
    language: str = "auto"
    beam_size: int = 5
    vad_filter: bool = True


class MeetingSkillConfig(BaseModel):
    default_language: str = "zh"
    auto_todo_extraction: bool = True
    output_format: Literal["markdown", "json", "text"] = "markdown"


class ReportSkillConfig(BaseModel):
    default_style: Literal["professional", "casual", "academic"] = "professional"
    default_type: Literal["weekly", "daily", "performance"] = "weekly"
    section_templates: list[str] = Field(
        default_factory=lambda: ["summary", "achievements", "challenges", "next_steps"]
    )


class SpreadsheetSkillConfig(BaseModel):
    default_output_format: str = "xlsx"
    encoding: str = "utf-8"
    max_preview_rows: int = 20


class EmailSkillConfig(BaseModel):
    reply_tone: str = "professional"
    classification_categories: list[str] = Field(
        default_factory=lambda: ["紧急", "会议邀请", "工作汇报", "一般咨询", "垃圾邮件", "其他"]
    )


class SkillsConfig(BaseModel):
    meeting: MeetingSkillConfig = Field(default_factory=MeetingSkillConfig)
    report: ReportSkillConfig = Field(default_factory=ReportSkillConfig)
    spreadsheet: SpreadsheetSkillConfig = Field(default_factory=SpreadsheetSkillConfig)
    email: EmailSkillConfig = Field(default_factory=EmailSkillConfig)


class OutputConfig(BaseModel):
    format: Literal["rich", "plain", "markdown"] = "rich"
    color: bool = True
    save_output: bool = True
    output_dir: str = "./output"


class AppConfig(BaseModel):
    llm: LLMConfig
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
