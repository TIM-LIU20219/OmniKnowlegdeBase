"""
验收脚本：测试PDF文本清洗和分块效果

该脚本会：
1. 提取PDF原始文本
2. 展示清洗前后的对比
3. 展示分块结果
4. 将结果保存为markdown文件

Usage:
    python backend/app/utils/validate_cleaning_chunking.py <pdf_path>
    # OR from project root:
    python -m backend.app.utils.validate_cleaning_chunking <pdf_path>
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Add project root to Python path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.services.chunking_service import ChunkingService, ChunkingStrategy
from backend.app.utils.pdf_extractor import PDFExtractor
from backend.app.utils.text_cleaner import TextCleaner


def extract_raw_pdf_text(pdf_path: Path, backend: Optional[str] = None) -> Tuple[str, str]:
    """
    提取PDF原始文本（未清洗），支持多种后端。

    Args:
        pdf_path: PDF文件路径
        backend: 可选的后端选择 ('pymupdf', 'pdfplumber', 'pypdf')

    Returns:
        (原始提取的文本, 使用的后端)
    """
    extractor = PDFExtractor(preferred_backend=backend)
    text, backend_used = extractor.extract_with_fallback(pdf_path)
    return text, backend_used


def generate_report(
    pdf_path: Path,
    raw_text: str,
    cleaned_text: str,
    chunks: list,
    output_path: Path,
    backend_used: str = "unknown",
    strategy: str = "unknown",
) -> None:
    """
    生成markdown格式的验收报告。

    Args:
        pdf_path: PDF文件路径
        raw_text: 原始文本
        cleaned_text: 清洗后的文本
        chunks: 分块列表
        output_path: 输出文件路径
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 计算统计信息
    raw_lines = len(raw_text.split("\n"))
    cleaned_lines = len(cleaned_text.split("\n"))
    raw_chars = len(raw_text)
    cleaned_chars = len(cleaned_text)
    reduction_ratio = (
        (raw_chars - cleaned_chars) / raw_chars * 100 if raw_chars > 0 else 0
    )
    
    # 检测被过滤的特殊字段（简化版本，只显示示例）
    # 注意：由于清洗可能改变行的格式，这里只做简单对比
    filtered_lines = []
    raw_lines_set = {line.strip() for line in raw_text.split("\n") if line.strip()}
    cleaned_lines_set = {line.strip() for line in cleaned_text.split("\n") if line.strip()}
    filtered_lines = list(raw_lines_set - cleaned_lines_set)[:10]  # 只取前10个示例
    
    # 生成markdown内容
    markdown_content = f"""# PDF文本清洗和分块验收报告

## 基本信息

- **PDF文件**: `{pdf_path.name}`
- **文件路径**: `{pdf_path}`
- **生成时间**: {timestamp}
- **PDF提取后端**: `{backend_used}`
- **分块策略**: `{strategy}`

## 统计信息

### 文本统计

| 指标 | 原始文本 | 清洗后文本 | 变化 |
|------|---------|-----------|------|
| 字符数 | {raw_chars:,} | {cleaned_chars:,} | -{raw_chars - cleaned_chars:,} ({reduction_ratio:.1f}%) |
| 行数 | {raw_lines:,} | {cleaned_lines:,} | -{raw_lines - cleaned_lines:,} |
| 分块数量 | - | {len(chunks)} | - |

### 分块统计

- **总chunk数**: {len(chunks)}
- **平均chunk长度**: {sum(len(c) for c in chunks) / len(chunks):.0f} 字符
- **最大chunk长度**: {max(len(c) for c in chunks) if chunks else 0} 字符
- **最小chunk长度**: {min(len(c) for c in chunks) if chunks else 0} 字符

## 1. 原始文本（前500字符）

```
{raw_text[:500]}
...
```

## 2. 清洗后文本（前500字符）

```
{cleaned_text[:500]}
...
```

## 3. 文本对比

### 被过滤的内容示例

以下是被清洗过程过滤掉的内容（前10行）：

"""
    
    # 添加被过滤的行
    if filtered_lines:
        filtered_sample = list(filtered_lines)[:10]
        for i, line in enumerate(filtered_sample, 1):
            markdown_content += f"{i}. `{line[:100]}{'...' if len(line) > 100 else ''}`\n"
    else:
        markdown_content += "无被过滤的内容。\n"
    
    markdown_content += f"""
## 4. 分块结果

共生成 **{len(chunks)}** 个chunk：

"""
    
    # 添加每个chunk的详细信息
    for i, chunk in enumerate(chunks, 1):
        chunk_preview = chunk[:200] + "..." if len(chunk) > 200 else chunk
        is_reference = TextCleaner.is_reference_section(chunk)
        reference_marker = " ⚠️ **参考文献section**" if is_reference else ""
        
        markdown_content += f"""### Chunk {i}{reference_marker}

- **长度**: {len(chunk)} 字符
- **预览**:
```
{chunk_preview}
```

"""
    
    # 添加完整文本对比（如果不太长）
    if raw_chars < 10000:
        markdown_content += f"""
## 5. 完整文本对比

### 原始文本（完整）

```
{raw_text}
```

### 清洗后文本（完整）

```
{cleaned_text}
```

"""
    
    # 保存文件
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown_content, encoding="utf-8")
    print(f"✅ 报告已保存到: {output_path}")


def validate_pdf(
    pdf_path: Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    output_dir: Path = None,
    strategy: str = ChunkingStrategy.HYBRID,
) -> Tuple[str, str, list]:
    """
    验证PDF的文本清洗和分块效果。

    Args:
        pdf_path: PDF文件路径
        chunk_size: 分块大小
        chunk_overlap: 分块重叠大小
        output_dir: 输出目录（如果为None，使用PDF所在目录）

    Returns:
        (raw_text, cleaned_text, chunks) 元组
    """
    print("=" * 80)
    print("PDF文本清洗和分块验收")
    print("=" * 80)
    print(f"\n处理文件: {pdf_path}")
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
    
    # 1. 提取原始文本
    print("\n[1/4] 提取PDF原始文本...")
    raw_text, backend_used = extract_raw_pdf_text(pdf_path)
    print(f"   ✅ 提取完成: {len(raw_text):,} 字符, {len(raw_text.split('\n')):,} 行")
    print(f"   📚 使用的后端: {backend_used}")
    
    # 2. 清洗文本
    print("\n[2/4] 清洗文本...")
    cleaned_text = TextCleaner.clean_pdf_text(raw_text)
    print(f"   ✅ 清洗完成: {len(cleaned_text):,} 字符, {len(cleaned_text.split('\n')):,} 行")
    reduction = len(raw_text) - len(cleaned_text)
    if reduction > 0:
        print(f"   📉 减少了 {reduction:,} 字符 ({reduction/len(raw_text)*100:.1f}%)")
    
    # 3. 分块
    print("\n[3/4] 分块文本...")
    print(f"   📋 分块策略: {strategy}")
    chunking_service = ChunkingService(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, strategy=strategy
    )
    chunks = chunking_service.chunk_text(cleaned_text)
    print(f"   ✅ 分块完成: {len(chunks)} 个chunk")
    
    # 检查是否有参考文献section被过滤
    reference_chunks = [
        i for i, chunk in enumerate(chunks, 1) 
        if TextCleaner.is_reference_section(chunk)
    ]
    if reference_chunks:
        print(f"   ⚠️  检测到 {len(reference_chunks)} 个参考文献section: {reference_chunks}")
    else:
        print(f"   ✅ 未检测到参考文献section")
    
    # 4. 生成报告
    print("\n[4/4] 生成验收报告...")
    if output_dir is None:
        output_dir = pdf_path.parent
    
    output_filename = f"{pdf_path.stem}_cleaning_chunking_report.md"
    output_path = output_dir / output_filename
    
    generate_report(pdf_path, raw_text, cleaned_text, chunks, output_path, backend_used, strategy)
    
    print("\n" + "=" * 80)
    print("✅ 验收完成！")
    print("=" * 80)
    print(f"\n📄 报告位置: {output_path}")
    print(f"\n📊 摘要:")
    print(f"   - 原始文本: {len(raw_text):,} 字符")
    print(f"   - 清洗后: {len(cleaned_text):,} 字符")
    print(f"   - 分块数量: {len(chunks)}")
    print(f"   - 平均chunk长度: {sum(len(c) for c in chunks) / len(chunks):.0f} 字符")
    
    return raw_text, cleaned_text, chunks


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="验收PDF文本清洗和分块效果",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "pdf_path",
        type=str,
        help="PDF文件路径",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="分块大小（默认: 1000）",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="分块重叠大小（默认: 200）",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="输出目录（默认: PDF所在目录）",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default=ChunkingStrategy.HYBRID,
        choices=["character", "sentence", "paragraph", "hybrid"],
        help=f"分块策略（默认: {ChunkingStrategy.HYBRID}）",
    )
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_path).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    
    try:
        validate_pdf(
            pdf_path=pdf_path,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            output_dir=output_dir,
            strategy=args.strategy,
        )
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

