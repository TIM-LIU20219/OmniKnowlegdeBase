# 笔记生成功能使用指南

本文档介绍如何在CLI和前端中使用不同的笔记生成模式。

## 概述

笔记生成功能支持三种模式：

1. **`/new` 模式**：使用LLM自身知识生成笔记，不进行RAG检索
2. **`/ask` 模式**：先进行RAG检索，然后基于检索结果生成笔记（默认）
3. **`/enhance` 模式**：完善已有笔记内容（待实现）

## CLI使用方式

### 基本语法

```bash
python cli.py note generate <topic> [options]
```

### 模式选择

使用 `--mode` 参数选择生成模式：

```bash
# 使用RAG检索模式（默认）
python cli.py note generate "什么是RAG？"

# 使用LLM知识模式
python cli.py note generate "Python基础语法" --mode new

# 使用RAG模式（显式指定）
python cli.py note generate "机器学习基础" --mode ask
```

### 常用选项

```bash
# 生成并立即保存
python cli.py note generate "深度学习入门" --mode ask --save

# 指定文件路径和标签
python cli.py note generate "RAG评估指标" --mode ask \
    --file-path "rag_evaluation.md" \
    --tags "RAG,评估,指标"

# 添加风格指令
python cli.py note generate "Python装饰器" --mode new \
    --style "使用简洁的语言，包含代码示例"

# JSON格式输出
python cli.py note generate "向量数据库" --mode ask --json
```

### 完整示例

```bash
# 示例1：使用RAG检索生成关于RAG的笔记
python cli.py note generate "什么是RAG？" --mode ask --save --tags "RAG,AI"

# 示例2：使用LLM知识生成Python基础笔记
python cli.py note generate "Python列表和字典" --mode new \
    --file-path "python_basics.md" \
    --tags "Python,编程基础"

# 示例3：生成并查看结果（不保存）
python cli.py note generate "机器学习算法" --mode ask
```

### 输出说明

CLI会显示以下信息：

- **Mode**: 使用的生成模式（/new 或 /ask）
- **Title**: 生成的笔记标题
- **Content length**: 内容字符数
- **Similarity suggestions**: 相似笔记建议（Markdown注释格式）
- **Similar notes found**: 找到的相似笔记数量
- **Links added**: 自动添加的Obsidian链接
- **RAG sources**: RAG检索的来源（仅/ask模式）
- **Content preview**: 内容预览（前500字符）

## 前端使用方式

### 访问笔记生成功能

1. 启动前端应用：
   ```bash
   cd frontend
   streamlit run app.py
   ```

2. 导航到 **📝 Notes** 页面

3. 在侧边栏中，切换到 **🤖 Generate** 标签页

### 使用步骤

1. **选择生成模式**
   - `ask`: 使用RAG检索（推荐，默认）
   - `new`: 使用LLM自身知识

2. **输入主题/问题**
   - 在 "Topic/Question" 文本框中输入要生成笔记的主题或问题
   - 例如："什么是RAG？"、"Python装饰器详解"

3. **可选设置**
   - **File path**: 指定保存路径（可选）
   - **Tags**: 输入标签，用逗号分隔（可选）
   - **Style instructions**: 添加风格指令（可选）

4. **生成笔记**
   - 点击 **Generate** 按钮：生成笔记并预览，可手动保存
   - 点击 **Generate & Save** 按钮：生成并立即保存

### 前端功能说明

#### Generate按钮（预览模式）

点击后会在侧边栏显示：

- **Generated Note Preview**: 生成的笔记预览
- **Similarity Suggestions**: 相似笔记建议（可展开查看）
- **Similar notes found**: 找到的相似笔记列表
- **Links added**: 自动添加的链接
- **RAG sources**: RAG检索来源（仅ask模式）
- **Generated Content**: 完整内容（可展开查看）
- **Save Generated Note**: 保存按钮

#### Generate & Save按钮（直接保存）

点击后：

- 立即生成笔记
- 自动保存到文件系统
- 显示成功消息
- 自动刷新笔记列表

### 前端示例

**示例1：使用RAG模式生成笔记**

1. 选择模式：`ask`
2. 输入主题：`什么是RAG？`
3. 添加标签：`RAG,AI,检索`
4. 点击 **Generate & Save**

**示例2：使用LLM知识模式生成笔记**

1. 选择模式：`new`
2. 输入主题：`Python装饰器详解`
3. 添加风格指令：`使用简洁的语言，包含代码示例`
4. 点击 **Generate** 预览
5. 查看预览后，点击 **Save Generated Note** 保存

## API使用方式

### 直接调用API

#### 生成笔记（不保存）

```python
import requests

# /new 模式
response = requests.post(
    "http://localhost:8000/api/notes/generate",
    json={
        "topic": "/new Python基础语法",
        "tags": ["Python", "编程"],
        "style": "使用简洁的语言"
    }
)

# /ask 模式
response = requests.post(
    "http://localhost:8000/api/notes/generate",
    json={
        "topic": "/ask 什么是RAG？",
        "tags": ["RAG", "AI"]
    }
)
```

#### 生成并保存

```python
response = requests.post(
    "http://localhost:8000/api/notes/generate-and-save",
    json={
        "topic": "/ask 机器学习基础",
        "file_path": "ml_basics.md",
        "tags": ["ML", "AI"]
    }
)
```

#### 完善笔记（待实现）

```python
response = requests.post(
    "http://localhost:8000/api/notes/enhance",
    json={
        "content": "现有笔记内容...",
        "instruction": "添加更多细节和示例"
    }
)
```

## 模式对比

| 特性 | `/new` 模式 | `/ask` 模式 |
|------|------------|------------|
| **信息检索** | ❌ 不使用RAG | ✅ 使用RAG检索 |
| **知识来源** | LLM自身知识 | RAG检索结果 + LLM知识 |
| **适用场景** | 通用知识、概念解释 | 需要参考已有文档/笔记 |
| **生成速度** | 较快 | 较慢（需要检索） |
| **准确性** | 依赖LLM知识 | 基于实际文档内容 |
| **来源引用** | ❌ 无 | ✅ 包含来源信息 |
| **相似性检阅** | ✅ 有 | ✅ 有 |
| **自动链接** | ✅ 有 | ✅ 有 |

## 使用建议

### 何时使用 `/new` 模式

- 生成通用知识笔记（如编程概念、算法原理）
- LLM已有足够知识回答的问题
- 需要快速生成，不依赖外部文档
- 生成原创性内容

**示例**：
- "Python装饰器详解"
- "机器学习基础概念"
- "数据结构与算法"

### 何时使用 `/ask` 模式

- 需要参考已有文档或笔记
- 问题涉及特定领域知识
- 需要引用具体来源
- 希望基于实际内容生成

**示例**：
- "什么是RAG？"（如果已有RAG相关文档）
- "如何实现向量检索？"（如果已有相关代码/文档）
- "RAG评估指标有哪些？"（如果已有评估文档）

## 常见问题

### Q: 如何知道应该使用哪种模式？

A: 
- 如果问题涉及通用知识，使用 `/new` 模式
- 如果需要参考已有文档，使用 `/ask` 模式
- 如果不确定，先尝试 `/ask` 模式，它会自动检索相关信息

### Q: 生成的笔记在哪里？

A: 
- CLI使用 `--save` 选项时，笔记会保存到 `notes/` 目录
- 前端使用 "Generate & Save" 时，笔记会保存到 `notes/` 目录
- 可以通过 `python cli.py note list` 查看所有笔记

### Q: 如何修改生成的笔记？

A: 
- 前端：在 "Note List" 标签页中选择笔记，在 "Edit Mode" 中修改
- CLI：使用 `python cli.py note update <file_path> --content "新内容"`

### Q: 相似性建议是什么？

A: 
- 系统会自动搜索相似的已有笔记
- 生成建议注释，提示你参考哪些笔记
- 建议以Markdown注释格式显示，不会影响笔记内容

### Q: 自动链接是如何工作的？

A: 
- 系统会识别笔记中的关键概念
- 自动匹配已有笔记标题
- 添加 `[[note-name]]` 格式的Obsidian链接
- 可以在 "Links" 标签页查看链接关系

## 技术细节

### 工作流程

#### `/new` 模式流程

```
用户输入: /new <主题>
    ↓
[阶段1: 笔记生成]
使用LLM自身知识生成初稿
    ↓
[阶段2: 相似性检阅]
搜索相似笔记，生成建议
    ↓
[阶段3: 链接建立]
识别概念，添加Obsidian链接
    ↓
返回结果
```

#### `/ask` 模式流程

```
用户输入: /ask <问题>
    ↓
[阶段1: RAG检索]
使用AgenticRAGService检索相关信息
    ↓
[阶段2: 笔记生成]
基于检索结果生成初稿
    ↓
[阶段3: 相似性检阅]
搜索相似笔记，生成建议
    ↓
[阶段4: 链接建立]
识别概念，添加Obsidian链接
    ↓
返回结果（包含来源信息）
```

### API响应格式

```json
{
    "mode": "/ask",
    "title": "笔记标题",
    "content": "笔记内容（含链接）",
    "suggestions": "相似性建议（注释格式）",
    "similar_notes": [
        {
            "title": "相似笔记标题",
            "file_path": "path/to/note.md",
            "similarity": 0.85
        }
    ],
    "added_links": ["笔记1", "笔记2"],
    "sources": [
        {
            "title": "来源标题",
            "type": "note",
            "file_path": "path/to/source.md"
        }
    ],
    "rag_context": "检索上下文摘要",
    "file_path": "path/to/note.md",
    "tags": ["tag1", "tag2"]
}
```

## 相关文档

- [API文档](../docs/API.md)
- [CLI使用文档](../docs/CLI_USAGE.md)
- [架构文档](../docs/ARCHITECTURE.md)

