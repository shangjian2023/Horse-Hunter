# 上市公司财报"智能问数"助手 - Docker 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖（OpenCV、PDF 处理所需）
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 基础工具
    build-essential \
    git \
    curl \
    # OpenCV 依赖
    libgl1-mesa-glx \
    libglib2.3-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    # PDF 处理依赖
    poppler-utils \
    default-jre \
    # 清理
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/result /app/logs

# 暴露端口（Streamlit 默认 8501）
EXPOSE 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 启动命令
CMD ["python", "app.py"]
