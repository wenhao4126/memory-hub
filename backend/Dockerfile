# ============================================================
# 多智能体记忆中枢 - API 服务镜像
# ============================================================
# 功能：构建 FastAPI 后端服务 Docker 镜像
# 作者：小码
# 日期：2026-03-06
# ============================================================

# 基础镜像 - Python 3.11 slim 版本（更小更快）
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
# 防止 Python 生成 .pyc 文件
ENV PYTHONDONTWRITEBYTECODE=1
# 防止 Python 缓冲 stdout/stderr
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
# - gcc: 编译 Python 扩展
# - libpq-dev: PostgreSQL 客户端库
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
# --no-cache-dir: 不缓存下载的包，减小镜像体积
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/

# 暴露端口
EXPOSE 8000

# 健康检查
# 每 30 秒检查一次，超时 10 秒，失败 3 次标记为不健康
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health')" || exit 1

# 启动命令
# 使用 uvicorn 运行 FastAPI 应用
# --host 0.0.0.0: 监听所有网络接口
# --port 8000: 监听端口
# --workers 2: 启动 2 个工作进程（生产环境）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]