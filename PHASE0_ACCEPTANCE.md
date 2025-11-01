# Phase 0 验收指南

## 验收目标

验证 Phase 0 的所有功能是否正常工作，确保项目基础搭建完成。

## 准备工作

### 1. 环境准备

```bash
# 1. 确保在项目根目录
cd d:\repo\OmniKnowledgeBase

# 2. 创建并激活虚拟环境（如果还没有）
python -m venv backend\venv
backend\venv\Scripts\activate  # Windows PowerShell

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建 .env 文件
copy .env.example .env
# 编辑 .env 文件，至少填入 DEEPSEEK_API_KEY
```

### 2. 配置 API Key

编辑 `.env` 文件，填入你的 DeepSeek API Key：

```bash
# 至少需要配置以下内容：
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_actual_api_key_here
```

**获取 DeepSeek API Key**：
- 访问：https://platform.deepseek.com
- 注册账号并获取 API Key

## 验收步骤

### 步骤 1: 验证目录结构

```bash
# 检查必要的目录是否存在
dir pages
dir .streamlit
dir backend\app\services
dir backend\app\utils
```

**预期结果**：
- ✅ `pages/` 目录存在，包含三个页面文件
- ✅ `.streamlit/` 目录存在，包含 `config.toml`
- ✅ `backend/app/services/` 目录存在
- ✅ `backend/app/utils/` 目录存在

### 步骤 2: 验证文件存在

```bash
# 检查关键文件
dir app.py
dir .env.example
dir backend\app\services\vector_service.py
dir backend\app\utils\filesystem.py
dir backend\app\utils\logging_config.py
dir backend\app\utils\llm_config.py
```

**预期结果**：
- ✅ 所有文件都存在
- ✅ `pages/` 目录下的文件名不包含 emoji（使用 `1_Documents.py` 格式）

### 步骤 3: 验证 Python 代码语法

```bash
# 检查代码语法
python -m py_compile app.py
python -m py_compile backend\app\services\vector_service.py
python -m py_compile backend\app\utils\filesystem.py
python -m py_compile backend\app\utils\logging_config.py
python -m py_compile backend\app\utils\llm_config.py
```

**预期结果**：
- ✅ 所有文件没有语法错误

### 步骤 4: 验证文件系统工具

```python
# 运行 Python 交互式环境
python

# 在 Python 中执行：
from backend.app.utils.filesystem import ensure_directories, get_notes_directory, get_documents_directory

# 确保目录创建
ensure_directories()

# 验证目录路径
print(get_notes_directory())
print(get_documents_directory())

# 检查目录是否创建
import os
print(os.path.exists("notes"))
print(os.path.exists("documents"))
print(os.path.exists("chroma_db"))
```

**预期结果**：
- ✅ `ensure_directories()` 执行成功
- ✅ 三个目录（notes/, documents/, chroma_db/）都已创建

### 步骤 5: 验证 ChromaDB 连接

```python
# 在 Python 中执行：
from backend.app.services.vector_service import VectorService

# 创建向量服务实例
vector_service = VectorService()

# 测试创建集合
collection = vector_service.get_or_create_collection("test_collection")
print(f"Collection created: {collection.name}")

# 测试列出集合
collections = vector_service.list_collections()
print(f"Collections: {collections}")
```

**预期结果**：
- ✅ VectorService 初始化成功
- ✅ 可以创建集合
- ✅ 可以列出集合

### 步骤 6: 验证 LLM 配置

```python
# 在 Python 中执行：
from backend.app.utils.llm_config import llm_config

# 检查配置
print(f"Provider: {llm_config.provider}")
print(f"Model: {llm_config.model}")
print(f"API Base: {llm_config.api_base}")
print(f"Has API Key: {bool(llm_config.api_key)}")

# 获取 LangChain 配置
config = llm_config.get_langchain_config()
print(f"LangChain config: {config}")
```

**预期结果**：
- ✅ LLM 配置加载成功
- ✅ Provider 默认为 `deepseek`
- ✅ 如果配置了 API Key，`has_api_key` 为 True

### 步骤 7: 验证 Streamlit 应用启动

```bash
# 启动 Streamlit 应用
streamlit run app.py
```

**预期结果**：
- ✅ 应用成功启动
- ✅ 浏览器自动打开 `http://localhost:8501`
- ✅ 主页面显示 "OmniKnowledgeBase" 标题
- ✅ 侧边栏显示导航菜单，包含：
  - Documents
  - Notes
  - Q&A

### 步骤 8: 验证页面导航

在浏览器中：

1. **主页面**：
   - ✅ 显示 "OmniKnowledgeBase" 标题
   - ✅ 显示功能列表
   - ✅ 显示导航说明

2. **Documents 页面**：
   - ✅ 点击侧边栏 "Documents" 或访问 `http://localhost:8501/Documents`
   - ✅ 显示 "Documents" 标题
   - ✅ 显示 "Coming Soon" 信息

3. **Notes 页面**：
   - ✅ 点击侧边栏 "Notes" 或访问 `http://localhost:8501/Notes`
   - ✅ 显示 "Notes" 标题
   - ✅ 显示 "Coming Soon" 信息

4. **Q&A 页面**：
   - ✅ 点击侧边栏 "Q&A" 或访问 `http://localhost:8501/QA`
   - ✅ 显示 "Q&A" 标题
   - ✅ 显示 "Coming Soon" 信息

### 步骤 9: 验证日志系统

```python
# 在 Python 中执行：
from backend.app.utils.logging_config import setup_logging
import logging

# 测试日志
setup_logging(log_level="DEBUG")
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

**预期结果**：
- ✅ 日志输出到控制台
- ✅ 日志格式正确（包含时间、级别、文件名、行号、消息）

### 步骤 10: 验证环境变量

```bash
# 检查 .env.example 文件
type .env.example
```

**预期结果**：
- ✅ `.env.example` 文件存在
- ✅ 包含所有必要的环境变量说明
- ✅ 默认配置为 DeepSeek
- ✅ 包含 OpenRouter 和 OpenAI 的备选配置

## 验收检查清单

### 文件结构 ✅
- [ ] `app.py` 存在且可运行
- [ ] `pages/` 目录存在，包含三个页面文件
- [ ] 所有页面文件名不包含 emoji
- [ ] `.streamlit/config.toml` 存在
- [ ] `.env.example` 存在

### 后端服务 ✅
- [ ] `backend/app/services/vector_service.py` 存在
- [ ] `backend/app/utils/filesystem.py` 存在
- [ ] `backend/app/utils/logging_config.py` 存在
- [ ] `backend/app/utils/llm_config.py` 存在

### 功能验证 ✅
- [ ] 文件系统工具可以创建目录
- [ ] ChromaDB 可以连接和创建集合
- [ ] LLM 配置可以正确加载
- [ ] Streamlit 应用可以启动
- [ ] 所有页面可以正常访问

### 配置验证 ✅
- [ ] `.env.example` 包含 DeepSeek 配置（默认）
- [ ] `.env.example` 包含 OpenRouter 配置（备选）
- [ ] `.env.example` 包含 OpenAI 配置（备选）
- [ ] 日志系统可以正常工作

## 常见问题排查

### 问题 1: Streamlit 无法启动

**可能原因**：
- 依赖未安装：运行 `pip install -r requirements.txt`
- 端口被占用：检查 8501 端口是否被占用

**解决方案**：
```bash
# 重新安装依赖
pip install -r requirements.txt

# 使用不同端口
streamlit run app.py --server.port 8502
```

### 问题 2: ChromaDB 初始化失败

**可能原因**：
- 目录权限问题
- ChromaDB 未正确安装

**解决方案**：
```bash
# 重新安装 ChromaDB
pip install chromadb --upgrade

# 检查目录权限
python -c "from backend.app.utils.filesystem import ensure_directories; ensure_directories()"
```

### 问题 3: 导入错误

**可能原因**：
- Python 路径问题
- 模块未正确安装

**解决方案**：
```bash
# 确保在项目根目录
cd d:\repo\OmniKnowledgeBase

# 检查 Python 路径
python -c "import sys; print(sys.path)"

# 重新安装依赖
pip install -e .
```

## 验收通过标准

✅ **所有检查项都通过**，Phase 0 验收完成！

如果所有步骤都成功，说明：
1. 项目基础结构正确
2. 所有核心模块可以正常工作
3. Streamlit 应用可以正常启动和访问
4. 配置系统正常工作
5. 可以开始 Phase 1 的开发工作

## 下一步

Phase 0 验收通过后，可以开始 Phase 1：
- Phase 1.1: 向量数据库和文件系统配置（完善）
- Phase 1.2: Streamlit 基础框架（完善）

