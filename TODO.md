# 后端开发任务清单（命令行优先）

> **项目目标**：
>
> 1. 迭代优化 RAG 效果
> 2. 更好的 Q&A 与笔记管理
> 3. 更好的多模态输入能力（参考 Crawl4AI）
>
> **开发原则**：所有功能优先在命令行中用纯后端方式实现

---

## 📊 当前状态概览

### ✅ 已完成的后端服务（95%）

- ✅ **核心基础设施**：向量存储、嵌入服务、文件系统工具
- ✅ **文档处理**：PDF/Markdown/URL 解析、分块、向量化
- ✅ **笔记管理**：CRUD、Frontmatter、链接提取
- ✅ **RAG Pipeline**：检索、生成、流式响应
- ✅ **评估系统**：Benchmark 评估、指标计算

### ⚠️ 缺失的功能

- ✅ **统一 CLI 工具**：已完成 Phase 1
- 🔄 **文档管理机制完善**：元数据增强、去重、智能存储（Sprint 2.1.5，进行中）
- 🚀 **Agentic Search与笔记检索体系**：结构化信息存储、智能检索流程（最高优先级）
- ⏳ **RAG 优化**：混合检索、查询扩展、重排序等（优先级降低，待Agentic Search完成后）
- ⏳ **多模态输入**：Crawl4AI 集成、增强网页读取（中优先级）
- ⏳ **测试与优化**：单元测试、集成测试、性能优化（优先级降低）

---

## 🎯 Phase 1: 统一 CLI 工具（优先级：最高）

> **目标**：为所有后端功能提供统一的命令行接口，确保可以通过 CLI 完成所有操作

### Sprint 1.1: CLI 框架搭建 ✅

- [x] 选择 CLI 框架（推荐 `click`）
- [x] 创建统一 CLI 入口 (`backend/app/cli/__main__.py`)
- [x] 设计 CLI 命令结构
- [x] 实现基础 CLI 工具（帮助、版本等）

### Sprint 1.2: 文档管理 CLI ✅

- [x] 文档上传命令
  - [x] `cli document add --pdf <file>`
  - [x] `cli document add --markdown <file>`
  - [x] `cli document add --url <url>`
- [x] 文档列表命令 (`cli document list`)
- [x] 文档详情命令 (`cli document show <doc_id>`)
- [x] 文档删除命令 (`cli document delete <doc_id>`)
- [x] 文档搜索命令 (`cli document search <query>`)
- [x] 文档块查看命令 (`cli document chunks <doc_id>`)

### Sprint 1.3: RAG Q&A CLI ✅

- [x] 单次查询命令 (`cli rag query <question>`)
- [x] 交互式 Q&A 模式 (`cli rag interactive`)
- [x] 流式响应支持 (`cli rag query --stream`)
- [x] 查询历史记录 (`cli rag history`) - 占位符（待实现）
- [x] 查询配置选项 (`--collection`, `--k`, `--threshold`)

### Sprint 1.4: 笔记管理 CLI ✅

- [x] 笔记创建命令 (`cli note create --title <title> --content <content>`)
- [x] 笔记列表命令 (`cli note list`)
- [x] 笔记读取命令 (`cli note show <file_path>`)
- [x] 笔记更新命令 (`cli note update <file_path>`)
- [x] 笔记删除命令 (`cli note delete <file_path>`)
- [x] 笔记链接提取 (`cli note links <file_path>`)
- [x] 笔记向量化命令 (`cli note vectorize <file_path>`) - 占位符（待实现）

### Sprint 1.5: 向量存储管理 CLI ✅

- [x] 集合列表 (`cli vector collections`)
- [x] 集合统计 (`cli vector stats <collection>`)
- [x] 集合删除 (`cli vector delete-collection <collection>`)
- [x] 文档删除 (`cli vector delete-document <collection> <doc_id>`)
- [x] 向量查询 (`cli vector query <collection> <query>`)
- [x] 向量服务维度检查工具 (`backend/app/utils/check_embedding_dim.py`)

---

## 🚀 Phase 2.5: Agentic Search与笔记检索体系（优先级：最高）

> **目标**：实现基于Agentic Search的智能检索系统，支持结构化笔记的精确查询和文本内容的向量检索，LLM可以自主选择检索策略

### Sprint 2.5.1: 数据结构分离 ✅

- [x] **创建结构化信息存储服务** ✅
  - [x] 创建 `backend/app/services/note_metadata_service.py`
  - [x] SQLite数据库初始化（`backend/app/db/notes.db`）
  - [x] 笔记元数据表设计：note_id, title, file_path, tags, links, frontmatter, created_at, updated_at
  - [x] 笔记链接关系表设计：source_note_id, target_note_id（支持双向链接查询）
  - [x] 标签索引表设计：tag, note_id（支持按标签查询）
  - [x] 实现笔记元数据CRUD操作
  - [x] 实现 `get_notes_by_tag(tag: str) -> List[NoteMetadata]`
  - [x] 实现 `get_linked_notes(note_id: str) -> List[NoteMetadata]`
  - [x] 实现 `get_backlinks(note_id: str) -> List[NoteMetadata]`

- [x] **修改文档处理逻辑** ✅
  - [x] 修改 `backend/app/services/document_service.py` 的 `_process_and_store()` 方法
  - [x] 提取结构化信息（tags, links, frontmatter）
  - [x] 存储到SQLite（通过note_metadata_service）
  - [x] 只对纯文本内容生成embedding
  - [x] 清理markdown语法（移除`[[links]]`、`#tags`等）后再生成embedding

- [x] **创建文本清理服务** ✅
  - [x] 扩展 `backend/app/utils/text_cleaner.py`
  - [x] 实现 `clean_for_embedding(content: str) -> str`：移除结构化标记，保留纯文本
  - [x] 移除`[[links]]`、`#tags`、frontmatter等
  - [x] 保留标题层级（`#`）作为文本内容的一部分
  - [x] 移除Obsidian链接但保留链接文本：`[[note-name]]` → `note-name`

### Sprint 2.5.2: Agentic Search框架

- [ ] **创建工具定义**
  - [ ] 创建 `backend/app/services/agent_tools.py`
  - [ ] 定义工具列表：
    - [ ] `search_notes_by_title(query: str, limit: int) -> List[NoteMetadata]`：通过标题embedding搜索笔记
    - [ ] `get_note_metadata(note_id: str) -> NoteMetadata`：获取笔记的tags和links
    - [ ] `get_notes_by_tag(tag: str) -> List[NoteMetadata]`：按标签查询笔记
    - [ ] `get_linked_notes(note_id: str) -> List[NoteMetadata]`：获取链接的笔记
    - [ ] `read_note_content(note_id: str) -> str`：读取笔记完整内容
    - [ ] `search_pdf_chunks(query: str, limit: int) -> List[Document]`：搜索PDF文档块
    - [ ] `search_web(query: str) -> str`：网络搜索（可选，需要API）
  - [ ] 工具转换为OpenAI function calling格式

- [ ] **创建Agentic Search服务**
  - [ ] 创建 `backend/app/services/agentic_search_service.py`
  - [ ] 使用LangChain的Agent框架或自定义ReAct模式
  - [ ] LLM可以调用工具进行多步骤检索
  - [ ] 实现检索策略决策逻辑

- [ ] **实现检索策略**
  - [ ] 创建 `backend/app/services/search_strategy.py`
  - [ ] **笔记优先策略**：先搜索笔记标题，找到相关笔记后读取tags/links
  - [ ] **链接扩展策略**：根据links读取相关笔记
  - [ ] **标签过滤策略**：如果用户提到特定tag，使用标签查询
  - [ ] **回退策略**：如果笔记中找不到，搜索PDF或网络

### Sprint 2.5.3: LLM工具调用集成

- [ ] **扩展LLMService支持Function Calling**
  - [ ] 修改 `backend/app/services/llm_service.py`
  - [ ] 支持OpenAI格式的function calling
  - [ ] 工具定义转换为function schema
  - [ ] 解析LLM的工具调用请求

- [ ] **创建Agent执行器**
  - [ ] 创建 `backend/app/services/agent_executor.py`
  - [ ] 执行LLM的工具调用
  - [ ] 管理多轮对话和工具调用循环
  - [ ] 限制最大工具调用次数（防止无限循环）

### Sprint 2.5.4: 集成到RAG服务

- [ ] **创建新的AgenticRAGService**
  - [ ] 创建 `backend/app/services/agentic_rag_service.py`
  - [ ] 替代或扩展现有的RAGService
  - [ ] 使用Agentic Search进行检索
  - [ ] 支持流式响应

- [ ] **更新CLI接口**
  - [ ] 添加agentic search端点 (`cli rag agentic-query <question>`)
  - [ ] 支持工具调用结果的展示
  - [ ] 支持检索策略选择 (`--strategy note-first|pdf-first|hybrid`)

### Sprint 2.5.5: 笔记向量化流程

- [ ] **笔记专用向量化服务**
  - [ ] 修改笔记处理流程，分离结构化信息和文本内容
  - [ ] 实现笔记批量向量化 (`cli note vectorize --all`)
  - [ ] 实现笔记增量向量化（仅向量化新笔记）
  - [ ] 确保结构化信息存储到SQLite，文本内容存储到ChromaDB

- [ ] **笔记检索CLI**
  - [ ] 实现笔记语义搜索 (`cli note search <query>`)
  - [ ] 实现按标签查询 (`cli note search --tag <tag>`)
  - [ ] 实现链接关系查询 (`cli note links --from <note_id>`)

---

## 🔍 Phase 3: RAG 效果优化（优先级：中，待Agentic Search完成后）

> **目标**：迭代优化 RAG 效果，提升检索和生成质量

### Sprint 3.1: 基础测评与基准建立（优先级降低）

- [ ] **PDF 教材接入**
  - [ ] 准备 31 页 PDF 教材
  - [ ] 创建 PDF 处理脚本 (`cli document add --pdf textbook.pdf`)
  - [ ] 验证文档完整导入（检查块数量、向量化状态）
  - [ ] 创建初始 Benchmark 数据集（基于教材内容）
- [ ] **基准测试**
  - [ ] 运行初始评估 (`cli benchmark run --dataset textbook_benchmark.json`)
  - [ ] 记录基线指标（Precision/Recall/F1、答案相似度）
  - [ ] 分析检索和生成的薄弱环节

### Sprint 2.1.5: 文档管理机制完善（优先级：最高）

> **目标**：完善文档管理机制，利用元数据避免重复添加，并为检索阶段提供帮助信息

- [x] **元数据模型增强** ✅
  - [x] 扩展 `DocumentMetadata` 模型，添加以下字段：
    - [x] `original_path`: 原始文件路径（resources文件夹中的相对路径）
    - [x] `file_hash`: 文件内容SHA256哈希（用于去重）
    - [x] `file_size`: 文件大小（字节）
    - [x] `file_mtime`: 文件修改时间（ISO格式）
    - [x] `storage_path`: 文件存储路径（documents文件夹或原始位置）
    - [x] `import_batch`: 导入批次标识符（用于跟踪导入组）
  - [x] 更新 `to_chromadb_metadata()` 方法支持新字段
  - [x] 更新 `from_chromadb_metadata()` 方法支持新字段
- [x] **文件哈希工具** ✅
  - [x] 创建 `backend/app/utils/file_hash.py`
  - [x] 实现 `calculate_file_hash()` 函数（SHA256）
  - [x] 实现 `get_file_metadata()` 函数（文件大小、修改时间）
  - [ ] 添加单元测试（待补充）
- [x] **去重检查服务** ✅
  - [x] 在 `DocumentService` 中实现 `_check_duplicate()` 方法
    - [x] 基于文件hash查询已存在的文档
    - [x] 返回已存在的 `DocumentMetadata` 或 `None`
  - [x] 实现 `_should_copy_file()` 方法
    - [x] 判断文件是否在resources文件夹中
    - [x] resources文件夹中的文件不复制，只保存引用
    - [x] 临时上传的文件复制到documents文件夹
  - [x] 创建 `DuplicateDocumentError` 异常类
- [x] **文档处理流程改进** ✅
  - [x] 修改 `process_and_store_pdf()` 方法：
    - [x] 计算文件hash和元数据
    - [x] 检查重复文档（可选，通过参数控制）
    - [x] 实现智能存储策略（resources文件不复制）
    - [x] 增强元数据（添加所有新字段）
    - [x] 支持 `skip_duplicates` 参数
    - [x] 支持 `import_batch` 参数
  - [x] 修改 `process_and_store_markdown()` 方法（类似增强）
  - [x] 修改 `process_and_store_url()` 方法（支持 `import_batch` 参数，URL无需文件哈希）
  - [x] 更新导入脚本 `import_pdfs.py`：
    - [x] 添加 `--skip-duplicates` 选项
    - [x] 添加 `--batch-id` 选项
    - [x] 显示重复文档警告信息
- [x] **检索阶段增强** ✅
  - [x] 在 `ChromaDBRetriever` 中实现 `retrieve_with_context()` 方法
    - [x] 返回增强的检索结果，包含源文件信息
    - [x] 包含 `original_path`、`storage_path`、`file_size`、`import_batch` 等
  - [ ] 更新 `RAGService` 使用增强的检索结果（待验证）
  - [x] 添加 CLI 命令选项：
    - [x] `cli rag query --show-source-info` 显示源文件信息
    - [x] `cli document list --by-batch <batch_id>` 按批次列出文档
    - [x] `cli document find-duplicates` 查找重复文档
- [ ] **测试与验证**
  - [ ] 测试文件hash计算准确性
  - [ ] 测试去重检查功能（相同文件、不同文件名）
  - [ ] 测试智能存储策略（resources文件不复制）
  - [ ] 测试元数据完整性（所有字段正确存储和读取）
  - [ ] 测试检索结果中的源文件信息
  - [ ] 测试批量导入的去重功能
- [ ] **文档更新**
  - [ ] 更新架构文档说明新的元数据字段
  - [ ] 更新CLI文档说明去重选项
  - [ ] 添加文档管理最佳实践指南

### Sprint 3.2: 检索优化

- [ ] **混合检索**
  - [ ] 实现关键词检索（BM25 或 TF-IDF）
  - [ ] 实现向量+关键词混合检索策略
  - [ ] 添加混合检索 CLI (`cli rag query --hybrid`)
  - [ ] 对比纯向量检索 vs 混合检索效果
- [ ] **查询扩展**
  - [ ] 实现查询重写（基于 LLM）
  - [ ] 实现同义词扩展
  - [ ] 添加查询扩展 CLI 选项 (`cli rag query --expand`)
- [ ] **重排序（Reranking）**
  - [ ] 集成重排序模型（如 CrossEncoder）
  - [ ] 实现检索结果重排序
  - [ ] 添加重排序 CLI 选项 (`cli rag query --rerank`)

### Sprint 3.3: 上下文优化

- [ ] **上下文压缩**
  - [ ] 实现基于重要性的上下文压缩
  - [ ] 实现基于长度的上下文截断
- [ ] **相关性过滤**
  - [ ] 实现基于相似度阈值的过滤
  - [ ] 实现基于元数据的过滤
- [ ] **动态上下文长度**
  - [ ] 根据问题复杂度动态调整上下文长度
  - [ ] 根据 LLM 模型限制调整上下文

### Sprint 3.4: Prompt 优化

- [ ] **Prompt 模板管理**
  - [ ] 实现 Prompt 模板系统
  - [ ] 支持多模板切换 (`cli rag query --prompt-template <name>`)
  - [ ] 创建针对不同场景的 Prompt 模板
- [ ] **Prompt 优化实验**
  - [ ] A/B 测试不同 Prompt 模板
  - [ ] 记录不同模板的效果指标
  - [ ] 选择最优 Prompt 模板

### Sprint 3.5: 评估与迭代

- [ ] **扩展 Benchmark 数据集**
  - [ ] 基于 PDF 教材创建更多测试问题
  - [ ] 添加不同难度级别的问题
  - [ ] 添加不同类型的问题（事实性、推理性、总结性）
- [ ] **自动化评估流程**
  - [ ] 实现定期评估脚本
  - [ ] 实现评估结果对比工具 (`cli benchmark compare <result1> <result2>`)
  - [ ] 实现评估报告生成 (`cli benchmark report <results>`)
- [ ] **性能监控**
  - [ ] 实现检索延迟监控
  - [ ] 实现生成质量监控
  - [ ] 实现错误率统计

---

## 📝 Phase 4: Q&A 与笔记管理增强（优先级：中）

> **目标**：提升 Q&A 体验和笔记管理能力

### Sprint 4.1: 对话管理

- [ ] **多轮对话支持**
  - [ ] 实现对话上下文管理
  - [ ] 实现对话历史存储
  - [ ] 添加对话 CLI (`cli rag chat <session_id>`)
- [ ] **对话历史管理**
  - [ ] 实现对话历史查询 (`cli rag history list`)
  - [ ] 实现对话历史删除 (`cli rag history delete <session_id>`)
  - [ ] 实现对话导出 (`cli rag history export <session_id>`)

### Sprint 4.2: 笔记链接管理（部分功能已在Phase 2.5实现）

- [ ] **双向链接追踪**
  - [ ] 实现反向链接扫描（扫描所有笔记）
  - [ ] 实现链接图构建 (`cli note graph`)
  - [ ] 实现链接统计 (`cli note links --stats`)
- [ ] **笔记关系分析**
  - [ ] 实现笔记聚类分析
  - [ ] 实现笔记主题提取
  - [ ] 实现笔记推荐 (`cli note recommend <file_path>`)

### Sprint 4.3: AI 笔记生成

- [ ] **笔记生成服务**
  - [ ] 实现基于 RAG 的笔记生成服务
  - [ ] 设计笔记生成 Prompt 模板
  - [ ] 实现笔记格式化（Obsidian 格式）
- [ ] **笔记生成 CLI**
  - [ ] 实现笔记生成命令 (`cli note generate --topic <topic>`)
  - [ ] 实现基于文档的笔记生成 (`cli note generate --from-doc <doc_id>`)
  - [ ] 实现笔记自动向量化

---

## 🌐 Phase 5: 多模态输入增强（优先级：中）

> **目标**：集成 Crawl4AI，增强网页读取能力

### Sprint 5.1: Crawl4AI 集成

- [ ] **Crawl4AI 集成研究**
  - [ ] 研究 Crawl4AI 功能和 API
  - [ ] 评估与现有 URL 处理器的集成方案
  - [ ] 设计集成架构
- [ ] **Crawl4AI 服务实现**
  - [ ] 安装和配置 Crawl4AI
  - [ ] 创建 Crawl4AI 服务 (`Crawl4AIService`)
  - [ ] 实现网页内容提取（文本、图片、表格等）
  - [ ] 实现 JavaScript 渲染支持
- [ ] **URL 处理器增强**
  - [ ] 集成 Crawl4AI 到现有 URL 处理器
  - [ ] 实现智能内容提取（去除广告、导航等）
  - [ ] 实现多模态内容处理（文本+图片+表格）

### Sprint 5.2: 多模态内容处理

- [ ] **图片处理**
  - [ ] 实现图片 OCR（文字提取）
  - [ ] 实现图片描述生成（基于 Vision API）
  - [ ] 实现图片元数据提取
- [ ] **表格处理**
  - [ ] 实现表格结构化提取
  - [ ] 实现表格转 Markdown
  - [ ] 实现表格向量化
- [ ] **多模态内容向量化**
  - [ ] 实现文本+图片混合向量化
  - [ ] 实现多模态检索支持

### Sprint 5.3: 多模态 CLI

- [ ] **URL 处理 CLI 增强**
  - [ ] 更新 `cli document add --url` 支持 Crawl4AI
  - [ ] 添加多模态选项 (`cli document add --url <url> --multimodal`)
  - [ ] 添加图片处理选项 (`cli document add --url <url> --extract-images`)
- [ ] **多模态内容查看**
  - [ ] 实现多模态内容预览 (`cli document show --multimodal <doc_id>`)
  - [ ] 实现图片查看 (`cli document images <doc_id>`)
  - [ ] 实现表格查看 (`cli document tables <doc_id>`)

---

## 🧪 Phase 6: 测试与优化（优先级：低）

### Sprint 6.1: 单元测试

- [ ] 文档处理服务测试
- [ ] 笔记管理服务测试
- [ ] RAG 服务测试
- [ ] CLI 命令测试
- [ ] 测试覆盖率 ≥ 70%

### Sprint 6.2: 集成测试

- [ ] 端到端文档处理流程测试
- [ ] RAG Pipeline 集成测试
- [ ] CLI 集成测试
- [ ] 性能测试

### Sprint 6.3: 性能优化

- [ ] 向量检索优化
- [ ] 批量处理优化
- [ ] 缓存机制实现
- [ ] 异步处理优化

---

## 📚 Phase 7: 文档与工具（优先级：低）

### Sprint 7.1: CLI 文档

- [ ] CLI 使用手册
- [ ] CLI 命令参考
- [ ] CLI 示例脚本
- [ ] CLI 最佳实践

### Sprint 7.2: 开发文档

- [ ] API 文档更新
- [ ] 架构文档更新
- [ ] 贡献指南
- [ ] 故障排查指南

---

## 🎯 里程碑追踪

### Milestone 1: CLI 工具完备（Phase 1 完成）✅

- [x] 所有核心功能都有 CLI 接口
- [x] 可以通过 CLI 完成所有操作
- [ ] CLI 文档完善（待补充使用说明）

### Milestone 2: Agentic Search与笔记检索体系（Phase 2.5 完成）

- [ ] 结构化信息存储（SQLite）完成
- [ ] 文本内容与结构化信息分离
- [ ] Agentic Search框架实现
- [ ] LLM工具调用集成完成
- [ ] 笔记优先检索策略可用

### Milestone 3: RAG 效果优化（Phase 3 完成，优先级降低）

- [ ] PDF 教材成功接入并测评
- [ ] RAG 效果相比基线提升 ≥ 20%
- [ ] Benchmark 评估流程完善

### Milestone 4: Q&A 与笔记管理增强（Phase 4 完成）

- [ ] 多轮对话支持
- [ ] AI 笔记生成可用

### Milestone 5: 多模态输入（Phase 5 完成）

- [ ] Crawl4AI 集成完成
- [ ] 多模态内容处理可用
- [ ] 网页读取质量显著提升

---

## 📝 开发原则

1. **命令行优先**：所有功能首先在 CLI 中实现，确保可以通过命令行完成所有操作
2. **后端优先**：专注于后端服务层，前端界面后续补充
3. **迭代优化**：基于实际使用和测评结果持续优化 RAG 效果
4. **测试驱动**：重要功能都要有测试和 Benchmark
5. **文档同步**：代码变更时同步更新文档

---

## 🔄 当前重点任务

### 立即开始（本周）

1. **Phase 2.1.5**: 完成文档管理机制完善的测试与验证
2. **Phase 2.5**: Agentic Search与笔记检索体系（最高优先级）
   - Sprint 2.5.1: 数据结构分离（SQLite + ChromaDB）
   - Sprint 2.5.2: Agentic Search框架搭建

### 近期计划（2-4 周）

1. **Phase 2.5**: 完成Agentic Search核心功能
   - 结构化信息存储服务
   - 文本清理与embedding分离
   - Agent工具定义与执行器
   - AgenticRAGService集成
2. **Phase 2.5.5**: 笔记向量化流程完善
3. **Phase 3**: RAG效果优化（优先级降低，待Agentic Search完成后）
4. **Phase 4**: 对话管理实现

---

## 📌 注意事项

- 每个任务完成后更新此文件
- 遇到阻塞问题及时记录
- 定期回顾和调整优先级
- 遵循项目规范（文件长度、代码风格、提交规范）
- **重点关注**：
  - **Agentic Search与笔记检索体系（Phase 2.5）**：最高优先级，核心功能
  - **文档管理机制完善（Sprint 2.1.5）**：基础功能，需完成测试验证
  - RAG 效果优化：优先级降低，待Agentic Search完成后进行
  - CLI 工具完善

---

## 📋 已完成功能记录（参考）

### Phase 0: 项目基础搭建 ✅

- [x] ChromaDB 配置
- [x] 向量存储服务
- [x] 文件系统工具
- [x] 日志配置
- [x] LLM 配置

### Phase 1: 核心基础设施 ✅

- [x] ChromaDB 配置模块
- [x] 向量存储服务封装
- [x] 文件系统工具
- [x] 笔记文件管理服务
- [x] 元数据模型定义（Pydantic）

### Phase 2: 文档处理模块 ✅（后端）

- [x] Markdown 解析器
- [x] PDF 解析器
- [x] URL 抓取器
- [x] 元数据提取
- [x] 文档分块服务
- [x] 文档向量化服务

### Phase 3: 笔记管理模块 ✅（后端）

- [x] 笔记文件服务
- [x] Markdown 链接解析器
- [x] 文件夹结构支持
- [x] Frontmatter 解析

### Phase 4: RAG 问答系统 ✅（后端）

- [x] RAG 服务
- [x] 检索器实现（ChromaDB）
- [x] 上下文窗口管理
- [x] LLM 集成（LangChain）
- [x] 流式响应支持
- [x] Benchmark 评估系统

---

## 🔄 架构变更记录

### 2024-01-XX: 架构调整 - 后端优先

- ✅ 移除 Streamlit 前端开发优先级
- ✅ 专注于命令行接口开发
- ✅ 强调 RAG 效果迭代优化
- ✅ 新增 Crawl4AI 集成计划
- ✅ 新增 PDF 教材测评任务

### 2024-01-XX: 文档管理机制完善（Sprint 2.1.5）

- ✅ 新增文档管理机制完善任务（插入到Sprint 2.1和2.2之间）
- ✅ 优先级设为最高，必须在完成后再进行Benchmark与调优
- ✅ 包含元数据增强、文件哈希、去重检查、智能存储等功能
- ✅ 目标：避免文档重复添加，为检索阶段提供帮助信息

### 2024-01-XX: Agentic Search与笔记检索体系（Phase 2.5）

- ✅ 新增Agentic Search与笔记检索体系任务（最高优先级）
- ✅ 重构计划文档，降低RAG优化与评测的优先级
- ✅ 优先实现笔记的检索体系与agentic search流程
- ✅ 核心设计：
  - 结构化信息（tags, links, frontmatter）存储在SQLite，支持精确查询
  - 只有普通文本内容生成embedding用于语义搜索
  - LLM通过工具调用自主决定检索策略（笔记优先 → 标签/链接查询 → 网络/PDF搜索）
- ✅ 目标：实现智能检索系统，充分利用Obsidian笔记的结构化特征
