# OmniKnowledgeBase 启动指南

## 前置要求

1. Python 3.8+
2. 已安装所有依赖（见 `requirements.txt`）
3. 环境变量配置（可选）

## 快速启动

### 1. 启动 FastAPI 后端

**重要：必须从项目根目录运行！**

在项目根目录下运行：

```bash
# Windows PowerShell / Linux / Mac
python -m uvicorn backend.main:app --reload --port 8000
```

后端将在 `http://localhost:8000` 启动。

### 2. 启动 Streamlit 前端

打开新的终端窗口，在项目根目录下运行：

```bash
# Windows PowerShell / Linux / Mac
cd frontend
streamlit run app.py

# 或者从项目根目录
streamlit run frontend/app.py
```

前端将在 `http://localhost:8501` 启动。

## 验证安装

### 检查后端

访问 `http://localhost:8000/docs` 查看 FastAPI 自动生成的 API 文档。

访问 `http://localhost:8000/health` 应该返回：
```json
{"status": "healthy"}
```

### 检查前端

浏览器会自动打开 Streamlit 应用，或者手动访问 `http://localhost:8501`。

## 环境配置（可选）

在 `frontend` 目录下创建 `.env` 文件（如果后端不在默认地址）：

```
API_BASE_URL=http://localhost:8000
```

## 常见问题

### 1. 端口被占用

如果 8000 或 8501 端口被占用，可以修改：

**后端：**
```bash
python -m uvicorn backend.main:app --reload --port 8001
```

**前端：**
修改 `frontend/config.py` 中的 `API_BASE_URL`，或设置环境变量。

### 2. 导入错误

**确保从项目根目录运行命令！**

如果仍然遇到导入错误，设置 PYTHONPATH：

```bash
# Windows PowerShell
$env:PYTHONPATH = "D:\repo\OmniKnowledgeBase"

# Linux/Mac
export PYTHONPATH=$PWD
```

### 3. 依赖缺失

安装缺失的依赖：

```bash
pip install streamlit httpx python-dotenv pandas
```

## 开发模式

### 后端热重载

使用 `--reload` 参数（已包含在上面的命令中），代码修改后会自动重启。

### 前端热重载

Streamlit 默认支持热重载，修改代码后会自动刷新。

## 生产部署

### 后端

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 前端

```bash
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
```

## 下一步

1. 访问 `http://localhost:8501` 查看前端界面
2. 尝试上传文档（Documents 页面）
3. 测试 RAG 查询（RAG Query 页面）
4. 体验 Agentic Search（Agentic Search 页面）

