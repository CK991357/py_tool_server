# Python 工具集服务使用指南

## 1. 概述

本文档详细说明了部署在私有服务器上的 Python 工具集服务。该服务旨在为 AI 模型或任何其他客户端提供一个统一、可扩展的 API 接口，以执行各种预定义的工具。

该服务的核心特点是其可扩展性。所有工具都通过一个统一的端点进行调用，并通过 `tool_name` 参数进行区分。未来可以轻松地在后端添加新工具，而无需更改 API 的调用方式。

## 2. 服务器与环境

- **服务器详情**: 详细的硬件和基础软件配置请参考项目根目录下的 `server_configuration.md` 文件。
- **运行环境**:
    - **语言**: Python 3.10+
    - **框架**: FastAPI
    - **核心依赖**: `fastapi`, `uvicorn`, `tavily-python`, `python-dotenv` (完整列表请参见 `requirements.txt`)
    - **部署方式**:
        - `tavily_search`: 通过 Gunicorn 和 Systemd 作为后台服务在主机上持久化运行。
        - `python_sandbox`: 作为一个独立的、容器化的服务通过 **Docker Compose** 运行。
    
    ## 3. 部署与运行
    
    ### 3.1 `tavily_search` (主机部署)
    
    1.  **代码获取**: 将 `py_tool_server` 文件夹上传到服务器（例如 `/home/ren/py_tool_server`）。
    2.  **进入目录**: `cd /home/ren/py_tool_server`
    3.  **创建并激活虚拟环境**:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    4.  **安装依赖**: `pip install -r requirements.txt`
    5.  **生产环境部署**: 详细的 Systemd 和 Cloudflare Tunnel 配置请参考 `server_configuration.md` 中的“阶段四”。
    
    ### 3.2 `python_sandbox` (Docker 部署)
    
    `python_sandbox` 服务被设计为在 Docker 容器中运行，以实现最高级别的安全和隔离。
    
    1.  **代码获取**: 将包含 `code_interpreter.py`, `Dockerfile`, 和 `docker-compose.yml` 的 `tools` 文件夹上传到服务器。
    2.  **进入目录**: `cd /path/to/your/tools`
    3.  **构建并启动服务**:
        ```bash
        docker-compose up --build -d
        ```
        - `--build`: 强制重新构建 Docker 镜像，以确保应用最新的代码和依赖变更。
        - `-d`: 在后台（detached mode）运行服务。
    4.  **确认运行状态**:
        ```bash
        docker-compose ps
        ```
    5.  **查看日志**:
        ```bash
        docker-compose logs -f
        ```
    
    **重要前提**:
    - 主机上必须已安装 Docker 和 Docker Compose。
    - 运行 Docker 的用户必须有权限访问 Docker守护进程。`docker-compose.yml` 中已通过挂载 Docker socket (`/var/run/docker.sock`) 来实现此功能。

## 4. API 使用方式

### 4.1 端点

- **URL**: `https://tools.10110531.xyz/api/v1/execute_tool`
- **Method**: `POST`
- **Content-Type**: `application/json`

### 4.2 请求体格式

请求体必须是一个包含以下两个字段的 JSON 对象：

- `tool_name` (string, required): 要执行的工具的名称。
- `parameters` (object, required): 一个包含该工具所需所有参数的字典。

**示例请求体:**
```json
{
  "tool_name": "tavily_search",
  "parameters": {
    "query": "What are the latest advancements in AI?",
    "search_depth": "advanced",
    "max_results": 3
  }
}
```

### 4.3 成功响应

- **HTTP Status Code**: `200 OK`
- **Body**: 一个包含以下字段的 JSON 对象：
    - `success` (boolean): 恒为 `true`。
    - `data` (object): 工具执行成功后返回的具体数据。该对象的结构由执行的工具决定。

**示例成功响应 (来自 tavily_search):**
```json
{
    "success": true,
    "data": {
        "query": "...",
        "results": [
            {
                "title": "...",
                "url": "...",
                "content": "...",
                "score": 0.98
            }
        ]
    }
}
```

### 4.4 失败响应

- **HTTP Status Code**:
    - `404 Not Found`: 如果请求的 `tool_name` 不存在。
    - `400 Bad Request`: 如果为工具提供的 `parameters` 未通过验证（例如，缺少必需参数或类型错误）。
    - `500 Internal Server Error`: 如果工具在执行过程中发生意外错误。
- **Body**: 响应体将包含一个描述错误详情的 JSON 对象。

**示例 404 响应:**
```json
{
    "detail": "Tool 'non_existent_tool' not found. Available tools are: ['tavily_search']"
}
```

**示例 400 响应:**
```json
{
    "detail": {
        "success": false,
        "error": "Input validation failed",
        "details": [
            {
                "loc": ["query"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
}
```

## 5. 可用工具列表

---

### 5.1 `tavily_search`

- **描述**: 使用 Tavily API 执行网络搜索，以查找实时信息、回答问题或研究主题。返回包含摘要和链接的搜索结果列表。

- **输入参数 (`parameters`)**:

| 参数名         | 类型   | 是否必需 | 默认值     | 描述                                                                 |
|----------------|--------|----------|------------|----------------------------------------------------------------------|
| `query`        | string | **是**   | N/A        | 要执行的搜索查询。                                                   |
| `search_depth` | string | 否       | "advanced" | 搜索深度。`"basic"` 更快，`"advanced"` 更全面。                      |
| `max_results`  | integer| 否       | 5          | 要返回的最大搜索结果数量。                                           |


- **输出 (`data` 字段内容)**:
  成功时，`data` 字段是一个 JSON 对象，其结构与 [Tavily Search API 的官方响应](https://docs.tavily.com/docs/python-sdk/api-reference#search-api) 一致，主要包含 `query` 和 `results` 等字段。

- **使用示例 (`curl`)**:
  ```bash
  curl -X POST 'https://tools.10110531.xyz/api/v1/execute_tool' \
  --header 'Content-Type: application/json' \
  --data '{
      "tool_name": "tavily_search",
      "parameters": {
          "query": "Who is the founder of OpenAI?"
      }
  }'

---

### 5.2 `python_sandbox`

- **描述**: 在一个高度安全、多层隔离的 Docker 沙箱环境中执行 Python 代码片段。此工具是为最大化安全而设计的，能够防御不安全的模型生成代码。

- **API 端点**: `POST /api/v1/python_sandbox`
  *(注意: 这是一个独立的专用端点，与通用的 `/execute_tool` 不同)*

- **输入参数 (`parameters`)**:

| 参数名 | 类型   | 是否必需 | 默认值 | 描述                     |
|----------|--------|----------|--------|--------------------------|
| `code`   | string | **是**   | N/A    | 要在沙箱中执行的 Python 代码。 |


- **输出**:
  成功执行时（HTTP 200），响应体是一个包含以下三个键的 JSON 对象：
    - `stdout` (string): 代码执行后的标准输出内容。
    - `stderr` (string): 代码执行期间产生的标准错误内容。
    - `exit_code` (integer): 容器内代码的退出码。`0` 表示成功，非 `0` 表示代码本身存在错误。

- **安全特性**:
    - **Docker 容器隔离**: 每次执行都在一个全新的、一次性的 Docker 容器 (`python:3.11-slim`) 中进行。
    - **无网络访问**: 容器的 `network_disabled=True`，彻底杜绝任何网络请求。
    - **只读文件系统**: 容器的文件系统是只读的 (`read_only=True`)，防止任何文件写入尝试。
    - **资源限制**: 内存上限为 **256MB**，CPU 使用率上限为 **0.5 核**，防止资源滥用。
    - **Python 内置函数限制**: 在执行代码前，通过自定义的 `runner_script` 移除了所有危险的 Python 内置函数（如 `open`, `import`, `eval` 等），只保留一个安全的子集。

- **使用示例 (`curl`)**:
  ```bash
  curl -X POST 'https://pythonsandbox.10110531.xyz/api/v1/python_sandbox' \
  --header 'Content-Type: application/json' \
  --data '{
      "parameters": {
          "code": "import sys; print(\"Hello from sandbox\"); print(\"Error log\", file=sys.stderr)"
      }
  }'
  ```
  *(注意: 请求体中不包含 `tool_name`)*

- **示例成功响应**:
  ```json
  {
      "stdout": "Hello from sandbox\n",
      "stderr": "Error log\n",
      "exit_code": 0
  }
  ```