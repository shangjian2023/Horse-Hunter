# FinBrain 快速开始指南

## 1. 环境准备

### 安装依赖

```bash
cd C:\Users\共产主义接班人\OneDrive\Desktop\泰迪杯
pip install -r requirements.txt
```

### 配置 API Key（可选）

编辑 `.env` 文件：

```bash
# DeepSeek API 配置
LLM_API_KEY=sk-76f4b259f25147879777441ce24a0644
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

---

## 2. 运行测试

### 完整测试套件

```bash
python test_finbrain.py
```

预期输出：
```
============================================================
测试报告
============================================================
  LLM 客户端：PASS
  财报解析器：PASS
  任务规划器：PASS
  NL2SQL: PASS
  可视化：PASS

总计：5/5 通过
```

---

## 3. 使用命令行工具

### 运行完整流水线

```bash
python src/main.py --api-key "sk-76f4b259f25147879777441ce24a0644"
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--data-dir` | 数据目录 | `./B 题 - 示例数据/示例数据` |
| `--output-dir` | 输出目录 | `./result` |
| `--task2` | 任务二问题文件 | 自动查找附件 4 |
| `--task3` | 任务三问题文件 | 自动查找附件 6 |
| `--api-key` | API Key | 从.env 读取 |
| `--api-base` | API Base URL | DeepSeek 默认 |

---

## 4. Python API 调用

### 财报解析

```python
from src.etl.financial_parser import FinancialParser

parser = FinancialParser()

# 解析单个文件
result = parser.parse_pdf("600080_20230428_FQ2V.pdf")

# 解析目录
results = parser.parse_directory("./reports/")

# 保存为 CSV
parser.save_to_csv(results)
```

### 任务规划

```python
from src.agent.task_planner import TaskPlanner

planner = TaskPlanner()

# 拆解复杂问题
plan = planner.decompose_question("Top 10 企业对比及原因分析")

# 查看任务序列
for task in plan.sub_tasks:
    print(f"[{task.task_type.value}] {task.description}")
```

### NL2SQL 转换

```python
from src.agent.nl2sql import NL2SQLConverter

converter = NL2SQLConverter()

# 生成 SQL
result = converter.convert("贵州茅台 2024 年的净利润是多少？")
print(f"SQL: {result.sql}")
print(f"有效：{result.is_valid}")
```

### 可视化生成

```python
from src.agent.visualization import VisualizationEngine
import pandas as pd

viz = VisualizationEngine(output_dir="./result")

# 准备数据
df = pd.DataFrame({
    'company_name': ['贵州茅台', '五粮液', '泸州老窖'],
    'net_profit': [750, 320, 150]
})

# 生成图表
chart_path = viz.create_chart(
    df,
    "净利润排名",
    question_id="B002_01"
)
print(f"图表已保存：{chart_path}")
```

### RAG 检索

```python
from src.rag.retriever import RAGRetriever

rag = RAGRetriever(knowledge_base_path="./data/knowledge_base")

# 初始化（首次需要构建向量存储）
rag.initialize()

# 检索并生成答案
result = rag.retrieve_and_answer("医药行业的政策环境如何？")

print(f"答案：{result['answer']}")
print(f"参考来源：{len(result['references'])} 个")

for ref in result['references']:
    print(f"  - {ref['source']}: {ref['content'][:50]}...")
```

---

## 5. 输出文件说明

### 任务二输出 (result/task2_output.xlsx)

| 列名 | 说明 |
|------|------|
| 问题编号 | B002_01, B002_02, ... |
| 问题 | 原始问题 |
| SQL | 生成的 SQL |
| 图表路径 | ./result/B002_01_01.jpg |
| 时间戳 | ISO 8601 |

### 任务三输出 (result/task3_output.xlsx)

| 列名 | 说明 |
|------|------|
| 问题编号 | B003_01, B003_02, ... |
| 问题 | 原始问题 |
| SQL | 生成的 SQL |
| 图表路径 | ./result/B003_01_01.jpg |
| 答案 | RAG 生成的答案 |
| references | JSON 格式的参考来源 |

---

## 6. 常见问题

### Q: PDF 解析失败怎么办？

A: 检查：
1. PDF 文件路径是否正确
2. 是否安装了 `pdfplumber` 和 `PyMuPDF`
3. PDF 是否为扫描版（需要 OCR）

### Q: SQL 生成不准确？

A: 可以尝试：
1. 配置更强大的 LLM（如 deepseek-chat）
2. 在 `nl2sql.py` 中添加更多 Few-shot 示例
3. 手动调整 Schema 定义

### Q: 图表中文字符显示为方框？

A: 安装中文字体或修改 `visualization.py` 中的字体路径：
```python
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
```

### Q: RAG 检索不到相关内容？

A: 确保：
1. `knowledge_base` 目录存在且有 PDF 文件
2. 首次运行时正确构建了向量存储
3. 查询词与文档内容相关

---

## 7. 下一步

1. 阅读 `FINBRAIN_IMPLEMENTATION.md` 了解完整架构
2. 查看 `src/main.py` 学习流水线组织
3. 运行完整测试验证所有功能
4. 根据实际数据调整参数和配置

---

*文档创建：2026-03-23*
