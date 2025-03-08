FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AWS_REGION=us-east-1

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建必要的目录
RUN mkdir -p /app/glossary_files

# 复制项目文件
COPY requirements.txt .
COPY src/ ./src/
COPY gradio_app.py .
COPY .env.example .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建非root用户
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# 数据卷
VOLUME ["/app/glossary_files"]

# 暴露端口
EXPOSE 7860

# 启动命令
CMD ["python", "gradio_app.py"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1
