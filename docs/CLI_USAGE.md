# OmniKnowledgeBase CLI 使用指南

## 概述

`cli.py` 是 OmniKnowledgeBase 项目的命令行入口脚本，提供了统一的命令行接口用于文档处理、笔记管理、RAG Q&A 和向量存储管理。

## 安装

确保已安装所有依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

CLI 可以通过以下两种方式运行：

### 方式 1: 使用 CLI 脚本（推荐）

```bash
python cli.py [命令] [选项]
```

### 方式 2: 使用 Python 模块

```bash
python -m backend.app.cli [命令] [选项]
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
- `document find-duplicates` - 查找重复文档

### RAG Q&A (`rag`)

- `rag query <question>` - 单次查询
- `rag query <question> --stream` - 流式响应
- `rag interactive` - 交互式 Q&A 会话
- `rag agentic-query <question>` - 使用智能代理查询（LLM 工具调用）
- `rag history` - 查询历史（待实现）

### 笔记管理 (`note`)

- `note create --title <title> --content <content>` - 创建笔记
- `note list` - 列出所有笔记
- `note show <file_path>` - 显示笔记内容
- `note update <file_path>` - 更新笔记
- `note delete <file_path>` - 删除笔记
- `note links <file_path>` - 提取笔记链接
- `note search <query>` - 搜索笔记（语义搜索或标签过滤）
- `note generate <topic>` - AI 生成笔记
- `note enhance <content>` - 完善笔记内容（待实现）
- `note vectorize <file_path>` - 向量化笔记
- `note update-metadata <file_path>` - 更新笔记元数据

### 向量存储管理 (`vector`)

- `vector collections` - 列出所有集合
- `vector stats <collection>` - 显示集合统计
- `vector delete-collection <collection>` - 删除集合
- `vector delete-document <collection> <doc_id>` - 删除文档
- `vector query <collection> <query>` - 向量查询

### 索引管理 (`index`)

- `index reindex` - 重新索引所有文档和笔记
- `index clean` - 清理数据库（删除所有数据）
- `index status` - 显示索引状态

## 详细示例

### 文档管理

#### 添加文档

```bash
# 添加 PDF 文档
python cli.py document add --pdf document.pdf

# 添加 Markdown 文档
python cli.py document add --markdown readme.md

# 添加 URL 文档
python cli.py document add --url https://example.com/article

# 添加文档并指定批次 ID（用于批量导入）
python cli.py document add --pdf document.pdf --batch-id "import_2024_01"

# 添加文档时不跳过重复项
python cli.py document add --pdf document.pdf --no-skip-duplicates
```

#### 列出和查看文档

```bash
# 列出所有文档
python cli.py document list

# 列出指定批次的文档
python cli.py document list --by-batch "import_2024_01"

# 查看文档详情
python cli.py document show <doc_id>

# 查看文档的所有块
python cli.py document chunks <doc_id>

# 查找重复文档
python cli.py document find-duplicates
```

#### 搜索文档

```bash
# 语义搜索文档
python cli.py document search "机器学习基础"

# 返回更多结果
python cli.py document search "机器学习基础" --k 10

# 显示源文件信息
python cli.py document search "机器学习基础" --show-source-info

# JSON 格式输出
python cli.py document search "机器学习基础" --json
```

#### 删除文档

```bash
# 删除文档（需要确认）
python cli.py document delete <doc_id>

# 跳过确认直接删除
python cli.py document delete <doc_id> --yes
```

### RAG Q&A

#### 基本查询

```bash
# 单次查询
python cli.py rag query "什么是RAG？"

# 流式响应（实时显示）
python cli.py rag query "什么是RAG？" --stream

# 指定检索文档数量
python cli.py rag query "什么是RAG？" --k 8

# 设置相似度阈值
python cli.py rag query "什么是RAG？" --threshold 0.7

# 显示源文件信息
python cli.py rag query "什么是RAG？" --show-source-info

# JSON 格式输出
python cli.py rag query "什么是RAG？" --json
```

#### 交互式会话

```bash
# 启动交互式 Q&A 会话
python cli.py rag interactive

# 指定集合和参数
python cli.py rag interactive --collection documents --k 5
```

#### 智能代理查询

```bash
# 使用智能代理查询（LLM 自动选择工具）
python cli.py rag agentic-query "RAG和向量数据库的关系是什么？"

# 指定搜索策略
python cli.py rag agentic-query "RAG和向量数据库的关系是什么？" --strategy note-first

# 显示详细工具调用信息
python cli.py rag agentic-query "RAG和向量数据库的关系是什么？" --verbose

# 流式响应
python cli.py rag agentic-query "RAG和向量数据库的关系是什么？" --stream
```

### 笔记管理

#### 创建和查看笔记

```bash
# 创建笔记
python cli.py note create --title "我的笔记" --content "# 标题\n这是内容"

# 创建笔记并指定文件路径和标签
python cli.py note create --title "我的笔记" --content "# 标题\n这是内容" \
    --file-path "my_note.md" --tags "标签1,标签2"

# 列出所有笔记
python cli.py note list

# 列出指定子目录的笔记
python cli.py note list --subdirectory "subfolder"

# 查看笔记内容
python cli.py note show my_note.md

# 查看笔记链接
python cli.py note links my_note.md

# 通过 note_id 查看链接
python cli.py note links --from <note_id>
```

#### 更新和删除笔记

```bash
# 更新笔记内容
python cli.py note update my_note.md --content "新内容"

# 更新笔记标题
python cli.py note update my_note.md --title "新标题"

# 更新笔记标签
python cli.py note update my_note.md --tags "新标签1,新标签2"

# 删除笔记（需要确认）
python cli.py note delete my_note.md

# 跳过确认直接删除
python cli.py note delete my_note.md --yes
```

#### 搜索笔记

```bash
# 语义搜索笔记
python cli.py note search "机器学习"

# 按标签过滤
python cli.py note search --tag "AI"

# 组合搜索（语义 + 标签）
python cli.py note search "深度学习" --tag "AI"

# 限制结果数量
python cli.py note search "机器学习" --limit 5

# JSON 格式输出
python cli.py note search "机器学习" --json
```

#### AI 生成笔记

```bash
# 使用 RAG 模式生成笔记（默认）
python cli.py note generate "什么是RAG？"

# 使用 LLM 知识模式生成笔记
python cli.py note generate "Python基础语法" --mode new

# 生成并立即保存
python cli.py note generate "机器学习基础" --mode ask --save --tags "AI,ML"

# 指定文件路径和风格
python cli.py note generate "RAG评估指标" --mode ask \
    --file-path "rag_evaluation.md" \
    --tags "RAG,评估" \
    --style "使用简洁的语言，包含代码示例"

# JSON 格式输出
python cli.py note generate "向量数据库" --mode ask --json
```

#### 向量化和元数据

```bash
# 向量化单个笔记
python cli.py note vectorize my_note.md

# 强制重新向量化
python cli.py note vectorize my_note.md --force

# 向量化所有笔记
python cli.py note vectorize --all

# 增量向量化（只处理新笔记）
python cli.py note vectorize --all --incremental

# 更新单个笔记的元数据
python cli.py note update-metadata my_note.md

# 批量更新所有笔记的元数据
python cli.py note update-metadata --all
```

### 向量存储管理

```bash
# 列出所有集合
python cli.py vector collections

# 查看集合统计信息
python cli.py vector stats documents

# 查询向量集合
python cli.py vector query documents "机器学习"

# 返回更多结果
python cli.py vector query documents "机器学习" --k 10

# 删除集合（需要确认）
python cli.py vector delete-collection old_collection

# 删除集合中的文档
python cli.py vector delete-document documents <doc_id>

# JSON 格式输出
python cli.py vector collections --json
```

### 索引管理

#### 重新索引

```bash
# 重新索引所有文档和笔记（需要确认）
python cli.py index reindex

# 只重新索引文档
python cli.py index reindex --documents

# 只重新索引笔记
python cli.py index reindex --notes

# 跳过确认
python cli.py index reindex --yes
```

#### 清理数据库

```bash
# 清理 ChromaDB（需要确认）
python cli.py index clean --chromadb

# 清理 SQLite（需要确认）
python cli.py index clean --sqlite

# 清理所有数据库（需要确认）
python cli.py index clean --all

# 跳过确认
python cli.py index clean --all --yes
```

#### 查看索引状态

```bash
# 显示索引状态
python cli.py index status
```

## 常用选项

### JSON 输出

大多数命令支持 `--json` 选项以 JSON 格式输出，便于脚本处理：

```bash
python cli.py document list --json
python cli.py vector collections --json
python cli.py note search "查询" --json
```

### 跳过确认

删除操作通常需要确认，可以使用 `--yes` 跳过：

```bash
python cli.py document delete <doc_id> --yes
python cli.py note delete <file_path> --yes
python cli.py vector delete-collection <collection> --yes
```

## 帮助信息

查看帮助信息：

```bash
# 主帮助
python cli.py --help

# 命令组帮助
python cli.py document --help
python cli.py rag --help
python cli.py note --help
python cli.py vector --help
python cli.py index --help

# 具体命令帮助
python cli.py document add --help
python cli.py rag query --help
python cli.py note generate --help
```

## 版本信息

查看 CLI 版本：

```bash
python cli.py --version
```

