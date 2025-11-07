# OmniKnowledgeBase CLI 使用指南

## 安装

确保已安装所有依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

CLI 可以通过以下两种方式运行：

### 方式 1: 使用 Python 模块

```bash
python -m backend.app.cli [命令]
```

### 方式 2: 使用 CLI 脚本

```bash
python cli.py [命令]
```

## 命令概览

### 文档管理 (`document`)

- `document add --pdf <file>` - 添加 PDF 文档
- `document add --markdown <file>` - 添加 Markdown 文档
- `document add --url <url>` - 添加 URL 文档
- `document list` - 列出所有文档
- `document show <doc_id>` - 显示文档详情
- `document delete <doc_id>` - 删除文档
- `document search <query>` - 搜索文档
- `document chunks <doc_id>` - 查看文档块

### RAG Q&A (`rag`)

- `rag query <question>` - 单次查询
- `rag query <question> --stream` - 流式响应
- `rag interactive` - 交互式 Q&A 会话
- `rag history` - 查询历史（待实现）

### 笔记管理 (`note`)

- `note create --title <title> --content <content>` - 创建笔记
- `note list` - 列出所有笔记
- `note show <file_path>` - 显示笔记内容
- `note update <file_path>` - 更新笔记
- `note delete <file_path>` - 删除笔记
- `note links <file_path>` - 提取笔记链接
- `note vectorize <file_path>` - 向量化笔记（待实现）

### 向量存储管理 (`vector`)

- `vector collections` - 列出所有集合
- `vector stats <collection>` - 显示集合统计
- `vector delete-collection <collection>` - 删除集合
- `vector delete-document <collection> <doc_id>` - 删除文档
- `vector query <collection> <query>` - 向量查询

## 示例

### 添加文档

```bash
# 添加 PDF
python cli.py document add --pdf document.pdf

# 添加 Markdown
python cli.py document add --markdown readme.md

# 添加 URL
python cli.py document add --url https://example.com/article
```

### 查询 RAG

```bash
# 单次查询
python cli.py rag query "What is RAG?"

# 流式响应
python cli.py rag query "What is RAG?" --stream

# 交互式会话
python cli.py rag interactive
```

### 管理笔记

```bash
# 创建笔记
python cli.py note create --title "My Note" --content "# Hello\nThis is a note."

# 列出笔记
python cli.py note list

# 查看笔记
python cli.py note show my_note.md

# 提取链接
python cli.py note links my_note.md
```

### JSON 输出

大多数命令支持 `--json` 选项以 JSON 格式输出：

```bash
python cli.py document list --json
python cli.py vector collections --json
```

## 帮助信息

查看帮助信息：

```bash
python cli.py --help
python cli.py document --help
python cli.py rag --help
python cli.py note --help
python cli.py vector --help
```

