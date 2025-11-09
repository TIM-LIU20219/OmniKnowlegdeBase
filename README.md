# OmniKnowledgeBase

A RAG-focused knowledge base with document processing, Obsidian-like note management, AI-powered note generation, and Streamlit UI.

## Features

- 📄 Document processing (Markdown, PDF, URL)
- 📝 Obsidian-style note management with bidirectional links
- 🤖 RAG-based Q&A system
- ✍️ AI note generation (LLM generates Obsidian format notes)
- 🎨 Streamlit UI (fast LLM app development)

## Quick Start

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions.

### Prerequisites

1. **Create `.env` file**: Copy `.env.example` to `.env` and configure required settings:

   ```bash
   cp .env.example .env
   ```

   **⚠️ Important**: You must set `EMBEDDING_MODEL` in `.env` file. The application will not start without it.

   Example:

   ```bash
   EMBEDDING_MODEL=BAAI/bge-base-zh-v1.5
   ```

   See [docs/CHINESE_MODELS_CONFIG.md](docs/CHINESE_MODELS_CONFIG.md) for available models and configuration options.

### Backend + Frontend (Streamlit)

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动后端服务（可选，如果使用CLI）
cd backend
uvicorn main:app --reload --port 8000

# 运行 Streamlit 应用
streamlit run app.py
```

应用将在 `http://localhost:8501` 启动。

## AI Note Generation

智能笔记生成功能支持两种模式：

- **`/new` 模式**：使用LLM自身知识生成笔记，不进行RAG检索
- **`/ask` 模式**：先进行RAG检索，然后基于检索结果生成笔记（默认）

### CLI Usage

```bash
# 使用RAG检索模式生成笔记（默认）
python cli.py note generate "什么是RAG？"

# 使用LLM知识模式生成笔记
python cli.py note generate "Python基础语法" --mode new

# 生成并立即保存
python cli.py note generate "机器学习基础" --mode ask --save --tags "AI,ML"

# 查看所有选项
python cli.py note generate --help
```

### Frontend Usage

1. 启动前端应用：`streamlit run app.py`
2. 导航到 **📝 Notes** 页面
3. 在侧边栏切换到 **🤖 Generate** 标签页
4. 选择生成模式（`ask` 或 `new`）
5. 输入主题/问题，点击 **Generate** 或 **Generate & Save**

### Note Generation Features

- ✨ 自动识别并建立Obsidian格式的笔记链接 `[[note-name]]`
- 🔍 相似性检阅：自动搜索相似笔记并提供建议
- 📚 RAG检索：基于已有文档和笔记生成内容
- 🎯 智能链接：自动匹配相关笔记并添加双向链接

详细使用说明请参考 [笔记生成功能使用指南](docs/NOTE_GENERATION_USAGE.md)。

## Documentation

- [Development Guide](DEVELOPMENT.md) - Development guidelines and workflow
- [Note Generation Usage](docs/NOTE_GENERATION_USAGE.md) - AI note generation guide
- [CLI Usage](docs/CLI_USAGE.md) - Command-line interface documentation
- [Architecture](docs/ARCHITECTURE.md) - System architecture overview

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for development guidelines and workflow.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for detailed development roadmap and sprint planning.

See [TODO.md](TODO.md) for current task tracking and progress.

## License

[Add your license here]
