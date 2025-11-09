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

**⚠️ 重要提示：**

1. **`EMBEDDING_MODEL` 是必需配置项**，必须在 `.env` 文件中设置！
2. 索引和查询必须使用相同的embedding模型！
3. ChromaDB集合会根据第一个文档的embedding维度锁定集合维度。如果后续使用不同维度的模型查询，会导致错误。

**如果没有设置 `EMBEDDING_MODEL`，程序将无法启动并显示错误提示。**

```bash
# 选择Embedding提供商：local, zhipu, baidu, alibaba, openai
EMBEDDING_PROVIDER=local

# 本地模型配置（⚠️ 必需设置）
# 默认推荐：BAAI/bge-base-zh-v1.5 (768维，中文，性能与资源平衡)
EMBEDDING_MODEL=BAAI/bge-base-zh-v1.5  # ⚠️ 必须设置此配置项
# EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5  # 512 dimensions (轻量级)
# EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5  # 1024 dimensions (最佳性能)
# EMBEDDING_MODEL=all-MiniLM-L6-v2  # 384 dimensions (英文模型)

# 多语言模型（支持100+语言，适合中英文混合场景）
# EMBEDDING_MODEL=BAAI/bge-m3  # 1024 dimensions (多语言，推荐)
# EMBEDDING_MODEL=intfloat/multilingual-e5-base  # 768 dimensions (多语言基础版)
# EMBEDDING_MODEL=intfloat/multilingual-e5-large  # 1024 dimensions (多语言大型版)

# 代码专用模型（适合代码知识库）
# EMBEDDING_MODEL=microsoft/codebert-base  # 768 dimensions (代码专用)
# EMBEDDING_MODEL=Salesforce/codet5-base  # 768 dimensions (代码专用)
# EMBEDDING_MODEL=microsoft/unilm-base-cased  # 768 dimensions (文本+代码统一模型)

EMBEDDING_DEVICE=auto  # auto, cpu, cuda

# Hugging Face 模型缓存目录配置（可选）
# 默认情况下，Hugging Face 模型会下载到 C:\Users\<用户名>\.cache\huggingface\hub
# 如果 C 盘空间不足，可以通过以下方式更改缓存目录：
# 方式1：在 .env 文件中设置（推荐）
HF_CACHE_DIR=D:\huggingface_cache\hub
# 方式2：直接设置 HF_HUB_CACHE（优先级更高）
# HF_HUB_CACHE=D:\huggingface_cache\hub
# 方式3：设置 HF_HOME（缓存会在 $HF_HOME/hub 下）
# HF_HOME=D:\huggingface_cache
# 注意：如果未设置，默认使用 D:\huggingface_cache\hub

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

**常见embedding模型维度：**

**中文模型：**

- `BAAI/bge-small-zh-v1.5`: 512维（中文，轻量级）
- `BAAI/bge-base-zh-v1.5`: 768维（中文，**默认推荐**，性能与资源平衡）
- `BAAI/bge-large-zh-v1.5`: 1024维（中文，最佳性能）

**英文模型：**

- `all-MiniLM-L6-v2`: 384维（英文）
- `BAAI/bge-base-en-v1.5`: 768维（英文）

**多语言模型（✅ 已支持）：**

- `BAAI/bge-m3`: 1024维（支持100+语言，推荐用于中英文混合）
- `intfloat/multilingual-e5-base`: 768维（多语言基础版）
- `intfloat/multilingual-e5-large`: 1024维（多语言大型版）

**代码专用模型（✅ 已支持）：**

- `microsoft/codebert-base`: 768维（代码专用，支持多种编程语言）
- `Salesforce/codet5-base`: 768维（代码专用，代码理解和生成）
- `microsoft/unilm-base-cased`: 768维（统一模型，同时支持文本和代码）

**注意：** 所有模型配置现在通过全局 `embedding_config` 统一管理，确保维度一致性，避免维度不匹配问题。

**检查embedding维度：**

```bash
python -m backend.app.utils.check_embedding_dim
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
EMBEDDING_MODEL=BAAI/bge-base-zh-v1.5  # 默认模型已升级

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

**默认模型已升级为 `BAAI/bge-base-zh-v1.5` (768维)**

**中文模型：**

- **BAAI/bge-small-zh-v1.5**: 轻量级中文embedding模型，512维，速度快，适合资源受限环境
- **BAAI/bge-base-zh-v1.5**: 标准中文embedding模型，768维，**默认推荐**，性能与资源消耗平衡
- **BAAI/bge-large-zh-v1.5**: 大型中文embedding模型，1024维，效果最佳，需要更多资源

**多语言模型（✅ 新增支持）：**

- **BAAI/bge-m3**: 多语言embedding模型，1024维，支持100+语言，推荐用于中英文混合场景
- **intfloat/multilingual-e5-base**: 多语言模型基础版，768维
- **intfloat/multilingual-e5-large**: 多语言模型大型版，1024维

**代码专用模型（✅ 新增支持）：**

- **microsoft/codebert-base**: 代码专用embedding模型，768维，支持多种编程语言
- **Salesforce/codet5-base**: 代码专用模型，768维，支持代码理解和生成
- **microsoft/unilm-base-cased**: 统一语言模型，768维，同时支持文本和代码

**统一配置说明：**

- 所有嵌入模型配置通过 `backend/app/utils/embedding_config.py` 统一管理
- `EmbeddingService` 自动使用全局 `embedding_config`，确保维度一致性
- 模型维度信息存储在 `MODEL_DIMENSIONS` 映射中，避免硬编码

**语言支持说明：**

- ✅ **新增支持**：多语言模型（bge-m3、multilingual-e5）和代码模型（CodeBERT、CodeT5）
- 中文模型（如 bge-base-zh-v1.5）可以处理英文和代码，但性能会有所下降
- 如需处理多语言或代码，请参考语言支持指南选择合适的模型

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

