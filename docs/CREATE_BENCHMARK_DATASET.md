# 如何构建 textbook_benchmark.json 数据集

本指南说明如何从 PDF 教材创建 RAG 评估用的 benchmark 数据集。

---

## 📋 数据集格式

`textbook_benchmark.json` 是一个 JSON 文件，包含以下结构：

```json
{
  "dataset_name": "textbook_benchmark",
  "description": "Benchmark dataset based on PDF textbook",
  "questions": [
    {
      "question_id": "textbook_001",
      "question": "What is the main topic of Chapter 1?",
      "ground_truth_answer": "Chapter 1 introduces the fundamental concepts of...",
      "context_doc_ids": ["doc_id_from_pdf"],
      "metadata": {
        "category": "factual",
        "difficulty": "easy",
        "chapter": "1"
      }
    }
  ],
  "metadata": {
    "version": "1.0",
    "created_date": "2024-01-XX",
    "total_questions": 10
  }
}
```

### 字段说明

- **question_id**: 唯一的问题标识符（如 `textbook_001`）
- **question**: 问题文本
- **ground_truth_answer**: 标准答案（期望 RAG 系统生成的答案）
- **context_doc_ids**: 包含答案的文档 ID 列表（PDF 导入后生成的 doc_id）
- **metadata**: 可选的元数据（类别、难度、章节等）

---

## 🚀 快速开始

### 方法 1: 使用交互式工具（推荐）

1. **确保 PDF 已导入**

   首先将 PDF 教材导入到 ChromaDB：

   ```bash
   # 使用测试脚本导入（如果还没有 CLI）
   python backend/test_document_processing.py
   
   # 或者使用未来的 CLI（Phase 1.2 完成后）
   # python -m backend.app.cli document add --pdf textbook.pdf
   ```

2. **运行交互式创建工具**

   ```bash
   python backend/app/utils/create_textbook_benchmark.py
   ```

3. **按提示操作**

   - 输入数据集名称（如 `textbook_benchmark`）
   - 输入描述
   - 查看可用的文档列表
   - 逐个创建问题：
     - 输入问题 ID
     - 输入问题文本
     - 输入标准答案
     - 工具会自动搜索相关文档，或手动选择文档 ID
     - 可选：添加元数据

4. **保存数据集**

   工具会自动保存到 `benchmark_data/textbook_benchmark.json`

---

### 方法 2: 手动创建 JSON 文件

1. **获取文档 ID**

   首先需要知道 PDF 导入后的文档 ID：

   ```bash
   # 使用检查脚本查看文档
   python backend/inspect_chromadb.py
   ```

   或者使用 Python：

   ```python
   from backend.app.services.vector_service import VectorService
   
   vector_service = VectorService()
   collection = vector_service.get_documents_collection()
   results = collection.get()
   
   # 查看所有文档 ID
   doc_ids = set()
   for metadata in results.get("metadatas", []):
       doc_id = metadata.get("doc_id")
       if doc_id:
           doc_ids.add(doc_id)
   
   print("Document IDs:", list(doc_ids))
   ```

2. **创建 JSON 文件**

   创建 `benchmark_data/textbook_benchmark.json`：

   ```json
   {
     "dataset_name": "textbook_benchmark",
     "description": "Benchmark dataset based on PDF textbook",
     "questions": [
       {
         "question_id": "textbook_001",
         "question": "你的第一个问题",
         "ground_truth_answer": "标准答案",
         "context_doc_ids": ["你的文档ID"],
         "metadata": {
           "category": "factual",
           "difficulty": "easy"
         }
       }
     ],
     "metadata": {
       "version": "1.0",
       "created_date": "2024-01-XX"
     }
   }
   ```

3. **验证格式**

   ```bash
   python -c "
   from backend.app.services.benchmark_evaluator import load_benchmark_dataset
   from pathlib import Path
   
   dataset = load_benchmark_dataset(Path('benchmark_data/textbook_benchmark.json'))
   print(f'Dataset loaded: {dataset.dataset_name}')
   print(f'Questions: {len(dataset.questions)}')
   "
   ```

---

### 方法 3: 使用模板文件

1. **创建模板文件**

   创建 `benchmark_data/textbook_template.json`：

   ```json
   {
     "dataset_name": "textbook_benchmark",
     "description": "Benchmark dataset based on PDF textbook",
     "questions": [],
     "metadata": {
       "version": "1.0"
     }
   }
   ```

2. **填充问题**

   手动编辑模板文件，添加问题。

3. **使用工具加载**

   ```bash
   python backend/app/utils/create_textbook_benchmark.py \
     --mode template \
     --template benchmark_data/textbook_template.json \
     --output benchmark_data/textbook_benchmark.json
   ```

---

## 📝 创建高质量问题的建议

### 问题类型

1. **事实性问题（Factual）**
   - 直接询问文档中的具体信息
   - 例如："What is the definition of X?"
   - 难度：简单

2. **推理性问题（Reasoning）**
   - 需要基于文档内容进行推理
   - 例如："Why does X happen when Y occurs?"
   - 难度：中等

3. **总结性问题（Summarization）**
   - 要求总结或概括文档内容
   - 例如："Summarize the main points of Chapter 2"
   - 难度：中等-困难

4. **比较性问题（Comparison）**
   - 比较文档中的不同概念
   - 例如："What are the differences between X and Y?"
   - 难度：中等-困难

### 问题分布建议

- **简单问题**: 30-40%（测试基础检索能力）
- **中等问题**: 40-50%（测试检索+生成能力）
- **困难问题**: 10-20%（测试复杂推理能力）

### 标准答案编写建议

1. **准确性**: 答案必须准确反映文档内容
2. **完整性**: 答案应该完整回答问题
3. **简洁性**: 避免过于冗长，但包含关键信息
4. **可评估性**: 答案应该能够与 RAG 输出进行对比

---

## 🔍 查找相关文档 ID

### 方法 1: 使用交互式工具

运行创建工具时，工具会自动搜索相关文档：

```bash
python backend/app/utils/create_textbook_benchmark.py
```

输入问题后，工具会显示最相关的文档。

### 方法 2: 使用 Python 脚本

```python
from backend.app.services.vector_service import VectorService
from backend.app.services.embedding_service import EmbeddingService

vector_service = VectorService()
embedding_service = EmbeddingService()

# 搜索相关文档
query = "你的问题"
query_embedding = embedding_service.embed_text(query)

results = vector_service.query(
    collection_name="documents",
    query_embeddings=[query_embedding],
    n_results=5,
)

# 提取文档 ID
doc_ids = set()
for metadata in results.get("metadatas", [[]])[0]:
    doc_id = metadata.get("doc_id")
    if doc_id:
        doc_ids.add(doc_id)

print("Relevant document IDs:", list(doc_ids))
```

### 方法 3: 手动查找

1. 查看所有文档：

   ```bash
   python backend/inspect_chromadb.py
   ```

2. 根据文档标题和内容确定 doc_id

---

## ✅ 验证数据集

创建数据集后，验证格式是否正确：

```bash
python -c "
from backend.app.services.benchmark_evaluator import load_benchmark_dataset
from pathlib import Path

try:
    dataset = load_benchmark_dataset(Path('benchmark_data/textbook_benchmark.json'))
    print(f'✅ Dataset loaded successfully!')
    print(f'   Name: {dataset.dataset_name}')
    print(f'   Questions: {len(dataset.questions)}')
    print(f'   Description: {dataset.description}')
    
    # 验证每个问题
    for i, q in enumerate(dataset.questions, 1):
        if not q.context_doc_ids:
            print(f'⚠️  Question {i} ({q.question_id}) has no context_doc_ids')
        if not q.ground_truth_answer:
            print(f'⚠️  Question {i} ({q.question_id}) has no ground_truth_answer')
    
    print('✅ Validation complete!')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

---

## 🧪 运行评估

创建数据集后，运行评估：

```bash
python -m backend.app.scripts.run_benchmark \
  --dataset benchmark_data/textbook_benchmark.json \
  --collection documents \
  --k 4 \
  --output benchmark_results/textbook_baseline.json
```

---

## 📊 示例：31 页 PDF 教材数据集

假设你有一本 31 页的 PDF 教材，建议创建：

- **总问题数**: 20-30 个问题
- **分布**:
  - 每章 2-3 个问题
  - 涵盖不同难度级别
  - 涵盖不同问题类型

### 示例问题结构

```json
{
  "dataset_name": "textbook_benchmark",
  "description": "Benchmark dataset for 31-page PDF textbook",
  "questions": [
    {
      "question_id": "textbook_ch1_001",
      "question": "What is the main topic introduced in Chapter 1?",
      "ground_truth_answer": "Chapter 1 introduces the fundamental concepts of...",
      "context_doc_ids": ["pdf_doc_id"],
      "metadata": {
        "category": "factual",
        "difficulty": "easy",
        "chapter": "1"
      }
    },
    {
      "question_id": "textbook_ch1_002",
      "question": "Explain the relationship between concept A and concept B.",
      "ground_truth_answer": "Concept A and concept B are related because...",
      "context_doc_ids": ["pdf_doc_id"],
      "metadata": {
        "category": "reasoning",
        "difficulty": "medium",
        "chapter": "1"
      }
    }
  ],
  "metadata": {
    "version": "1.0",
    "created_date": "2024-01-XX",
    "textbook_pages": 31,
    "total_questions": 25
  }
}
```

---

## 🛠️ 工具使用示例

### 交互式创建

```bash
$ python backend/app/utils/create_textbook_benchmark.py

============================================================
Benchmark Dataset Creator
============================================================

Dataset name (e.g., textbook_benchmark): textbook_benchmark
Description (optional): Benchmark for 31-page PDF textbook

============================================================
Available Documents in ChromaDB
============================================================
  1. PDF Textbook
     ID: abc123-def456-...
     Source: pdf
     Chunks: 45

============================================================
Creating Questions
============================================================

============================================================
Create New Question
============================================================

Question ID (e.g., textbook_001): textbook_001

Enter the question:
> What is the main topic of Chapter 1?

Enter the ground truth answer:
> Chapter 1 introduces the fundamental concepts of...

Searching for relevant documents...

Found relevant documents:
  1. PDF Textbook (ID: abc123-def456-...)
     Relevance: 0.856

Select document IDs (comma-separated numbers, or enter doc_ids directly):
> 1

Metadata (optional, JSON format, or press Enter to skip):
> {"category": "factual", "difficulty": "easy", "chapter": "1"}

✅ Question 'textbook_001' added. Total: 1

Add another question? (y/n): y
...
```

---

## 📚 相关文档

- [RAG Benchmark 文档](docs/RAG_BENCHMARK.md)
- [RAG Pipeline 状态](docs/RAG_PIPELINE_STATUS.md)
- [运行 RAG Pipeline](docs/RUN_RAG_PIPELINE.md)

---

## 💡 提示

1. **从简单开始**: 先创建 5-10 个简单问题，验证流程
2. **逐步扩展**: 根据评估结果，逐步添加更多问题
3. **记录文档 ID**: 保存 PDF 导入后的 doc_id，方便后续使用
4. **问题多样性**: 确保问题涵盖不同章节和难度
5. **定期更新**: 随着知识库扩展，更新 benchmark 数据集

