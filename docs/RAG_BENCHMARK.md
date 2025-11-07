# RAG Benchmark 评估指南

## 概述

RAG Benchmark 评估系统用于评估和调优 RAG pipeline 的性能。它提供了完整的评估框架，包括数据集管理、指标计算和结果分析。

## 当前 RAG Pipeline 状态

### ✅ 已完成组件

1. **EmbeddingService** - 文本向量化
   - 支持多种 embedding 模型
   - GPU/CPU 自动检测
   - 批量处理优化

2. **VectorService** - ChromaDB 向量存储
   - 文档存储和检索
   - 元数据过滤
   - 多集合管理

3. **ChunkingService** - 文档分块
   - 多种分块策略
   - 重叠窗口支持
   - 句子边界识别

4. **Retriever** - LangChain 兼容检索器
   - ChromaDB 语义搜索
   - 相似度阈值过滤
   - 元数据过滤支持

5. **LLMService** - LLM 集成
   - 支持多种 provider (DeepSeek/OpenRouter/OpenAI)
   - 同步/异步调用
   - 流式响应支持

6. **RAGService** - 完整 RAG Pipeline
   - 检索增强生成
   - 上下文管理
   - 来源追踪

7. **BenchmarkEvaluator** - 评估系统
   - 检索指标（Precision/Recall/F1）
   - 答案质量指标
   - 自动化评估流程

## 评估指标

### 检索指标

- **Precision（精确率）**: 检索到的相关文档占比
- **Recall（召回率）**: 所有相关文档中被检索到的占比
- **F1 Score**: Precision 和 Recall 的调和平均

### 答案质量指标

- **Answer Similarity（答案相似度）**: 基于词汇重叠的相似度计算
- **Answer Length**: 答案长度统计
- **Context Length**: 使用的上下文长度

## 使用方法

### 1. 准备 Benchmark 数据集

创建一个 JSON 格式的 benchmark 数据集：

```json
{
  "dataset_name": "my_benchmark",
  "description": "My custom benchmark",
  "questions": [
    {
      "question_id": "q001",
      "question": "What is the default chunk size?",
      "ground_truth_answer": "The default chunk size is 1000 characters.",
      "context_doc_ids": ["doc_id_1", "doc_id_2"],
      "metadata": {
        "category": "configuration",
        "difficulty": "easy"
      }
    }
  ],
  "metadata": {
    "version": "1.0"
  }
}
```

### 2. 创建示例数据集

```bash
cd backend
python -m app.utils.create_example_benchmark
```

这将创建 `benchmark_data/example_dataset.json`。

### 3. 运行评估

```bash
cd backend
python -m app.scripts.run_benchmark \
  --dataset benchmark_data/example_dataset.json \
  --collection documents \
  --k 4 \
  --output benchmark_results.json
```

### 4. 查看结果

结果会保存为 JSON 文件，包含：
- 摘要统计（Summary）
- 详细结果（Detailed Results）

## 评估流程

1. **数据准备**: 确保文档已导入 ChromaDB
2. **数据集创建**: 创建包含问题和标准答案的数据集
3. **运行评估**: 执行评估脚本
4. **结果分析**: 查看指标，识别需要改进的地方
5. **调优迭代**: 调整参数（chunk_size, k, prompt等）后重新评估

## 调优建议

### 检索优化

- **调整 k 值**: 增加检索文档数量（但可能引入噪声）
- **相似度阈值**: 过滤低质量检索结果
- **Chunk 大小**: 影响检索粒度和上下文质量
- **Embedding 模型**: 更换更强大的模型可能提升检索质量

### 生成优化

- **Prompt 模板**: 优化提示词以提高答案质量
- **上下文长度**: 平衡上下文信息和token限制
- **LLM 参数**: 调整 temperature, max_tokens 等

## 下一步工作

### 可选的增强功能

1. **更高级的评估指标**
   - BLEU/ROUGE 分数
   - 语义相似度（使用 embedding）
   - 人工评估接口

2. **自动调优工具**
   - 超参数搜索
   - A/B 测试框架
   - 性能对比报告

3. **更多评估数据集**
   - 领域特定数据集
   - 多语言支持
   - 对抗样本测试

4. **可视化工具**
   - 评估结果可视化
   - 性能趋势分析
   - 错误案例分析

## 文件结构

```
backend/
├── app/
│   ├── models/
│   │   └── benchmark.py          # Benchmark 数据模型
│   ├── services/
│   │   ├── retriever.py          # 检索器包装
│   │   ├── llm_service.py        # LLM 服务
│   │   ├── rag_service.py        # RAG 服务
│   │   └── benchmark_evaluator.py # 评估器
│   ├── scripts/
│   │   └── run_benchmark.py     # 评估脚本
│   └── utils/
│       └── create_example_benchmark.py # 示例数据集生成
└── benchmark_data/              # Benchmark 数据集目录
    └── example_dataset.json
```

## 注意事项

1. **文档 ID 匹配**: 确保 benchmark 数据集中的 `context_doc_ids` 与实际存储的文档 ID 匹配
2. **LLM API 配置**: 确保 `.env` 文件中配置了正确的 LLM API key
3. **评估成本**: 大量评估会消耗 LLM API 调用，注意成本控制
4. **数据集质量**: 高质量的标准答案对评估结果至关重要

