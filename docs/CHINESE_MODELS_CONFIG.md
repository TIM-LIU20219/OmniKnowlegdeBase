# 中国模型服务配置指南

本文档说明如何配置和使用中国的模型服务（Chat、Embedding、Rerank）。

## 环境变量配置

在项目根目录创建或编辑 `.env` 文件，添加以下配置：

### LLM Chat 模型配置

```bash
# 选择LLM提供商：deepseek, zhipu, baidu, alibaba, openrouter, openai
LLM_PROVIDER=deepseek

# DeepSeek配置
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 智谱AI配置
ZHIPU_API_KEY=your_zhipu_api_key
ZHIPU_API_BASE=https://open.bigmodel.cn/api/paas/v4
ZHIPU_MODEL=glm-4

# 百度文心配置
BAIDU_API_KEY=your_baidu_api_key
BAIDU_API_SECRET=your_baidu_api_secret
BAIDU_API_BASE=https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat
BAIDU_MODEL=ernie-bot-turbo

# 阿里通义配置
ALIBABA_API_KEY=your_alibaba_api_key
ALIBABA_API_BASE=https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation
ALIBABA_MODEL=qwen-turbo

# LLM通用配置
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=60
```

### Embedding 模型配置

```bash
# 选择Embedding提供商：local, zhipu, baidu, alibaba, openai
EMBEDDING_PROVIDER=local

# 本地模型配置（推荐使用中文模型）
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
EMBEDDING_DEVICE=auto  # auto, cpu, cuda

# 智谱AI Embedding配置
ZHIPU_EMBEDDING_API_BASE=https://open.bigmodel.cn/api/paas/v4/embeddings
ZHIPU_EMBEDDING_MODEL=embedding-2

# 百度文心 Embedding配置
BAIDU_EMBEDDING_API_BASE=https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings
BAIDU_EMBEDDING_MODEL=text-embedding

# 阿里通义 Embedding配置
ALIBABA_EMBEDDING_API_BASE=https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding
ALIBABA_EMBEDDING_MODEL=text-embedding-v2
```

### Rerank 模型配置

```bash
# 选择Rerank提供商：local, zhipu, baidu, alibaba, openai
RERANK_PROVIDER=local

# 本地Rerank模型配置（推荐使用中文模型）
RERANK_MODEL=BAAI/bge-reranker-base

# 智谱AI Rerank配置
ZHIPU_RERANK_API_BASE=https://open.bigmodel.cn/api/paas/v4/rerank
ZHIPU_RERANK_MODEL=rerank

# 阿里通义 Rerank配置
ALIBABA_RERANK_API_BASE=https://dashscope.aliyuncs.com/api/v1/services/rerank/rerank
ALIBABA_RERANK_MODEL=rerank-v1
```

## 推荐配置

### 方案1：全本地模型（免费，适合开发测试）

```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key

EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5

RERANK_PROVIDER=local
RERANK_MODEL=BAAI/bge-reranker-base
```

### 方案2：中国云服务（推荐生产环境）

```bash
# Chat使用DeepSeek或智谱AI
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key

# Embedding使用智谱AI或阿里通义
EMBEDDING_PROVIDER=zhipu
ZHIPU_API_KEY=your_key

# Rerank使用本地模型或阿里通义
RERANK_PROVIDER=local
RERANK_MODEL=BAAI/bge-reranker-base
```

## 中文模型推荐

### Embedding模型
- **BAAI/bge-small-zh-v1.5**: 轻量级中文embedding模型，速度快
- **BAAI/bge-base-zh-v1.5**: 标准中文embedding模型，效果更好
- **BAAI/bge-large-zh-v1.5**: 大型中文embedding模型，效果最佳

### Rerank模型
- **BAAI/bge-reranker-base**: 标准中文rerank模型
- **BAAI/bge-reranker-large**: 大型中文rerank模型，效果更好

## 使用示例

### 在代码中使用

```python
from backend.app.services.llm_service import LLMService
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.rerank_service import RerankService

# LLM服务（自动使用配置的provider）
llm_service = LLMService()
response = llm_service.invoke("你好")

# Embedding服务
embedding_service = EmbeddingService()
embedding = embedding_service.embed_text("文本内容")

# Rerank服务
rerank_service = RerankService()
reranked = rerank_service.rerank(
    query="查询内容",
    documents=["文档1", "文档2", "文档3"],
    top_k=2
)
```

## API密钥获取

### DeepSeek
- 访问：https://platform.deepseek.com/
- 注册账号并获取API密钥

### 智谱AI
- 访问：https://open.bigmodel.cn/
- 注册账号并获取API密钥

### 百度文心
- 访问：https://cloud.baidu.com/product/wenxinworkshop
- 注册账号并获取API Key和Secret Key

### 阿里通义
- 访问：https://dashscope.aliyuncs.com/
- 注册账号并获取API密钥

## 注意事项

1. **API密钥安全**：不要将 `.env` 文件提交到Git仓库
2. **模型选择**：中文任务推荐使用中文模型（BAAI系列）
3. **成本控制**：云服务API按调用次数计费，注意控制使用量
4. **网络要求**：使用中国云服务需要能访问相应API地址

