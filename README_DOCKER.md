# 上市公司财报"智能问数"助手 - Docker 协作指南

## 快速开始

### 1. 环境准备

确保所有成员安装以下软件：
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)（Windows/Mac）
- Git

### 2. 克隆项目

```bash
git clone <项目仓库地址>
cd 泰迪杯
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入实际的 API key 等配置
```

### 4. 启动服务

```bash
# 一键启动所有服务（MySQL + 应用）
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

### 5. 访问应用

- **Streamlit 前端**: http://localhost:8501
- **MySQL 数据库**: localhost:3306

---

## 常用命令

### 开发模式

```bash
# 启动服务（代码变更自动重载）
docker compose up -d

# 重新构建镜像
docker compose build

# 重启单个服务
docker compose restart app
```

### 数据库操作

```bash
# 进入 MySQL 容器
docker exec -it financial_report_mysql mysql -u fin_user -pfin_pass123 financial_report

# 从宿主机执行 SQL
docker exec financial_report_mysql mysql -u fin_user -pfin_pass123 financial_report -e "SELECT * FROM core_performance_indicators LIMIT 10;"
```

### 日志查看

```bash
# 查看所有服务日志
docker compose logs -f

# 查看单个服务日志
docker compose logs -f app
docker compose logs -f mysql
```

### 清理数据

```bash
# 停止服务并删除数据卷（⚠️ 谨慎使用）
docker compose down -v
```

---

## 团队协作流程

### Git 分支策略

```
main          - 主分支（稳定版本）
develop       - 开发分支
feature/xxx   - 功能分支（从 develop 检出）
```

### 开发流程

```bash
# 1. 拉取最新代码
git pull origin develop

# 2. 创建功能分支
git checkout -b feature/text-to-sql

# 3. 开发并提交
git add .
git commit -m "feat: 实现 Text-to-SQL 核心功能"

# 4. 推送分支
git push origin feature/text-to-sql

# 5. 创建 Pull Request
```

### 提交规范

```
feat:     新功能
fix:      修复 bug
docs:     文档更新
style:    代码格式（不影响功能）
refactor: 重构
test:     测试
chore:    构建/工具配置
```

---

## 项目结构

```
泰迪杯/
├── .env                  # 环境变量（不提交）
├── .env.example          # 环境变量模板
├── .gitignore            # Git 忽略规则
├── Dockerfile            # Docker 镜像配置
├── docker-compose.yml    # Docker 编排配置
├── requirements.txt      # Python 依赖
├── main.py               # 主程序入口
├── app.py                # Streamlit 前端
├── database/
│   └── init.sql          # 数据库初始化脚本
├── config/               # 配置文件
├── models/               # 模型定义
├── parsers/              # PDF 解析器
├── utils/                # 工具函数
├── data/                 # 数据目录（不提交）
├── result/               # 输出结果（不提交）
└── logs/                 # 日志目录（不提交）
```

---

## 故障排查

### 常见问题

**1. 端口冲突**
```bash
# 修改 .env 中的端口配置
APP_PORT=8503
MYSQL_PORT=3307
```

**2. 镜像构建失败**
```bash
# 清理缓存重新构建
docker compose build --no-cache
```

**3. 数据库连接失败**
```bash
# 检查 MySQL 是否启动
docker compose ps

# 查看 MySQL 日志
docker compose logs mysql
```

**4. 代码变更不生效**
```bash
# 重启应用容器
docker compose restart app
```

---

## 负责人联系方式

| 模块 | 负责人 | 联系方式 |
|------|--------|----------|
| 数据解析 | TBD | - |
| Text-to-SQL | TBD | - |
| RAG 知识库 | TBD | - |
| 前端可视化 | TBD | - |
