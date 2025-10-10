# 使用官方的 Python 3.11 slim 镜像 (基于Debian)
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# (可选) 如果需要，可以替换Debian的软件源为国内镜像，例如清华源
# RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
#     sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

# 安装系统依赖 (使用Debian的包管理)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    lsb-release && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（使用国内镜像加速并锁定版本）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    fastapi \
    uvicorn \
    docker \
    numpy==1.26.4 \
    pandas==2.2.2 \
    openpyxl==3.1.2 \
    sympy==1.12 \
    matplotlib==3.8.4 \
    seaborn==0.13.2

# 复制您的 code_interpreter.py 文件到容器的 /app 目录
COPY code_interpreter.py .

# 暴露应用程序监听的端口
EXPOSE 8828

# 定义容器启动时执行的命令
CMD ["uvicorn", "code_interpreter:app", "--host", "0.0.0.0", "--port", "8828", "--log-level", "info"]
