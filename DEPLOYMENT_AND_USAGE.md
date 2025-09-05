# Python 工具集服务部署与使用指南

本文档详细记录了在 Ubuntu 服务器上部署 Python 工具集服务（`py_tool_server`），并通过 Cloudflare Tunnel 进行域名访问的完整步骤，以及如何使用该服务提供的工具。

## 1. 概述

Python 工具集服务旨在为 AI 模型或其他客户端提供一个统一的 API 接口，以执行各种预定义的工具。目前，该服务集成了 Tavily Search API，用于实时信息检索。

*   **服务器类型**：旧电脑改造服务器
*   **操作系统**：Ubuntu 22.04.5 LTS
*   **服务域名**：`tools.10110531.xyz`
*   **服务端口**：`8827`
*   **部署位置**：`/home/ren/py_tool_server`

## 2. 部署步骤

以下步骤假设您已完成服务器的基础设置（如系统更新、Python/Node.js 环境安装、SSH 免密登录、`cloudflared` 的基本安装和认证，详见项目根目录下的 [`server_configuration.md`](server_configuration.md)）。

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
在 `nano` 编辑器中，添加您的 Tavily API 密钥。将 `YOUR_TAVILY_API_KEY` 替换为您的实际密钥。

```
TAVILY_API_KEY="YOUR_TAVILY_API_KEY"
```
**获取 Tavily API Key：** 请访问 [Tavily 官方网站](https://tavily.com/) 注册并获取。

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

修改 `config.yml` 文件，为新服务添加路由。

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

## 3. API 使用方法与效果

Python 工具集服务现在通过 `https://tools.10110531.xyz/api/v1/execute_tool` 提供一个统一的 `POST` 端点，用于执行不同的工具。

### 3.1 端点详情

*   **URL**: `https://tools.10110531.xyz/api/v1/execute_tool`
*   **Method**: `POST`
*   **Content-Type**: `application/json`
*   **请求体格式**:
    ```json
    {
      "tool_name": "要执行的工具名称 (string, required)",
      "parameters": {
        "工具所需参数 (object, required)"
      }
    }
    ```

### 3.2 可用工具示例：`tavily_search`

*   **描述**: 使用 Tavily API 执行网络搜索，获取实时信息。
*   **输入参数 (`parameters`)**:
    *   `query` (string, **必需**): 搜索查询。
    *   `search_depth` (string, 可选): 搜索深度，`"basic"` 或 `"advanced"` (默认 `"advanced"`)。
    *   `max_results` (integer, 可选): 返回最大结果数量 (默认 5)。

*   **成功响应 (`data` 字段内容)**:
    一个 JSON 对象，包含 `query` 和 `results` 等字段，其结构与 Tavily Search API 的官方响应一致。

### 3.3 API 测试命令及效果

您可以使用 `curl` 命令从任何有互联网连接的电脑上测试 API。

**测试命令 (在本地 Windows 终端执行)：**

```bash
curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" --header "Content-Type: application/json" --data "{\"tool_name\": \"tavily_search\",\"parameters\": {\"query\": \"What are the latest advancements in autonomous vehicles?\"}}"
```

**预期成功响应示例 (部分内容)：**

```json
{"success":true,"data":{"query":"What are the latest advancements in autonomous vehicles?","follow_up_questions":null,"answer":null,"images":[],"results":[{"url":"https://fifthlevelconsulting.com/top-10-autonomous-vehicle-trends-2025/","title":"Must-Read: Top 10 Autonomous Vehicle Trends (2025)","content":"..."},{"url":"https://autofleet.io/resource/state-of-autonomous-vehicles-2025s-av-push-toward-a-driverless-future","title":"State of Autonomous Vehicles: 2025's AV Push Toward a Driverless ...","content":"..."}, ...],"response_time":3.68,"request_id":"1e3e50c3-f42a-4f26-b90f-27b7ccddbe1e"}}
```

此响应表明服务已成功接收请求，调用 Tavily Search API，并返回了相关的搜索结果。