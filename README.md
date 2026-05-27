# 全能办公助手 Agent

> CLI 形态的智能办公助手，解决重复办公操作耗时问题。

基于 LLM 的 Agent 架构，将办公能力拆解为多个独立 Skill，Agent 自动识别意图并路由调用。

## 核心能力

| Skill | 功能 | 示例 |
|-------|------|------|
| **meeting** | 录音 → Whisper 转文字 → 提炼纪要 → 提取待办 | `oa meeting transcribe meeting.mp3` |
| **report** | 零散工作内容 → 周报/日报/述职报告 | `oa report weekly "完成了A、B、C"` |
| **spreadsheet** | 多格式互转、数据清洗、AI 数据分析 | `oa spreadsheet analyze data.xlsx` |
| **email** | .eml 解析 → 智能分类 → 自动回复模板 | `oa email classify email.eml` |

## 安装

```bash
# 克隆仓库
git clone https://github.com/functionkiller/All-in-One-Office-Assistant-Agent.git
cd All-in-One-Office-Assistant-Agent

# 安装
pip install -e .

# 如需音频录制支持 (可选)
pip install -e ".[dev]"
```

## 快速开始

### 1. 配置

```bash
# 在当前目录创建配置文件
oa config init

# 编辑 config.yaml 填入 API Key
# 或通过环境变量设置
export ANTHROPIC_API_KEY=sk-ant-xxx
```

### 2. 使用

```bash
# 结构化命令
oa meeting transcribe meeting.mp3 -l zh
oa report weekly "完成了登录模块、修复了3个bug"
oa spreadsheet convert data.csv --to xlsx
oa email classify email.eml

# 自然语言交互（LLM 自动路由）
oa ask "帮我把上周的会议录音整理成纪要"
oa ask "把这周工作写成周报"
oa ask "分析一下 sales.xlsx 的销售数据"
```

### 3. 切换 LLM 后端

```bash
# CLI 方式
oa ask "帮我写周报" --backend openai
oa ask "帮我写周报" --backend ollama

# 环境变量方式
OA_LLM_DEFAULT_BACKEND=ollama oa ask "帮我写周报"

# 配置文件方式
oa config set llm.default_backend ollama
```

## 架构

```
CLI (Typer + Rich)
    │
    ▼
Agent Router (LLM 意图分类)
    │
    ├── MeetingMinutesSkill ──→ WhisperTranscriber (faster-whisper) + LLM
    ├── ReportWritingSkill ───→ LLM
    ├── SpreadsheetSkill ─────→ pandas + LLM
    └── EmailSkill ───────────→ mail-parser + LLM
    │
    ▼
LLM Backend Adapter ──→ Claude / OpenAI / Ollama
```

## 项目结构

```
src/office_assistant/
├── cli/              # Typer 命令行层
│   ├── main.py       # 主入口 + ask 自然语言命令
│   ├── meeting_cmd.py
│   ├── report_cmd.py
│   ├── spreadsheet_cmd.py
│   ├── email_cmd.py
│   └── config_cmd.py
├── core/             # Agent Router + Skill 基类
│   ├── router.py     # LLM 意图分类 + 分发
│   ├── skill_base.py
│   ├── skill_registry.py
│   └── skill_result.py
├── backends/         # LLM 后端适配层
│   ├── base.py       # 统一抽象接口
│   ├── schema.py     # 归一化数据类型
│   ├── factory.py    # 后端工厂
│   ├── claude.py     # ClaudeBackend
│   ├── openai_backend.py
│   └── ollama.py
├── skills/           # 四大技能模块
│   ├── meeting.py
│   ├── report.py
│   ├── spreadsheet.py
│   └── email_skill.py
├── audio/
│   └── transcriber.py   # faster-whisper 封装
├── config/
│   ├── loader.py        # YAML + ${ENV} 配置加载
│   └── schema.py        # Pydantic 校验
├── models/              # 数据模型
└── utils/               # 工具函数 + Rich 格式化
```

## 运行测试

```bash
pip install pytest pytest-mock
python -m pytest tests/ -v
```

## 支持的 LLM 后端

| 后端 | 配置项 | 说明 |
|------|--------|------|
| Claude | `ANTHROPIC_API_KEY` | 能力最强，支持 tool use |
| OpenAI | `OPENAI_API_KEY` | GPT-4o 等模型 |
| Ollama | 本地部署 | 隐私安全，无需联网 |

## 语音识别

使用 `faster-whisper` 本地运行，支持 CPU/GPU 自动切换。支持格式：mp3, wav, m4a, ogg, flac。

```bash
# 转录音频并提取纪要
oa meeting transcribe meeting.mp3 -l zh
```

## 表格处理

```bash
# 格式转换
oa spreadsheet convert data.csv --to xlsx
oa spreadsheet convert data.json --to csv

# 数据清洗
oa spreadsheet clean data.xlsx --fill --normalize-dates

# AI 分析
oa spreadsheet analyze sales.xlsx
```

## 邮件处理

```bash
# 智能分类
oa email classify inquiry.eml

# 生成回复
oa email reply inquiry.eml --tone professional -i "告知对方周三下午有空"
```

## 配置参考

完整配置项见 `config.yaml`，支持 `${ENV_VAR}` 环境变量替换和 `OA_*` 环境变量覆盖。

```bash
# 查看当前配置
oa config show

# 验证配置
oa config validate

# 显示配置文件位置
oa config path
```

## License

MIT
