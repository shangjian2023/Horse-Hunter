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
cd Horse-Hunter

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

# 3. 初始化数据库
python main.py --init-db

# 4. 启动应用
streamlit run chat_app.py
```

## 📁 项目结构

```
Horse-Hunter/
├── app.py                    # 财报数据处理应用
├── chat_app.py               # 智能问数助手（基础版）
├── rag_chat_app.py           # 智能问数助手（RAG 增强版）
├── main.py                   # 命令行批处理入口
├── rag_init.py               # RAG 知识库初始化工具
│
├── models/                   # AI 模型模块
│   ├── chat_agent.py         # 智能问数主模块
│   ├── text_to_sql.py        # Text-to-SQL 转换器
│   ├── conversation_manager.py  # 对话管理器
│   ├── visualization.py      # 可视化引擎
│   ├── multimodal.py         # 多模态处理器
│   └── rag/                  # RAG 知识库
│       ├── document_loader.py
│       ├── knowledge_base.py
│       └── retriever.py
│
├── database/                 # 数据库模块
├── parsers/                  # PDF 解析模块
├── utils/                    # 工具函数
└── config/                   # 配置模块
```

## 💡 功能演示

### 1. 自然语言查询

```
用户：贵州茅台 2024 年的净利润是多少？
助手：查询结果：
  - 营业总收入：1505.68 亿元
  - 净利润：743.21 亿元
  - 同比增长：15.3%
```

### 2. 多轮对话

```
用户：查询贵州茅台的净利润
助手：贵州茅台 2024 年净利润为 743.21 亿元

用户：那营业收入呢？
助手：贵州茅台 2024 年营业收入为 1505.68 亿元

用户：对比一下五粮液
助手：[展示对比数据]
```

### 3. 行业知识问答（RAG）

```
用户：医药行业的政策环境如何？
助手：根据知识库中的行业报告，医药行业政策环境如下：
  - 集采政策持续推进...
  - 创新药审批加速...
  [附参考来源]
```

## 🔧 配置说明

### 环境变量 (.env)

```ini
# LLM API 配置
ANTHROPIC_BASE_URL=https://your-api-endpoint.com
ANTHROPIC_AUTH_TOKEN=your-api-key
ANTHROPIC_MODEL=qwen-plus

# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=financial_report
MYSQL_USER=root
MYSQL_PASSWORD=your_password
```

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
