# 开发任务追踪（更新版）

> 基于 ROADMAP.md 的详细路线规划，此文件用于追踪当前开发进度
> 
> **架构调整**：使用 Streamlit + ChromaDB + 文件系统（无 SQL 数据库）

## 当前 Sprint: Phase 0 - 项目基础搭建 ✅

**开始日期**: 2024-01-XX  
**结束日期**: 2024-01-XX  
**状态**: ✅ 已完成

### 任务列表

- [x] **Streamlit 应用初始化** ✅
  - [x] 创建 Streamlit 主应用（`app.py`）
  - [x] 创建页面目录结构（`pages/`）
  - [x] 配置 Streamlit 配置文件（`.streamlit/config.toml`）
  - [x] 创建基础页面布局

- [x] **ChromaDB 配置** ✅
  - [x] 安装 ChromaDB（已在 requirements.txt）
  - [x] 创建向量存储服务（`backend/app/services/vector_service.py`）
  - [x] 配置 ChromaDB 连接和集合
  - [x] 基础向量存储功能已实现

- [x] **文件系统结构** ✅
  - [x] 创建 `notes/` 目录（存储 Obsidian 笔记）
  - [x] 创建 `documents/` 目录（存储上传的文档）
  - [x] 创建 `chroma_db/` 目录（ChromaDB 数据）
  - [x] 创建文件系统工具模块（`backend/app/utils/filesystem.py`）

- [x] **基础配置文件** ✅
  - [x] 创建 `.env.example`（包含所有必需的环境变量）
  - [x] 配置日志系统（`backend/app/utils/logging_config.py`）
  - [x] 配置 LLM API Key（OpenAI）- 通过 .env.example 配置

---

## Phase 1: 核心基础设施（第 1 周）

### Sprint 1.1: 向量数据库和文件系统配置

- [x] ChromaDB 配置模块
- [x] 向量存储服务封装
- [x] 文件系统工具
- [x] 笔记文件管理服务
- [x] 元数据模型定义（Pydantic）
- [x] 目录结构初始化

### Sprint 1.2: Streamlit 基础框架 ✅

- [x] Streamlit 主应用
- [x] 页面路由结构
- [x] 侧边栏配置和导航
- [x] 页面布局组件
- [x] 状态管理（st.session_state）
- [x] 配置文件管理

---

## Phase 2: 文档处理模块（第 2 周）

### Sprint 2.1: 文档解析服务 ✅

- [x] Markdown 解析器 ✅
- [x] PDF 解析器 ✅
- [x] URL 抓取器 ✅
- [x] 元数据提取 ✅
- [x] 文档分块服务 ✅
- [x] 文档向量化服务 ✅
- [x] Streamlit 文档上传界面 ✅

### Sprint 2.2: Streamlit 文档管理界面

- [ ] 文档上传页面
- [ ] 文档列表显示
- [ ] 文档详情页面
- [ ] 文档搜索功能（语义搜索）
- [ ] 文档删除功能
- [ ] 文档标签管理

---

## Phase 3: 笔记管理模块（第 3 周）

### Sprint 3.1: Obsidian 风格笔记核心功能

- [ ] 笔记文件服务
- [ ] Markdown 链接解析器
- [ ] 双向链接追踪
- [ ] 文件夹结构支持
- [ ] Frontmatter 解析
- [ ] 笔记向量化
- [ ] Streamlit 笔记管理界面

### Sprint 3.2: Streamlit 笔记界面和可视化

- [ ] 笔记列表页面
- [ ] Markdown 编辑器
- [ ] 笔记详情页面
- [ ] 链接自动补全
- [ ] 笔记关系图可视化
- [ ] 笔记搜索功能

---

## Phase 4: RAG 问答系统（第 4-5 周）

### Sprint 4.1: RAG 检索和生成

- [ ] RAG 服务
- [ ] 检索器实现（ChromaDB）
- [ ] 上下文窗口管理
- [ ] LLM 集成（LangChain）
- [ ] 流式响应支持（Streamlit）
- [ ] Streamlit Q&A 界面

### Sprint 4.2: AI 笔记生成功能 ⭐ 新功能

- [ ] 笔记生成服务
- [ ] Prompt 模板设计
- [ ] 笔记格式化（Obsidian 格式）
- [ ] 笔记保存到文件系统
- [ ] 自动向量化新笔记
- [ ] Streamlit 笔记生成界面

### Sprint 4.3: RAG 优化和增强

- [ ] 混合检索
- [ ] 查询扩展
- [ ] 对话历史管理
- [ ] 答案质量评估
- [ ] 相关文档推荐
- [ ] 问答历史记录

---

## Phase 5: Streamlit UI 优化（第 6 周）

### Sprint 5.1: UI 优化和增强

- [ ] 自定义主题和样式
- [ ] 页面布局优化
- [ ] 组件样式美化
- [ ] 加载状态和进度条
- [ ] 错误处理和用户提示
- [ ] 响应式设计优化

### Sprint 5.2: 高级功能集成

- [ ] 文件上传组件优化
- [ ] Markdown 预览增强
- [ ] 图表可视化
- [ ] 导出功能
- [ ] 设置页面
- [ ] 帮助文档和说明

---

## Phase 6: 测试和优化（第 7 周）

### Sprint 6.1: 测试和优化

- [ ] 单元测试（服务层）
- [ ] 集成测试（Streamlit 页面）
- [ ] 测试覆盖率 ≥ 70%
- [ ] 性能测试
- [ ] 错误场景测试
- [ ] 向量数据库查询优化
- [ ] 日志和监控
- [ ] 代码重构和优化

---

## Phase 7: 部署和文档（第 8 周）

### Sprint 7.1: 部署准备

- [ ] Docker 容器化（Streamlit + ChromaDB）
- [ ] Docker Compose 配置
- [ ] 环境变量管理
- [ ] Streamlit Cloud 部署配置（可选）
- [ ] 部署文档

### Sprint 7.2: 文档完善

- [ ] 用户使用手册
- [ ] 开发者文档
- [ ] 部署指南
- [ ] 常见问题（FAQ）
- [ ] 架构文档更新

---

## 里程碑追踪

- [ ] **Milestone 1: MVP**（第 4 周）
  - 文档上传和向量化
  - 基础笔记管理
  - RAG 问答功能
  - Streamlit 基础界面

- [ ] **Milestone 2: 核心功能完整**（第 6 周）
  - 完整文档管理
  - Obsidian 风格笔记
  - RAG 问答系统
  - **AI 笔记生成** ⭐
  - Streamlit 完整界面

- [ ] **Milestone 3: 生产就绪**（第 8 周）
  - 完整测试覆盖
  - 性能优化完成
  - 部署文档完善

---

## 架构变更记录

### 2024-01-XX: 架构简化

- ✅ 移除 SQL 数据库（SQLAlchemy、Alembic）
- ✅ 使用纯向量数据库（ChromaDB）+ 文件系统
- ✅ 前端改为 Streamlit（快速构建 LLM 应用）
- ✅ 新增 AI 笔记生成功能

### 注意事项

- 每个任务完成后更新此文件
- 遇到阻塞问题及时记录
- 定期回顾和调整路线图
- 遵循项目规范（文件长度、代码风格、提交规范）
- **重点关注**：RAG 功能和 AI 笔记生成
