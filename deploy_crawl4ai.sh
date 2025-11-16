#!/bin/bash
echo "🚀 开始部署 Crawl4AI 工具..."

# 1. 安装系统依赖
echo "📦 安装系统依赖..."
sudo apt update
sudo apt install -y python3-pip libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxcb1 libxdamage1 libxext6 libxfixes3 \
    libxrandr2 libxcomposite1 libx11-xcb1 libxkbcommon0 libxss1 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 libwayland-client0 \
    libwayland-server0 wget curl unzip

# 2. 安装字体
echo "🔤 安装字体..."
sudo apt install -y fonts-liberation fonts-noto-cjk fonts-noto-color-emoji \
    fonts-freefont-ttf ttf-ubuntu-font-family

# 3. 安装 Python 依赖
echo "📚 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements_crawl4ai.txt

# 4. 安装 Playwright 浏览器
echo "🌐 安装 Playwright Chromium..."
python -m playwright install chromium
python -m playwright install-deps chromium

echo "✅ 部署完成！"
echo "💡 启动命令: source venv/bin/activate && python your_main_script.py"