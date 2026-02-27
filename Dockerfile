FROM python:3.12-slim

LABEL maintainer="DragonAI Team"
LABEL description="DragonAI Backend Service"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 核心优化：替换为阿里云 Debian 源，大幅提升 apt 下载速度
# 适配 Debian 12 (Bookworm) 的 sources.list.d 格式
RUN sed -i 's|http://deb.debian.org|https://mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 可选优化：替换 pip 源为阿里云，加速 Python 包安装
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p storage chroma_db logs

RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--factory"]