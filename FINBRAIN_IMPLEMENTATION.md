# FinBrain 上市公司财报智能问数系统 - 实现完成报告

## 项目概述

基于 2026 年"泰迪杯"B 题要求构建的全自动化财报智能问数系统，实现"自然语言 -> 意图识别 -> SQL 生成 -> 数据查询 -> 可视化 -> 分析结论"的完整链路。

---

## 系统架构

```
finbrain/
├── src/
│   ├── etl/                    # 模块 A：结构化财报 ETL 引擎
│   │   ├── financial_parser.py   # 多交易所 PDF 解析器
│   │   └── financial_validator.py # 财务勾稽关系校验器
│   │
│   ├── agent/                  # 模块 B：Agent 智能问数核心
│   │   ├── task_planner.py       # 多意图任务规划器
│   │   ├── nl2sql.py             # NL2SQL 转换器
│   │   └── visualization.py      # 自动化可视化引擎
│   │
│   ├── rag/                    # 模块 C：RAG 增强与归因分析
│   │   └── retriever.py          # 检索增强生成模块
│   │
│   ├── api/                    # API 接口层
│   │   └── llm_client.py         # 多模型 API 客户端
│   │
│   └── main.py                 # 主入口程序
│
├── test_finbrain.py            # 系统测试脚本
└── requirements.txt            # 依赖包列表
```

---

## 核心功能实现

### 模块 A：结构化财报 ETL 引擎

**FinancialParser 类** (`src/etl/financial_parser.py`)

| 功能 | 实现说明 |
|------|----------|
| 多源解析 | 上交所规则：`股票代码_报告日期_随机标识.pdf` |
| | 深交所规则：`A 股简称：年份 + 报告周期 + 报告类型.pdf` |
| 精准提取 | 从 PDF 中提取核心业绩指标、资产负债表、利润表、现金流量表 |
| 自动校验 | 调用 FinancialValidator 执行勾股关系校验 |

**FinancialValidator 类** (`src/etl/financial_validator.py`)

| 校验类型 | 勾稽关系 |
|----------|----------|
| 资产负债校验 | 资产总计 = 负债合计 + 所有者权益合计 |
| 利润表校验 | 利润总额 = 营业利润 + 营业外收入 - 营业外支出 |
| | 净利润 = 利润总额 - 所得税费用 |
| 现金流量表校验 | 现金净增加额 = 经营 + 投资 + 筹资现金流净额 |
| 跨表校验 | 现金流量表期末现金 ≈ 资产负债表货币资金 |

---

### 模块 B：Agent 智能问数核心

**TaskPlanner 类** (`src/agent/task_planner.py`)

| 功能 | 实现说明 |
|------|----------|
| 意图识别 | 基于关键词匹配：数据查询、对比分析、趋势分析、排名分析、归因分析 |
| 任务拆解 | 复杂问题拆解为可执行的子任务序列 |
| 澄清机制 | 检测缺失信息（年份、公司、指标）并主动提问 |
| 依赖管理 | 子任务间的执行顺序和依赖关系 |

**NL2SQL 转换器** (`src/agent/nl2sql.py`)

| 功能 | 实现说明 |
|------|----------|
| Schema 注入 | 预定义数据库表结构和字段说明 |
| Few-shot 示例 | 5 个典型查询示例供模型学习 |
| SQL 验证 | 语法检查、危险操作拦截 |
| 规则 fallback | 无 LLM 时使用规则匹配生成 SQL |

**VisualizationEngine 类** (`src/agent/visualization.py`)

| 图表类型 | 触发条件 |
|----------|----------|
| 折线图 | 趋势、变化、走势、同比增长 |
| 柱状图 | 排名、对比、比较、top |
| 饼图 | 占比、构成、比例、份额 |

**命名规范**: 图表按 `【问题编号_顺序编号】.jpg` 格式保存至 `result/` 文件夹

---

### 模块 C：RAG 增强与归因分析

**RAGRetriever 类** (`src/rag/retriever.py`)

| 功能 | 实现说明 |
|------|----------|
| 文档加载 | 支持 PDF 研报批量加载 |
| 文本分块 | 按段落分割，chunk_size=500 |
| 向量嵌入 | 支持 FlagEmbedding 或 fallback 词袋模型 |
| 相似度检索 | 余弦相似度 top-k 检索 |
| 归因输出 | references 字段包含来源路径、原文摘要 |

---

## 输出规范

### 任务二产出 (task2_output.xlsx)

按照附件 7 表 2 的 JSON 结构：

| 字段 | 说明 |
|------|----------|
| 问题编号 | B002_01, B002_02, ... |
| 问题 | 原始问题文本 |
| SQL | 生成的 MySQL 查询语句 |
| 图表路径 | ./result/B002_01_01.jpg |
| 时间戳 | ISO 8601 格式 |

### 任务三产出 (task3_output.xlsx)

按照附件 7 表 5 的格式（包含 references 嵌套）：

| 字段 | 说明 |
|------|----------|
| 问题编号 | B003_01, B003_02, ... |
| 问题 | 原始问题文本 |
| SQL | 生成的 MySQL 查询语句 |
| 图表路径 | ./result/B003_01_01.jpg |
| 答案 | RAG 生成的答案 |
| references | JSON 数组，包含 source、page、content、similarity |

---

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行测试

```bash
python test_finbrain.py
```

### 3. 运行完整流水线

```bash
python src/main.py \
  --data-dir "./B 题 - 示例数据/示例数据" \
  --output-dir "./result" \
  --api-key "sk-76f4b259f25147879777441ce24a0644" \
  --api-base "https://api.deepseek.com/v1"
```

### 4. 模块化调用

```python
from src.etl.financial_parser import FinancialParser
from src.agent.task_planner import TaskPlanner
from src.agent.visualization import VisualizationEngine

# 解析财报
parser = FinancialParser()
result = parser.parse_pdf("600080_20230428_FQ2V.pdf")

# 任务规划
planner = TaskPlanner()
plan = planner.decompose_question("贵州茅台 2024 年的净利润是多少？")

# 生成图表
viz = VisualizationEngine()
viz.set_question_id("B002")
chart_path = viz.create_chart(df, "净利润排名", question_id="B002_01")
```

---

## 测试报告

运行 `python test_finbrain.py` 的结果：

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

## API 配置

支持多家国产大模型：

| 提供商 | Base URL | 模型 |
|--------|----------|------|
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| 阿里云 | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-plus |
| 百度 | https://aip.baidubce.com/rpc/2.0/ai_custom/v1 | ernie-4.0 |
| 智谱 | https://open.bigmodel.cn/api/paas/v4 | glm-4 |
| Moonshot | https://api.moonshot.cn/v1 | moonshot-v1-8k |
| 零一万物 | https://api.lingyiwanwu.com/v1 | yi-large |

---

## Git 提交历史

| 提交哈希 | 说明 |
|----------|------|
| 2fb8c7c | feat: 实现 FinBrain 财报智能问数系统核心模块 |
| 1f9964d | docs: 更新重构计划文档 |
| 3d09009 | chore: 添加缺失的 `__init__.py` 文件 |
| 3c5cf23 | refactor: 分离文件处理和查询模块 |

---

## 后续优化方向

1. **PDF 解析增强**: 处理扫描版 PDF 的 OCR 识别
2. **NL2SQL 优化**: 使用微调模型提升 SQL 生成准确率
3. **RAG 增强**: 接入真实向量数据库（Chroma/Milvus）
4. **多轮对话**: 完善上下文管理和追问处理
5. **可视化美化**: 增加更多图表类型和样式定制

---

## 团队协作

- GitHub 仓库：https://github.com/shangjian2023/Horse-Hunter.git
- 分支策略：master 为主分支
- 提交规范：使用语义化提交信息

---

*最后更新：2026-03-23*
