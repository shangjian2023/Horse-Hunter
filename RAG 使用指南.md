# RAG 知识库使用指南

## 功能概述

RAG（检索增强生成）功能将行业报告、企业信息等非结构化文档与结构化财报数据相结合，提供更全面的问答能力。

## 支持的文档类型

| 类型 | 扩展名 | 说明 |
|------|--------|------|
| PDF | .pdf | 行业研究报告、财报原文 |
| Word | .doc, .docx | 企业介绍、调研报告 |
| Excel | .xlsx, .xls | 行业数据、企业列表 |
| 文本 | .txt, .md | 笔记、摘要 |

## 快速开始

### 1. 准备文档

将行业报告、企业信息等文档放入目录：
```
B 题 - 示例数据/附件 5：行业报告/
├── 医药行业研究/
│   ├── 医药行业 2025 年报.pdf
│   └── 重点企业分析.docx
├── 新能源行业/
│   └── 发展趋势报告.pdf
└── 企业列表.xlsx
```

### 2. 初始化知识库

**命令行方式:**
```bash
python rag_init.py --init --data-dir "B 题 - 示例数据/附件 5：行业报告"
```

**Streamlit 界面:**
1. 启动应用：`streamlit run rag_chat_app.py`
2. 在侧边栏点击 "📚 初始化知识库"

### 3. 开始问答

**示例问题:**

| 类型 | 示例问题 |
|------|----------|
| 行业分析 | "医药行业的政策环境如何？" |
| 企业研究 | "华润三九的核心竞争优势是什么？" |
| 趋势分析 | "新能源行业未来发展趋势" |
| 对比分析 | "对比医药行业和新能源行业的盈利能力" |

## 使用方式

### 方式一：Streamlit 界面

```bash
# 启动 RAG 增强版智能问数助手
streamlit run rag_chat_app.py
```

访问 http://localhost:8501

### 方式二：Python API

```python
from models.rag.retriever import Retriever

# 创建检索器
retriever = Retriever()

# 加载文档
result = retriever.load_knowledge_directory("B 题 - 示例数据/附件 5：行业报告")
print(f"加载了 {result['valid_chunks']} 个文档片段")

# 检索并回答
answer = retriever.retrieve_and_answer("医药行业有哪些重点企业？")
print(f"回答：{answer['answer']}")
print(f"参考来源：{answer['references']}")
```

### 方式三：多跳推理

```python
from models.rag.retriever import Retriever

retriever = Retriever()

# 多跳推理（自动分解问题，多次检索）
result = retriever.multi_hop_retrieval(
    "医药行业中净利润最高的企业是哪家的？它的主要产品是什么？",
    max_hops=3
)

print(f"回答：{result['answer']}")
print(f"推理步骤：{result['reasoning_chain']}")
```

## 配置选项

### 环境变量 (.env 文件)

```ini
# LLM API 配置
ANTHROPIC_BASE_URL=https://your-api-endpoint.com
ANTHROPIC_AUTH_TOKEN=your-api-key

# 知识库存储路径
KNOWLEDGE_BASE_PATH=data/knowledge_base
```

### 分块参数

```python
from models.rag.document_loader import DocumentLoader

# chunk_size: 每块大小（字符数）
# chunk_overlap: 块之间重叠大小
loader = DocumentLoader(chunk_size=500, chunk_overlap=50)
```

## 高级功能

### 1. 自定义知识库路径

```python
from models.rag.knowledge_base import KnowledgeBase

kb = KnowledgeBase(persist_path="data/my_knowledge_base")
```

### 2. 批量加载文档

```python
from models.rag.document_loader import DocumentLoader

loader = DocumentLoader()

# 加载单个文件
chunks = loader.load_and_chunk("path/to/document.pdf")

# 加载整个目录
docs = loader.load_directory("path/to/docs")
```

### 3. 检索参数调优

```python
# top_k: 返回的相关文档数量
result = kb.search("查询问题", top_k=5)

# 增加 top_k 获取更全面的上下文
result = kb.search("复杂问题", top_k=10)
```

## 性能优化建议

1. **文档预处理**: 清理无关内容，保留核心信息
2. **合理分块**: 技术文档 500-800 字符，报告类 300-500 字符
3. **索引持久化**: 知识库会自动保存，避免重复加载
4. **批量检索**: 多个问题合并检索，减少 API 调用

## 常见问题

### Q: 知识库加载失败？
A: 检查文档路径是否正确，确保安装了 PyMuPDF、python-docx 等依赖

### Q: 检索结果不相关？
A: 尝试调整 top_k 参数，或优化问题表述

### Q: 回答质量不高？
A: 检查知识库文档质量，确保包含相关信息

## 下一步

- 集成到主应用 `app.py`
- 添加向量数据库（ChromaDB）支持
- 实现增量更新知识库
- 添加引用溯源功能
