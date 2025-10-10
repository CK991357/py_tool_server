# Python 工具集服务部署与使用指南

本文档详细记录了在 Ubuntu 服务器上部署 Python 工具集服务（`py_tool_server`），并通过 Cloudflare Tunnel 进行域名访问的完整步骤，以及如何使用该服务提供的工具。

## 1. 概述

Python 工具集服务旨在为 AI 模型或其他客户端提供一个统一的 API 接口，以执行各种预定义的工具。该项目包含两个核心部分：
1.  **主服务**: 托管了 `tavily_search` 和 `firecrawl` 等需要访问外部网络的工具。
2.  **独立沙箱服务**: `python_sandbox` 在一个隔离的 Docker 环境中运行，用于安全地执行代码。

*   **服务器类型**：旧电脑改造服务器
*   **操作系统**：Ubuntu 22.04.5 LTS
*   **主服务域名**：`tools.10110531.xyz`
*   **沙箱服务域名**：`pythonsandbox.10110531.xyz`
*   **主服务端口**：`8827`
*   **部署位置**：`/home/ren/py_tool_server`

## 2. 部署步骤

以下步骤假设您已完成服务器的基础设置。详细的服务器配置过程请参考 **附录 A**。

### 2.1 获取项目代码

将 `py_tool_server` 文件夹上传到服务器的 `/home/ren/` 目录下。推荐使用 `git clone`。

**操作命令 (在服务器终端执行)：**

```bash
# 1. 登录到服务器 (如果尚未登录)
# ssh ren@192.168.3.100

# 2. 切换到用户主目录
cd /home/ren/

# 3. 克隆 GitHub 仓库
git clone https://github.com/CK991357/py_tool_server.git
```
克隆成功后，项目路径为 `/home/ren/py_tool_server`。

### 2.2 配置环境变量 (`.env` 文件)

`py_tool_server` 依赖环境变量来存储敏感信息（如 API 密钥）。

**操作命令 (在服务器终端执行)：**

```bash
# 1. 进入项目目录
cd /home/ren/py_tool_server

# 2. 创建并编辑 .env 文件 (使用 nano 编辑器)
nano .env
```
在 `nano` 编辑器中，添加您的 Tavily 和 Firecrawl API 密钥。将占位符替换为您的实际密钥。

```
TAVILY_API_KEY="YOUR_TAVILY_API_KEY"
FIRECRAWL_API_KEY="YOUR_FIRECRAWL_API_KEY"
```
**获取 API Keys：**
*   **Tavily API Key:** 请访问 [Tavily 官方网站](https://tavily.com/) 注册并获取。
*   **Firecrawl API Key:** 请访问 [Firecrawl 官方网站](https://firecrawl.dev/) 注册并获取。

保存并退出 `nano` (按 `Ctrl + O`，然后 `Enter`；按 `Ctrl + X` 退出)。

### 2.3 创建并激活 Python 虚拟环境

为了隔离项目依赖，服务运行在独立的 Python 虚拟环境中。

**操作命令 (在服务器终端执行)：**

```bash
# 1. 确保在项目目录 /home/ren/py_tool_server
cd /home/ren/py_tool_server

# 2. 创建虚拟环境
python3 -m venv venv

# 3. 激活虚拟环境
source venv/bin/activate
```
成功激活后，终端提示符前会显示 `(venv)`。

### 2.4 安装项目依赖

安装 `requirements.txt` 中列出的所有 Python 库，以及额外的 `gunicorn`。

**操作命令 (在服务器终端执行，确保虚拟环境已激活)：**

```bash
# 1. 安装 requirements.txt 中的依赖
pip install -r requirements.txt

# 2. 安装 Gunicorn (如果未在 requirements.txt 中)
pip install gunicorn
```
此步骤确保 [`FastAPI`](https://fastapi.tiangolo.com/)、[`uvicorn`](https://www.uvicorn.org/) 和 [`gunicorn`](https://gunicorn.org/) 等运行所需的所有库都已安装。

### 2.5 配置 Systemd 服务

使用 [`Gunicorn`](https://gunicorn.org/) 和 [`Uvicorn`](https://www.uvicorn.org/) Worker 来管理 [`FastAPI`](https://fastapi.tiangolo.com/) 应用，并作为系统服务持久化运行。

**操作命令 (在服务器终端执行)：**

```bash
# 1. 创建 Systemd 服务文件
sudo nano /etc/systemd/system/py_tools_server.service
```
在 `nano` 编辑器中，复制并粘贴以下内容：

```ini
[Unit]
Description=Gunicorn instance to serve Python Tool Server
After=network.target

[Service]
User=ren
Group=www-data
WorkingDirectory=/home/ren/py_tool_server
ExecStart=/home/ren/py_tool_server/venv/bin/gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8827 main:app
Restart=always

[Install]
WantedBy=multi-user.target
```
保存并退出 `nano` (按 `Ctrl + O`，然后 `Enter`；按 `Ctrl + X` 退出)。

**启动和启用服务 (在服务器终端执行)：**

```bash
# 重新加载 systemd 管理器配置
sudo systemctl daemon-reload

# 启动工具服务
sudo systemctl start py_tools_server.service

# 设置为开机自启
sudo systemctl enable py_tools_server.service
```
`Created symlink ...` 的输出表示服务已成功设置为开机自启。

### 2.6 更新 Cloudflare Tunnel 配置

修改 `config.yml` 文件，为新服务添加路由。关于如何管理多个域名，请参考 **附录 B**。

**操作命令 (在服务器终端执行)：**

```bash
# 1. 编辑 Cloudflare Tunnel 配置文件
sudo nano /home/ren/.cloudflared/config.yml
```
在 `nano` 编辑器中，找到 `ingress:` 部分，并按如下方式更新其内容：

```yaml
tunnel: 2c162088-d4fa-4dc4-8584-843717f77a28
credentials-file: /home/ren/.cloudflared/2c162088-d4fa-4dc4-8584-843717f77a28.json

ingress:
  # 新增的工具服务域名
  - hostname: tools.10110531.xyz
    service: http://localhost:8827
  
  # 原有的服务 (保留不变)
  - hostname: chart.10110531.xyz
    service: http://localhost:8826
    
  # 默认规则，必须放在最后
  - service: http_status:404
```
保存并退出 `nano` (按 `Ctrl + O`，然后 `Enter`；按 `Ctrl + X` 退出)。

### 2.7 重启 Cloudflare Tunnel 并添加 DNS 记录

**操作命令 (在服务器终端执行)：**

```bash
# 1. 重启 Cloudflare Tunnel 使配置生效
sudo systemctl restart cloudflared

# 2. 为新域名添加 DNS 记录
cloudflared tunnel route dns my-private-server tools.10110531.xyz
```
您会看到 `INF Added CNAME tools.10110531.xyz which will route to this tunnel ...` 的输出，表示 DNS 记录添加成功。

### 2.8 部署 `python_sandbox` 服务 (Docker)

`python_sandbox` 服务被设计为在 Docker 容器中运行，以实现最高级别的安全和隔离。

**操作命令 (在服务器终端执行)：**

```bash
# 1. 进入包含 docker-compose.yml 的 'tools' 目录
cd /home/ren/py_tool_server/tools

# 2. 构建 Docker 镜像 (如果镜像是本地构建)
# 这一步通常在 PYTHON_SANDBOX_GUIDE.md 中有详细说明
# 例如: docker-compose build --no-cache

# 3. 以后台模式启动服务
docker-compose up -d
```
启动后，`python_sandbox` 服务将在 Docker 容器中运行，并监听一个端口（例如 `8828`，具体取决于 `docker-compose.yml` 的配置）。您需要像配置主服务一样，为其添加 Cloudflare Tunnel 路由。

## 3. API 使用方法与效果

服务通过两个独立的端点提供：

### 3.1 主服务 API (`tavily_search`, `firecrawl`)

*   **URL**: `https://tools.10110531.xyz/api/v1/execute_tool`
*   **Method**: `POST`
*   **请求体格式**:
    ```json
    {
      "tool_name": "工具名 (e.g., 'tavily_search' or 'firecrawl')",
      "parameters": { "工具所需参数" }
    }
    ```

#### 3.1.1 `tavily_search` 测试

**测试命令 (Windows CMD):**
```bash
curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"tavily_search\",\"parameters\": {\"query\": \"Latest advancements in AI?\"}}"
```

#### 3.1.2 `firecrawl` 测试 (`scrape` 模式)

**测试命令 (Windows CMD):**
```bash
curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"firecrawl\", \"parameters\": {\"mode\": \"scrape\", \"parameters\": {\"url\": \"https://www.firecrawl.dev/\"}}}"
```

### 3.2 `python_sandbox` API

*   **URL**: `https://pythonsandbox.10110531.xyz/api/v1/python_sandbox`
*   **Method**: `POST`
*   **请求体格式**:
    ```json
    {
      "parameters": {
        "code": "要在沙箱中执行的 Python 代码"
      }
    }
    ```

#### 3.2.1 `python_sandbox` 测试

**1. 文本输出测试 (Windows CMD):**
```bash
curl -X POST "https://pythonsandbox.10110531.xyz/api/v1/python_sandbox" -H "Content-Type: application/json" -d "{\"parameters\": {\"code\": \"import platform; print(f'Hello from a {platform.processor()} container!')\"}}"
```
**预期成功响应示例:**
```json
{
    "stdout": "Hello from a x86_64 container!\\n",
    "stderr": "",
    "exit_code": 0
}
```

**2. 数据可视化测试 (Windows CMD):**
```bash
curl -X POST https://pythonsandbox.10110531.xyz/api/v1/python_sandbox ^
  -H "Content-Type: application/json" ^
  -d "{ \"parameters\": { \"code\": \"import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt,io,base64;plt.plot([0,1,2],[0,1,0]);buf=io.BytesIO();plt.savefig(buf,format='png',bbox_inches='tight');buf.seek(0);print(base64.b64encode(buf.read()).decode());buf.close();plt.close('all')\" } }"
```
**预期成功响应示例 (stdout 包含 Base64 图像):**
```json
{
    "stdout": "iVBORw0KGgoAAAA... (Base64 encoded PNG image data)",
    "stderr": "",
    "exit_code": 0
}
```
*(注: `stdout` 中 Base64 字符串的实际内容会非常长，这里仅为示意)*

此响应表明服务已成功接收请求，执行 Python 代码，并根据代码逻辑返回文本或 Base64 编码的图像数据。

---

## 附录 A：服务器完整配置记录

### 服务器基础信息
*   **服务器类型**：旧电脑改造服务器
*   **操作系统**：Ubuntu 22.04.5 LTS (GNU/Linux 5.15.0-153-generic x86_64)
*   **服务器 IP 地址**：`192.168.3.100` (静态内网 IP)
*   **服务器用户名**：`ren`

### 阶段一：服务器基础设置

#### 1. 系统更新与必要工具安装
*   **更新系统**：
    ```bash
    sudo apt update
    sudo apt upgrade -y
    sudo apt autoremove -y
    ```
*   **安装常用工具 (curl, unzip, git)**：
    ```bash
    sudo apt install -y curl unzip git
    ```

#### 2. Python 运行环境配置
*   **Python 版本**：Python 3.10.12
*   **pip 版本**：pip 22.0.2
*   **安装 pip 和 venv**：
    ```bash
    sudo apt install -y python3-pip python3-venv
    ```

#### 3. Node.js 运行环境配置
*   **Node.js 版本**：v20.19.4 (LTS)
*   **npm 版本**：10.8.2
*   **安装步骤**：
    ```bash
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
    ```

#### 4. 服务器防火墙 (UFW) 配置
*   **Docker 安装**: Docker version 27.5.1。已安装并正在运行，是 `python_sandbox` 服务的核心依赖。
*   **配置命令**：
    ```bash
    sudo ufw allow ssh
    sudo ufw enable
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    ```

#### 5. Cloudflare `cloudflared` 及 Tunnel 配置
*   **Tunnel 名称**：`my-private-server`
*   **Tunnel ID**：`2c162088-d4fa-4dc4-8584-843717f77a28`
*   **`cloudflared` 安装步骤**：
    ```bash
    curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-archive-keyring.gpg >/dev/null
    echo "deb [signed-by=/usr/share/keyrings/cloudflare-archive-keyring.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
    sudo apt update
    sudo apt install cloudflared
    ```
*   **`cloudflared` 认证**：
    ```bash
    cloudflared login
    ```
    (在浏览器中完成认证)
*   **创建 Tunnel**：
    ```bash
    cloudflared tunnel create my-private-server
    ```
*   **`config.yml` 文件内容**：
    路径：`/home/ren/.cloudflared/config.yml`
    内容：
    ```yaml
    tunnel: 2c162088-d4fa-4dc4-8584-843717f77a28
    credentials-file: /home/ren/.cloudflared/2c162088-d4fa-4dc4-8584-843717f77a28.json

    ingress:
      # 新增的工具服务域名
      - hostname: tools.10110531.xyz
        service: http://localhost:8827
      
      # 新增的沙箱服务域名
      - hostname: pythonsandbox.10110531.xyz
        service: http://localhost:8828 # 假设沙箱服务运行在 8828 端口
      
      # 原有的服务
      - hostname: chart.10110531.xyz
        service: http://localhost:8826
        
      # 默认规则，必须放在最后
      - service: http_status:404
    ```
*   **`cloudflared` Systemd 服务文件 (`cloudflared.service`) 内容**：
    路径：`/etc/systemd/system/cloudflared.service`
    内容：
    ```ini
    [Unit]
    Description=Cloudflare Tunnel
    After=network.target

    [Service]
    TimeoutStartSec=0
    Type=notify
    ExecStart=/usr/local/bin/cloudflared tunnel run my-private-server
    Restart=on-failure
    RestartSec=5
    User=ren # 确保是您的服务器用户名

    [Install]
    WantedBy=multi-user.target
    ```
*   **DNS 路由配置命令**：
    ```bash
    cloudflared tunnel route dns my-private-server tools.10110531.xyz
    cloudflared tunnel route dns my-private-server pythonsandbox.10110531.xyz
    cloudflared tunnel route dns my-private-server chart.10110531.xyz
    ```

### 阶段二：新电脑开发环境设置

#### 1. VS Code 及 Remote - SSH 扩展安装
*   下载并安装 [Visual Studio Code](https://code.visualstudio.com/download)。
*   在 VS Code 中安装 `Remote - SSH` 扩展 (由 Microsoft 发布)。

#### 2. 新电脑到服务器的 SSH 免密登录配置
*   **生成 SSH 密钥对 (在新电脑)**：
    ```bash
    ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
    ```
*   **复制公钥到服务器 (在新电脑)**：
    ```bash
    ssh-copy-id ren@192.168.3.100
    ```

### 阶段三：Python 工具集服务部署

这是为 AI 模型提供可调用工具的后端服务。

#### 1. 项目代码结构

项目位于服务器的 `/home/ren/py_tool_server` 目录下。
```
/home/ren/py_tool_server/
├── .env
├── main.py
├── requirements.txt
└── tools/
   ├── __init__.py
   ├── tavily_search.py
   ├── firecrawl_tool.py
   ├── code_interpreter.py
   ├── tool_registry.py
   ├── Dockerfile
   └── docker-compose.yml
```

#### 2. Systemd 服务配置 (`py_tools_server.service`)

*   **服务文件路径**：`/etc/systemd/system/py_tools_server.service`
*   **文件内容**：
   ```ini
   [Unit]
   Description=Gunicorn instance to serve Python Tool Server
   After=network.target

   [Service]
   User=ren
   Group=www-data
   WorkingDirectory=/home/ren/py_tool_server
   ExecStart=/home/ren/py_tool_server/venv/bin/gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8827 main:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

---

## 附录 B：Cloudflare Tunnel 多域名管理

本指南将详细说明如何在同一个 Cloudflare Tunnel 中配置多个自定义域名。

### 概述

Cloudflare Tunnel 允许您通过单个 `cloudflared` 客户端将流量安全地路由到您本地服务器上运行的多个内部服务。您可以通过在 `config.yml` 文件中配置不同的 `hostname` 和 `service` 规则，来实现通过不同的自定义域名访问不同的本地服务。

### 步骤 1：编辑 `config.yml` 文件

在服务器终端中执行以下命令，打开配置文件：
```bash
nano /home/ren/.cloudflared/config.yml
```

### 步骤 2：添加入口规则 (Ingress Rules)

在 `ingress:` 列表下，为您的每个服务添加一个条目。每个条目包含 `hostname` 和 `service`。

**示例配置:**
```yaml
tunnel: 2c162088-d4fa-4dc4-8584-843717f77a28
credentials-file: /home/ren/.cloudflared/2c162088-d4fa-4dc4-8584-843717f77a28.json

ingress:
  # 规则 1: 指向 Python 工具集主服务
  - hostname: tools.10110531.xyz
    service: http://localhost:8827

  # 规则 2: 指向 Python 代码沙箱服务
  - hostname: pythonsandbox.10110531.xyz
    service: http://localhost:8828 # 假设沙箱服务运行在 8828 端口

  # 规则 3: 指向原有的图表服务
  - hostname: chart.10110531.xyz
    service: http://localhost:8826

  # 默认规则: 捕获所有不匹配的请求，必须放在最后！
  - service: http_status:404
```
保存并退出 `nano` 编辑器。

### 步骤 3：重启 `cloudflared` 服务

修改配置后，必须重启 `cloudflared` 服务才能使新的配置生效。
```bash
sudo systemctl restart cloudflared
```

### 步骤 4：更新 Cloudflare DNS 记录

此步骤将您的新域名与 Cloudflare Tunnel 关联起来。为 `config.yml` 中配置的每一个 `hostname` 都执行一次 `route dns` 命令。

```bash
# 为工具服务添加路由
cloudflared tunnel route dns my-private-server tools.10110531.xyz

# 为沙箱服务添加路由
cloudflared tunnel route dns my-private-server pythonsandbox.10110531.xyz

# 为图表服务添加路由 (如果尚未添加)
cloudflared tunnel route dns my-private-server chart.10110531.xyz
```
（请将 `my-private-server` 替换为您的实际 Tunnel 名称）

每条命令都会在 Cloudflare DNS 中自动创建一个 `CNAME` 记录，将对应的子域名指向您的 Tunnel。