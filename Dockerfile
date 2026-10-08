# 使用官方 Python 3.11 的轻量版镜像
FROM python:3.11-slim

LABEL maintainer="Evil0ctal"

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 设置工作目录
WORKDIR /app

# 安装 ffmpeg（Bilibili音视频合并必需）及基础证书
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件并安装，利用 Docker 缓存层
COPY requirements.txt /app/
RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ -U pip \
    && pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ \
    && pip install --no-cache-dir -r requirements.txt

# 复制应用代码到容器
COPY . /app

# 确保启动脚本具有执行权限
RUN chmod +x start.sh

# 暴露端口 80
EXPOSE 80

# 设置容器启动命令
CMD ["./start.sh"]

