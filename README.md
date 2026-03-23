# 上市公司财报"智能问数"助手

> 基于大模型的财报数据智能查询分析系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 项目简介

本项目是一个面向上市公司财报数据的智能问数助手，支持：

- **自然语言查询** - 用中文直接提问，自动解析并查询财报数据
- **多轮对话** - 支持上下文理解，可以连续追问
- **智能可视化** - 自动生成合适的图表（折线图、柱状图、饼图）
- **RAG 知识库增强** - 整合行业报告、企业信息等非结构化文档
- **多模态输入** - 支持上传财务图表截图进行分析

## 🚀 快速开始

### 方式一：Docker 一键启动（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/shangjian2023/Horse-Hunter.git
cd 泰迪杯

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API key

# 3. 启动服务
docker compose up -d

# 4. 访问应用
# Streamlit 前端：http://localhost:8501
```

### 方式二：本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API key

# 3. 运行测试
python test_finbrain.py

# 4. 运行完整流水线
python src/main.py --data-dir "./B 题 - 示例数据/示例数据" --output-dir "./result"
```

## 📁 项目结构

```
泰迪杯/
├── app.py                    # Streamlit 应用入口
├── test_finbrain.py          # 系统测试脚本
│
├── src/                      # 核心模块
│   ├── etl/                  # 财报 ETL 引擎
│   │   ├── financial_parser.py    # PDF 解析器
│   │   └── financial_validator.py # 财务勾稽关系校验
│   │
│   ├── agent/                # Agent 智能问数核心
│   │   ├── task_planner.py        # 任务规划器
│   │   ├── nl2sql.py              # NL2SQL 转换器
│   │   └── visualization.py       # 可视化引擎
│   │
│   ├── rag/                  # RAG 增强与归因分析
│   │   └── retriever.py           # 检索增强生成
│   │
│   ├── api/                  # API 接口层
│   │   └── llm_client.py          # 多模型 API 客户端
│   │
│   └── main.py               # 主入口程序
│
├── database/                 # 数据库模块
│   └── init.sql              # 初始化脚本
├── docker-compose.yml        # Docker 编排配置
├── Dockerfile                # Docker 镜像配置
└── requirements.txt          # Python 依赖
```

## 💡 功能演示

### 1. 财报解析

```
输入：600080_20230428_FQ2V.pdf
输出：
  - 核心业绩指标表
  - 资产负债表
  - 利润表
  - 现金流量表
  - 勾稽关系校验报告
```

### 2. 自然语言查询

```
用户：贵州茅台 2024 年的净利润是多少？
助手：生成 SQL 并执行：
  SELECT net_profit FROM core_performance_indicators
  WHERE company_name = '贵州茅台' AND report_date = '2024-12-31'
结果：743.21 亿元
```

### 3. 复杂问题拆解

```
用户：对比 Top 10 药企的净利润和研发投入

助手自动拆解为：
  1. 查询所有药企的净利润并排序
  2. 取前 10 名企业
  3. 查询这些企业的研发投入
  4. 生成对比柱状图
```

### 4. RAG 行业问答

```
用户：医药行业的政策环境如何？
助手：根据知识库中的行业报告：
  - 集采政策持续推进...
  - 创新药审批加速...
  [附参考来源：2025 年医药行业研究报告.pdf]
```

## 🔧 配置说明

### 环境变量 (.env)

```ini
# 数据库配置
MYSQL_ROOT_PASSWORD=root123
MYSQL_DATABASE=financial_report
MYSQL_USER=fin_user
MYSQL_PASSWORD=fin_pass123
MYSQL_PORT=3306

# 应用配置
APP_PORT=8501

# LLM API 配置（推荐使用 DeepSeek）
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 可选配置
DEBUG=true
TZ=Asia/Shanghai
```

### 支持的 LLM 模型

| 提供商 | 模型 | Base URL |
|--------|------|----------|
| DeepSeek | deepseek-chat | https://api.deepseek.com/v1 |
| 阿里云 | qwen-plus | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| 百度 | ernie-4.0 | https://aip.baidubce.com/rpc/2.0/ai_custom/v1 |
| 智谱 | glm-4 | https://open.bigmodel.cn/api/paas/v4 |
| Moonshot | moonshot-v1-8k | https://api.moonshot.cn/v1 |

## 📚 使用文档

| 文档 | 说明 |
|------|------|
| [RAG 使用指南.md](RAG 使用指南.md) | RAG 知识库配置和使用 |
| [团队协作指南.md](团队协作指南.md) | 团队协作流程和 Git 规范 |
| [README_DOCKER.md](README_DOCKER.md) | Docker 部署详细指南 |

## 🛠️ 开发指南

### 添加新模块

```bash
# 1. 在 models/ 下创建新模块
touch models/new_feature.py

# 2. 更新 models/__init__.py
echo "from .new_feature import NewFeature" >> models/__init__.py

# 3. 提交代码
git add .
git commit -m "feat: 添加新功能"
git push origin master
```

### 测试

```bash
# 运行测试脚本
python test_pipeline.py
```

## 📊 支持的数据表

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| core_performance_indicators | 核心业绩指标 | 每股收益、净资产收益率等 |
| balance_sheet | 资产负债表 | 总资产、总负债、所有者权益 |
| income_statement | 利润表 | 营收、成本、利润 |
| cash_flow_sheet | 现金流量表 | 经营、投资、筹资现金流 |

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支 `git checkout -b feature/your-feature`
3. 提交更改 `git commit -m "feat: 添加新功能"`
4. 推送到分支 `git push origin feature/your-feature`
5. 创建 Pull Request

## 📝 Git 提交规范

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 实现 RAG 知识库` |
| `fix` | 修复 Bug | `fix: 修复 SQL 生成错误` |
| `docs` | 文档更新 | `docs: 更新 README` |
| `refactor` | 重构 | `refactor: 优化代码结构` |
| `chore` | 构建/配置 | `chore: 更新依赖版本` |

## 🔗 相关资源

- [Streamlit 文档](https://docs.streamlit.io)
- [LangChain 文档](https://python.langchain.com)
- [Docker 文档](https://docs.docker.com)

## 📄 许可证

MIT License

## 👥 团队成员

- 项目负责人：@shangjian2023
- 核心开发：[欢迎加入](../../pulls)

---

<div align="center">

**问题反馈**: [Issues](../../issues) | **文档**: [Wiki](../../wiki)

⭐ 如果这个项目对你有帮助，请给一个 Star！

</div>
