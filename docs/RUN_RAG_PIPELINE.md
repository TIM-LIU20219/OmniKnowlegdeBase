# RAG Pipeline 运行指南

## 前置条件

### 1. 安装依赖

确保已安装所有必需的Python包：

```bash
cd backend
pip install -r ../requirements.txt
```

或者单独安装新添加的依赖：

```bash
pip install langchain-openai
```

### 2. 配置环境变量

确保 `.env` 文件中包含以下配置：

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=your_api_key_here
LLM_PROVIDER=deepseek
DEEPSEEK_MODEL=deepseek-chat

# 可选：其他LLM配置
# LLM_TEMPERATURE=0.7
# LLM_MAX_TOKENS=2000
```

## 快速测试

### 方法1: 使用测试脚本

```bash
cd backend
python test_rag_pipeline.py
```

这个脚本会：
1. 初始化所有服务
2. 测试RAG查询功能
3. 显示结果

### 方法2: 在Python中直接使用

```python
from backend.app.services.rag_service import RAGService
from backend.app.services.vector_service import VectorService
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.llm_service import LLMService

# 初始化服务
vector_service = VectorService()
embedding_service = EmbeddingService()
llm_service = LLMService()

# 创建RAG服务
rag_service = RAGService(
    vector_service=vector_service,
    embedding_service=embedding_service,
    llm_service=llm_service,
    collection_name="documents",
    k=4,
)

# 查询
result = rag_service.query("你的问题")
print(result["answer"])
print(result["sources"])
```

## 注意事项

1. **文档数据**: 确保ChromaDB中已有文档数据。如果没有，需要先通过文档上传功能导入文档。

2. **API Key**: 确保 `DEEPSEEK_API_KEY` 在 `.env` 文件中正确配置。

3. **虚拟环境**: 建议在虚拟环境中运行：

```bash
# Windows
backend\venv\Scripts\activate

# Linux/Mac
source backend/venv/bin/activate
```

## 常见问题

### 1. ModuleNotFoundError: No module named 'langchain_openai'

**解决方案**: 安装缺失的依赖
```bash
pip install langchain-openai
```

### 2. API Key错误

**解决方案**: 检查 `.env` 文件中的 `DEEPSEEK_API_KEY` 是否正确配置

### 3. 没有检索到文档

**解决方案**: 
- 确保ChromaDB中有文档数据
- 检查collection名称是否正确（默认是"documents"）
- 尝试增加检索数量（增大k值）

### 4. LLM调用失败

**解决方案**:
- 检查网络连接
- 验证API key是否有效
- 检查API配额是否充足

## 下一步

1. **准备测试数据**: 导入一些文档到ChromaDB
2. **运行测试**: 使用测试脚本验证功能
3. **创建Benchmark**: 准备评估数据集
4. **调优**: 根据评估结果调整参数

