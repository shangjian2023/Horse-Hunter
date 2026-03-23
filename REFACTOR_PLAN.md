# 项目重构计划 - 上市公司财报智能问数助手

## 一、需求分析

### 核心要求
1. **通用性**: 能处理不同来源、格式的财报数据 (PDF/Excel/Word)
2. **准确性**: 数据提取和 SQL 生成要准确可靠
3. **现场演示**: 比赛时现场给数据，快速完成分析任务

### 功能模块划分

#### 模块一：文件处理系统 (数据处理端)
- 支持 PDF/Excel/Word 多种格式
- 自动识别财报类型 (资产负债表/利润表/现金流量表)
- 数据清洗和验证
- 批量处理能力
- 输出标准化数据格式

#### 模块二：智能查询系统 (分析端)
- 自然语言查询 (Text-to-SQL)
- 多轮对话支持
- 可视化生成
- RAG 知识库增强
- 多模型支持 (国产大模型)

---

## 二、项目结构重构

```
financial-report-assistant/
├── README.md                      # 项目说明
├── requirements.txt               # Python 依赖
├── docker-compose.yml            # Docker 编排
├── Dockerfile                    # 容器镜像
│
├── config/                       # 配置模块
│   ├── __init__.py
│   └── settings.py               # 系统配置
│
├── data/                         # 数据目录
│   ├── input/                    # 输入数据目录
│   ├── processed/                # 处理后数据
│   └── knowledge_base/           # RAG 知识库
│
├── database/                     # 数据库模块
│   ├── __init__.py
│   ├── db_manager.py             # 数据库管理
│   ├── init.sql                  # 初始化脚本
│   └── models.py                 # 数据模型
│
├── parsers/                      # 解析器模块 (文件处理)
│   ├── __init__.py
│   ├── pdf_parser.py             # PDF 解析器
│   ├── excel_parser.py           # Excel 解析器
│   ├── word_parser.py            # Word 解析器
│   └── base_parser.py            # 解析器基类
│
├── processors/                   # 数据处理模块 (新增)
│   ├── __init__.py
│   ├── data_cleaner.py           # 数据清洗
│   ├── data_validator.py         # 数据验证
│   └── data_transformer.py       # 数据转换
│
├── models/                       # AI 模型模块 (查询分析)
│   ├── __init__.py
│   ├── chat_agent.py             # 智能问数助手
│   ├── text_to_sql.py            # Text-to-SQL 转换
│   ├── conversation_manager.py   # 对话管理
│   ├── visualization.py          # 可视化引擎
│   └── rag/                      # RAG 知识库
│       ├── __init__.py
│       ├── document_loader.py
│       ├── knowledge_base.py
│       └── retriever.py
│
├── apps/                         # 应用模块 (前端)
│   ├── __init__.py
│   ├── file_processor_app.py     # 文件处理应用 (新增)
│   ├── chat_app.py               # 智能问数应用
│   └── admin_app.py              # 管理后台 (新增)
│
├── utils/                        # 工具函数
│   ├── __init__.py
│   ├── logger.py                 # 日志工具
│   └── helpers.py                # 辅助函数
│
├── cli/                          # 命令行工具 (新增)
│   ├── __init__.py
│   ├── process.py                # 数据处理命令
│   └── query.py                  # 查询命令
│
└── tests/                        # 测试目录
    ├── __init__.py
    ├── test_parsers.py
    ├── test_processors.py
    └── test_models.py
```

---

## 三、核心功能设计

### 1. 文件处理流程 (通用性保证)

```
输入文件 → 格式识别 → 解析 → 数据清洗 → 验证 → 标准化输出 → 入库
   ↓           ↓          ↓          ↓          ↓          ↓          ↓
 PDF/Excel  判断类型   提取表格   去重/补全  格式校验   JSON/CSV   MySQL
```

### 2. 智能查询流程 (准确性保证)

```
用户问题 → 意图识别 → SQL 生成 → 执行查询 → 结果验证 → 可视化 → 自然语言回答
   ↓           ↓          ↓          ↓          ↓          ↓            ↓
 NLP 处理   判断类型    LLM 生成   DB 查询    数据校验   图表生成     文本输出
```

### 3. 多模型支持

```python
# 支持的模型提供商
PROVIDERS = {
    'deepseek': {'url': 'https://api.deepseek.com/v1', 'models': ['deepseek-chat']},
    'moonshot': {'url': 'https://api.moonshot.cn/v1', 'models': ['moonshot-v1-8k']},
    'zhipu': {'url': 'https://open.bigmodel.cn/api/paas/v4', 'models': ['glm-4']},
    'aliyun': {'url': 'https://dashscope.aliyuncs.com/compatible-mode/v1', 'models': ['qwen-plus']},
    'baidu': {'url': 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1', 'models': ['ernie-4.0']},
}
```

---

## 四、实施步骤

### 第一阶段：项目结构重构
1. 创建新的目录结构
2. 移动现有文件到新位置
3. 更新导入路径

### 第二阶段：文件处理模块增强
1. 创建解析器基类
2. 实现 PDF/Excel/Word 解析器
3. 添加数据验证和清洗
4. 实现批量处理

### 第三阶段：查询模块优化
1. 优化 Text-to-SQL 提示词
2. 添加 SQL 验证机制
3. 实现查询结果校验
4. 增强多轮对话能力

### 第四阶段：现场演示优化
1. 一键导入数据功能
2. 快速配置向导
3. 演示模式 (预设问题)
4. 结果导出功能

---

## 五、准确性保证措施

### 数据提取准确性
- 多引擎解析 (pdfplumber + PyMuPDF)
- 表格结构自动识别
- 数据交叉验证

### SQL 生成准确性
- Schema 信息注入
- Few-shot 示例
- SQL 语法验证
- 执行前预览

### 结果准确性
- 数据范围检查
- 逻辑一致性验证
- 异常值检测

---

## 六、现场演示准备

### 快速部署
- Docker 一键启动
- 预置演示数据
- 离线模型支持 (可选)

### 演示脚本
1. 数据导入演示 (30 秒)
2. 自然语言查询演示 (1 分钟)
3. 多轮对话演示 (1 分钟)
4. 可视化展示 (30 秒)

### 应急预案
- 离线数据包
- 备用 API Key
- 本地模型备选
