# 使用官方的 Python 3.11 slim 镜像 (基于Debian)
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 替换Debian软件源为国内镜像，加速下载
# RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
#     sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

# 安装系统依赖和轻量级字体
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    # 轻量级中文字体（金融图表常用）
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    # 基础英文字体
    fonts-dejavu-core \
    fonts-liberation \
    fontconfig && \
    fc-cache -fv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 设置matplotlib使用Agg后端（无GUI，适合服务器）
ENV MPLBACKEND=Agg

# 安装 Python 依赖（使用国内镜像加速并锁定版本）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    fastapi \
    uvicorn \
    docker \
    numpy==1.26.4 \
    scipy==1.14.1 \
    pandas==2.2.2 \
    openpyxl==3.1.2 \
    sympy==1.12 \
    matplotlib==3.8.4 \
    seaborn==0.13.2 \
    python-docx==1.1.2 \
    reportlab==4.0.7 \
    python-pptx==0.6.23

# 复制您的 code_interpreter.py 文件到容器的 /app 目录
COPY code_interpreter.py .

# 暴露应用程序监听的端口
EXPOSE 8828

# 定义容器启动时执行的命令
CMD ["uvicorn", "code_interpreter:app", "--host", "0.0.0.0", "--port", "8828", "--log-level", "info"]
