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
- ❌ **RAG 优化**：混合检索、查询扩展、重排序等
- ❌ **多模态输入**：Crawl4AI 集成、增强网页读取
- ❌ **笔记向量化**：笔记专用向量化流程
- ❌ **对话管理**：多轮对话、历史管理

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

---

## 🔍 Phase 2: RAG 效果优化（优先级：高）

> **目标**：迭代优化 RAG 效果，提升检索和生成质量

### Sprint 2.1: 基础测评与基准建立

- [ ] **PDF 教材接入**
  - [ ] 准备 31 页 PDF 教材
  - [ ] 创建 PDF 处理脚本 (`cli document add --pdf textbook.pdf`)
  - [ ] 验证文档完整导入（检查块数量、向量化状态）
  - [ ] 创建初始 Benchmark 数据集（基于教材内容）
- [ ] **基准测试**
  - [ ] 运行初始评估 (`cli benchmark run --dataset textbook_benchmark.json`)
  - [ ] 记录基线指标（Precision/Recall/F1、答案相似度）
  - [ ] 分析检索和生成的薄弱环节

### Sprint 2.2: 检索优化

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

### Sprint 2.3: 上下文优化

- [ ] **上下文压缩**
  - [ ] 实现基于重要性的上下文压缩
  - [ ] 实现基于长度的上下文截断
- [ ] **相关性过滤**
  - [ ] 实现基于相似度阈值的过滤
  - [ ] 实现基于元数据的过滤
- [ ] **动态上下文长度**
  - [ ] 根据问题复杂度动态调整上下文长度
  - [ ] 根据 LLM 模型限制调整上下文

### Sprint 2.4: Prompt 优化

- [ ] **Prompt 模板管理**
  - [ ] 实现 Prompt 模板系统
  - [ ] 支持多模板切换 (`cli rag query --prompt-template <name>`)
  - [ ] 创建针对不同场景的 Prompt 模板
- [ ] **Prompt 优化实验**
  - [ ] A/B 测试不同 Prompt 模板
  - [ ] 记录不同模板的效果指标
  - [ ] 选择最优 Prompt 模板

### Sprint 2.5: 评估与迭代

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

## 📝 Phase 3: Q&A 与笔记管理增强（优先级：高）

> **目标**：提升 Q&A 体验和笔记管理能力

### Sprint 3.1: 对话管理

- [ ] **多轮对话支持**
  - [ ] 实现对话上下文管理
  - [ ] 实现对话历史存储
  - [ ] 添加对话 CLI (`cli rag chat <session_id>`)
- [ ] **对话历史管理**
  - [ ] 实现对话历史查询 (`cli rag history list`)
  - [ ] 实现对话历史删除 (`cli rag history delete <session_id>`)
  - [ ] 实现对话导出 (`cli rag history export <session_id>`)

### Sprint 3.2: 笔记向量化

- [ ] **笔记专用向量化服务**
  - [ ] 创建笔记向量化服务 (`NoteVectorizationService`)
  - [ ] 实现笔记批量向量化 (`cli note vectorize --all`)
  - [ ] 实现笔记增量向量化（仅向量化新笔记）
- [ ] **笔记检索**
  - [ ] 实现笔记语义搜索 (`cli note search <query>`)
  - [ ] 实现笔记+文档混合检索 (`cli rag query --include-notes`)

### Sprint 3.3: 笔记链接管理

- [ ] **双向链接追踪**
  - [ ] 实现反向链接扫描（扫描所有笔记）
  - [ ] 实现链接图构建 (`cli note graph`)
  - [ ] 实现链接统计 (`cli note links --stats`)
- [ ] **笔记关系分析**
  - [ ] 实现笔记聚类分析
  - [ ] 实现笔记主题提取
  - [ ] 实现笔记推荐 (`cli note recommend <file_path>`)

### Sprint 3.4: AI 笔记生成

- [ ] **笔记生成服务**
  - [ ] 实现基于 RAG 的笔记生成服务
  - [ ] 设计笔记生成 Prompt 模板
  - [ ] 实现笔记格式化（Obsidian 格式）
- [ ] **笔记生成 CLI**
  - [ ] 实现笔记生成命令 (`cli note generate --topic <topic>`)
  - [ ] 实现基于文档的笔记生成 (`cli note generate --from-doc <doc_id>`)
  - [ ] 实现笔记自动向量化

---

## 🌐 Phase 4: 多模态输入增强（优先级：中）

> **目标**：集成 Crawl4AI，增强网页读取能力

### Sprint 4.1: Crawl4AI 集成

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

### Sprint 4.2: 多模态内容处理

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

### Sprint 4.3: 多模态 CLI

- [ ] **URL 处理 CLI 增强**
  - [ ] 更新 `cli document add --url` 支持 Crawl4AI
  - [ ] 添加多模态选项 (`cli document add --url <url> --multimodal`)
  - [ ] 添加图片处理选项 (`cli document add --url <url> --extract-images`)
- [ ] **多模态内容查看**
  - [ ] 实现多模态内容预览 (`cli document show --multimodal <doc_id>`)
  - [ ] 实现图片查看 (`cli document images <doc_id>`)
  - [ ] 实现表格查看 (`cli document tables <doc_id>`)

---

## 🧪 Phase 5: 测试与优化（优先级：中）

### Sprint 5.1: 单元测试

- [ ] 文档处理服务测试
- [ ] 笔记管理服务测试
- [ ] RAG 服务测试
- [ ] CLI 命令测试
- [ ] 测试覆盖率 ≥ 70%

### Sprint 5.2: 集成测试

- [ ] 端到端文档处理流程测试
- [ ] RAG Pipeline 集成测试
- [ ] CLI 集成测试
- [ ] 性能测试

### Sprint 5.3: 性能优化

- [ ] 向量检索优化
- [ ] 批量处理优化
- [ ] 缓存机制实现
- [ ] 异步处理优化

---

## 📚 Phase 6: 文档与工具（优先级：低）

### Sprint 6.1: CLI 文档

- [ ] CLI 使用手册
- [ ] CLI 命令参考
- [ ] CLI 示例脚本
- [ ] CLI 最佳实践

### Sprint 6.2: 开发文档

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

### Milestone 2: RAG 效果优化（Phase 2 完成）

- [ ] PDF 教材成功接入并测评
- [ ] RAG 效果相比基线提升 ≥ 20%
- [ ] Benchmark 评估流程完善

### Milestone 3: Q&A 与笔记管理增强（Phase 3 完成）

- [ ] 多轮对话支持
- [ ] 笔记向量化完成
- [ ] AI 笔记生成可用

### Milestone 4: 多模态输入（Phase 4 完成）

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

1. **Phase 1.1**: CLI 框架搭建
2. **Phase 2.1**: PDF 教材接入和基础测评
3. **Phase 1.2**: 文档管理 CLI（与 PDF 接入并行）

### 近期计划（2-3 周）

1. **Phase 1**: 完成所有核心功能的 CLI
2. **Phase 2.2-2.3**: 开始 RAG 检索优化
3. **Phase 3.1**: 对话管理实现

---

## 📌 注意事项

- 每个任务完成后更新此文件
- 遇到阻塞问题及时记录
- 定期回顾和调整优先级
- 遵循项目规范（文件长度、代码风格、提交规范）
- **重点关注**：RAG 效果优化和 CLI 工具完善

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
