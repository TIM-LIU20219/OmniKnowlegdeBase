# OmniKnowledgeBase 开发路线规划

## 项目概述

OmniKnowledgeBase 是一个专注于 RAG 的知识库系统，包含以下核心功能：

- 📄 **文档处理**：支持 Markdown、PDF、URL 等多种格式
- 📝 **笔记管理**：Obsidian 风格的笔记系统，支持双向链接
- 🤖 **RAG Q&A**：基于检索增强生成的智能问答系统
- ✍️ **AI 笔记生成**：LLM 自动生成 Obsidian 格式的 Markdown 笔记
- 🎨 **快速 UI**：Streamlit 构建的 LLM 应用界面（后期可迁移到 Vite+React）

## 技术栈

### 后端 + 前端（一体化）
- **框架**：Streamlit（快速构建 LLM 应用）
- **后端 API**：FastAPI（可选，用于后期扩展）
- **数据存储**：
  - **向量数据库**：ChromaDB（存储所有文档和笔记的向量嵌入）
  - **文件系统**：直接存储 Obsidian 笔记文件（.md）
  - **无 SQL 数据库**：简化架构，降低复杂度
- **RAG**：LangChain + Sentence Transformers
- **文档处理**：PyPDF、Markdown、BeautifulSoup4
- **LLM**：OpenAI API / 本地模型（通过 LangChain）

> **架构说明**：详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 开发路线（分阶段敏捷开发）

### 🎯 Phase 0: 项目基础搭建 ✅

**目标**：建立项目基础设施和开发环境

**任务清单**：
- [x] 项目结构创建
- [x] 依赖配置（requirements.txt, pyproject.toml）
- [x] Git 工作流配置
- [x] Streamlit 应用初始化
- [x] ChromaDB 配置和初始化
- [x] 文件系统结构创建（notes/、documents/目录）
- [x] 基础配置文件（.env.example）
- [ ] Docker 配置（可选，用于开发环境）

**预计时间**：1 天

**验收标准**：
- ✅ Streamlit 应用可启动并显示基础页面
- ✅ ChromaDB 可以连接和创建集合
- ✅ 文件系统目录结构正确

**完成状态**：✅ Phase 0 已完成

---

### 🚀 Phase 1: 核心基础设施（第 1 周）

#### Sprint 1.1: 向量数据库和文件系统配置

**目标**：建立 ChromaDB 向量存储和文件系统结构

**任务清单**：
- [ ] ChromaDB 配置模块（`app/utils/vector_store.py`）
- [ ] 向量存储服务封装（`app/services/vector_service.py`）
- [ ] 文件系统工具（`app/utils/filesystem.py`）
- [ ] 笔记文件管理服务（`app/services/note_file_service.py`）
- [ ] 元数据模型定义（Pydantic Schemas）
- [ ] 目录结构初始化（notes/、documents/、chroma_db/）

**技术要点**：
- ChromaDB 集合设计（文档集合、笔记集合）
- 元数据字段定义（doc_type、file_path、tags等）
- 文件系统操作（创建、读取、写入笔记文件）

**验收标准**：
- ChromaDB 可以创建集合并存储向量
- 笔记文件可以正确读写
- 元数据可以正确关联

---

#### Sprint 1.2: Streamlit 基础框架

**目标**：建立 Streamlit 应用结构和页面布局

**任务清单**：
- [ ] Streamlit 主应用（`app.py`）
- [ ] 页面路由结构（使用 `st.navigation` 或自定义路由）
- [ ] 侧边栏配置和导航
- [ ] 页面布局组件（Header、Sidebar、Main）
- [ ] 状态管理（使用 `st.session_state`）
- [ ] 配置文件管理（`.streamlit/config.toml`）

**验收标准**：
- Streamlit 应用可以启动
- 多页面导航正常工作
- 状态管理可用

---

### 📄 Phase 2: 文档处理模块（第 2 周）

#### Sprint 2.1: 文档解析服务

**目标**：实现多种格式文档的解析功能

**任务清单**：
- [ ] Markdown 解析器（`app/services/document_processor.py`）
- [ ] PDF 解析器（使用 PyPDF）
- [ ] URL 抓取器（使用 BeautifulSoup4）
- [ ] 文档元数据提取（标题、日期、标签、链接）
- [ ] 文档分块服务（`app/services/chunking_service.py`）
- [ ] 文档向量化服务（`app/services/embedding_service.py`）
- [ ] Streamlit 文档上传界面

**技术要点**：
- 智能文档分块（考虑语义边界）
- 异步文件处理
- 错误处理（损坏文件、网络超时等）

**验收标准**：
- 支持上传 Markdown、PDF、URL
- 正确提取文档元数据
- 文档内容可向量化并存储到 ChromaDB

---

#### Sprint 2.2: Streamlit 文档管理界面

**目标**：实现文档上传、列表、查看界面

**任务清单**：
- [ ] 文档上传页面（`pages/1_📄_Documents.py`）
- [ ] 文档列表显示（使用 `st.dataframe` 或卡片视图）
- [ ] 文档详情页面
- [ ] 文档搜索功能（语义搜索）
- [ ] 文档删除功能
- [ ] 文档标签管理

**验收标准**：
- 可以上传文档并显示列表
- 可以查看文档详情
- 搜索功能可用（基于向量搜索）

---

### 📝 Phase 3: 笔记管理模块（第 3 周）

#### Sprint 3.1: Obsidian 风格笔记核心功能

**目标**：实现笔记文件管理和双向链接解析

**任务清单**：
- [ ] 笔记文件服务（`app/services/note_service.py`）
- [ ] Markdown 链接解析器（`[[note-name]]` 格式）
- [ ] 笔记双向链接追踪（基于文件系统扫描）
- [ ] 笔记文件夹结构支持
- [ ] Frontmatter 元数据解析（YAML）
- [ ] 笔记内容向量化并存储到 ChromaDB
- [ ] Streamlit 笔记管理界面

**技术要点**：
- 使用正则表达式解析 `[[链接]]`
- 文件系统操作（读取、写入、删除笔记文件）
- 笔记链接关系图（内存或 JSON 文件存储）

**验收标准**：
- 支持创建、编辑、删除笔记文件
- 自动检测和解析双向链接
- 笔记可组织到文件夹中
- 笔记内容可以向量化

---

#### Sprint 3.2: Streamlit 笔记界面和可视化

**目标**：实现笔记管理界面和简单可视化

**任务清单**：
- [ ] 笔记列表页面（`pages/2_📝_Notes.py`）
- [ ] Markdown 编辑器（使用 `st.text_area` 或 `streamlit-markdown-editor`）
- [ ] 笔记详情页面
- [ ] 链接自动补全
- [ ] 笔记关系图可视化（使用 `networkx` + `pyvis` 或 `plotly`）
- [ ] 笔记搜索功能

**验收标准**：
- 可以创建和编辑笔记
- 链接自动识别
- 笔记关系图可以可视化
- 笔记搜索可用（基于向量搜索）

---

### 🤖 Phase 4: RAG 问答系统（第 4-5 周）

#### Sprint 4.1: RAG 检索和生成

**目标**：实现检索增强生成问答功能

**任务清单**：
- [ ] RAG 服务（`app/services/rag_service.py`）
- [ ] 检索器实现（基于 ChromaDB 的语义搜索）
- [ ] 上下文窗口管理
- [ ] LLM 集成（LangChain，支持 OpenAI/本地模型）
- [ ] 流式响应支持（Streamlit `st.write_stream`）
- [ ] Streamlit Q&A 界面（`pages/3_🤖_Q&A.py`）

**技术要点**：
- 使用 LangChain 构建 RAG 链
- ChromaDB 相似度搜索
- 上下文压缩和相关性过滤
- 支持多种 LLM 后端

**验收标准**：
- 可基于文档和笔记内容回答问题
- 返回答案包含来源引用
- 支持流式输出显示

---

#### Sprint 4.2: AI 笔记生成功能

**目标**：实现 LLM 自动生成 Obsidian 笔记

**任务清单**：
- [ ] 笔记生成服务（`app/services/note_generator_service.py`）
- [ ] Prompt 模板设计（总结、扩展、问答转笔记等）
- [ ] 笔记格式化（Obsidian 格式、Frontmatter、链接等）
- [ ] 笔记保存到文件系统
- [ ] 自动向量化新生成的笔记
- [ ] Streamlit 笔记生成界面

**技术要点**：
- 使用 LLM 生成结构化 Markdown
- 自动添加 Frontmatter（标题、日期、标签）
- 自动生成双向链接
- 支持多种生成模式（总结、问答、扩展等）

**验收标准**：
- 可以基于文档或对话生成笔记
- 生成的笔记符合 Obsidian 格式
- 笔记自动保存并向量化

---

#### Sprint 4.3: RAG 优化和增强

**目标**：优化检索质量和用户体验

**任务清单**：
- [ ] 混合检索（语义 + 关键词）
- [ ] 查询扩展和重写
- [ ] 对话历史管理（使用 `st.session_state`）
- [ ] 答案质量评估
- [ ] 相关文档推荐
- [ ] 问答历史记录（可选，使用文件或向量数据库）

**验收标准**：
- 检索准确率提升
- 支持多轮对话
- 答案质量可靠

---

### 🎨 Phase 5: Streamlit UI 优化（第 6 周）

#### Sprint 5.1: UI 优化和增强

**目标**：优化 Streamlit 界面体验

**任务清单**：
- [ ] 自定义主题和样式（`.streamlit/config.toml`）
- [ ] 页面布局优化（多列布局、侧边栏）
- [ ] 组件样式美化（使用 `streamlit-elements` 或自定义 CSS）
- [ ] 加载状态和进度条
- [ ] 错误处理和用户提示
- [ ] 响应式设计优化

**验收标准**：
- 界面美观易用
- 加载状态清晰
- 错误提示友好

---

#### Sprint 5.2: 高级功能集成

**目标**：集成高级功能和交互

**任务清单**：
- [ ] 文件上传组件优化（拖拽上传）
- [ ] Markdown 预览增强（使用 `streamlit-markdown`）
- [ ] 图表可视化（使用 `plotly` 或 `altair`）
- [ ] 导出功能（笔记导出、对话导出）
- [ ] 设置页面（配置 LLM、向量数据库等）
- [ ] 帮助文档和说明

**验收标准**：
- 所有功能可用
- 用户体验流畅
- 文档完整

---

### 🔧 Phase 6: 测试和优化（第 7 周）

#### Sprint 6.1: 测试和优化

**任务清单**：
- [ ] 单元测试（服务层）
- [ ] 集成测试（Streamlit 页面）
- [ ] 测试覆盖率 ≥ 70%
- [ ] 性能测试（文档处理、向量化、RAG）
- [ ] 错误场景测试
- [ ] 向量数据库查询优化
- [ ] 日志和监控（结构化日志）
- [ ] 代码重构和优化

---

### 🚢 Phase 7: 部署和文档（第 8 周）

#### Sprint 7.1: 部署准备

**任务清单**：
- [ ] Docker 容器化（Streamlit + ChromaDB）
- [ ] Docker Compose 配置
- [ ] 环境变量管理
- [ ] Streamlit Cloud 部署配置（可选）
- [ ] 部署文档

---

#### Sprint 7.2: 文档完善

**任务清单**：
- [ ] 用户使用手册
- [ ] 开发者文档
- [ ] 部署指南
- [ ] 常见问题（FAQ）
- [ ] 架构文档更新

---

## 开发原则和最佳实践

### 1. 敏捷开发流程

- **Sprint 周期**：2 周一个 Sprint
- **每日站会**：使用 Cursor AI Agent 进行代码审查和进度同步
- **Sprint 回顾**：每个 Sprint 结束后评估和调整

### 2. 代码质量

- **文件长度限制**：Python ≤ 300 行，TypeScript ≤ 400 行
- **代码审查**：每个 PR 必须通过 AI Agent 审查
- **测试驱动**：关键功能先写测试再实现

### 3. Git 工作流

- **分支策略**：
  - `main`：生产就绪代码
  - `develop`：开发集成分支
  - `feature/<feature-name>`：功能分支
  - `worktree/<agent-id>/<feature-name>`：并行开发分支
- **提交规范**：遵循 Conventional Commits

### 4. 并行开发建议

使用 Git Worktree 支持多 Agent 并行开发：

```bash
# 创建 worktree 分支
git worktree add ../OmniKnowledgeBase-agent1 feature/document-processing
git worktree add ../OmniKnowledgeBase-agent2 feature/note-management
```

---

## 里程碑和验收标准

### Milestone 1: MVP（最小可行产品）- 第 4 周

**功能范围**：
- ✅ 文档上传和向量化（Markdown、PDF、URL）
- ✅ 基础笔记管理（创建、编辑、查看）
- ✅ RAG 问答功能（基于文档和笔记）
- ✅ Streamlit 基础界面

**验收标准**：
- 用户可以上传文档
- 用户可以创建笔记
- 用户可以提问并获得答案
- 界面基本可用

---

### Milestone 2: 核心功能完整 - 第 6 周

**功能范围**：
- ✅ 完整的文档管理（上传、搜索、查看）
- ✅ Obsidian 风格笔记（双向链接、关系图）
- ✅ RAG 问答系统（检索、生成、流式输出）
- ✅ **AI 笔记生成**（LLM 自动生成 Obsidian 笔记）
- ✅ Streamlit 完整界面

**验收标准**：
- 所有核心功能可用
- UI 界面完整
- 可以生成 Obsidian 笔记

---

### Milestone 3: 生产就绪 - 第 8 周

**功能范围**：
- ✅ 完整的测试覆盖
- ✅ 性能优化完成
- ✅ 部署文档完善
- ✅ 监控和日志系统

**验收标准**：
- 测试覆盖率 ≥ 70%
- 可稳定运行
- 文档完整

---

## 风险与应对

### 技术风险

1. **向量存储性能问题**
   - **应对**：早期进行性能测试，必要时切换到 Pinecone 等云服务

2. **LLM 集成复杂度**
   - **应对**：先使用 OpenAI API，后续再支持本地模型

3. **前端性能问题**
   - **应对**：使用代码分割、懒加载，优化大文档渲染

### 进度风险

1. **功能范围蔓延**
   - **应对**：严格遵循路线图，新功能放入后续版本

2. **测试时间不足**
   - **应对**：测试与开发并行，每个 Sprint 包含测试任务

---

## 后续版本规划（v0.2+）

### v0.2: 协作功能
- 多用户支持
- 权限管理
- 协作编辑

### v0.3: 插件系统
- 插件架构
- 自定义处理器
- 第三方集成

### v0.4: 移动端
- 响应式优化
- PWA 支持
- 移动端应用

---

## 总结

本路线图采用**敏捷开发**方式，分 7 个阶段、16 周完成核心功能开发。每个阶段都有明确的交付物和验收标准，便于使用 Cursor AI Agent 进行并行开发和快速迭代。

**关键成功因素**：
1. 遵循项目规范（文件长度、代码风格）
2. 持续集成和测试
3. 清晰的 API 设计和文档
4. 模块化架构，便于并行开发

**开始第一步**：从 Phase 0 的"Streamlit 应用初始化"开始，建立开发环境。

---

## 架构调整说明

### 数据库架构简化

根据项目侧重点（RAG），采用**纯向量数据库 + 文件系统**架构：

- ✅ **ChromaDB**：存储所有文档和笔记的向量嵌入和元数据
- ✅ **文件系统**：直接存储 Obsidian 笔记文件（.md），可以用 Obsidian 打开
- ❌ **无 SQL 数据库**：简化架构，降低复杂度

详见：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

### 前端技术栈调整

- ✅ **Streamlit**：快速构建 LLM 应用，适合快速迭代
- ✅ **后期可迁移**：如果后续需要更复杂的 UI，可以迁移到 Vite + React

### LLM 生成笔记功能

新增核心功能：**AI 自动生成 Obsidian 格式笔记**
- 基于文档内容生成总结笔记
- 基于问答对话生成笔记
- 自动格式化为 Obsidian 格式（Frontmatter、链接等）


