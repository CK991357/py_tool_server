# Python 工具集服务使用指南

## 1. 概述

本文档详细说明了部署在私有服务器上的 Python 工具集服务。该服务旨在为 AI 模型或任何其他客户端提供一个统一、可扩展的 API 接口，以执行各种预定义的工具。

该服务的核心特点是其可扩展性。所有由主服务托管的工具都通过一个统一的端点进行调用，并通过 `tool_name` 参数进行区分。未来可以轻松地在后端添加新工具，而无需更改 API 的调用方式。

## 2. 服务器与环境

- **服务器详情**: 详细的硬件和基础软件配置请参考项目根目录下的 `server_configuration.md` 文件。
- **运行环境**:
    - **语言**: Python 3.10+
    - **框架**: FastAPI
    - **核心依赖**: `fastapi`, `uvicorn`, `tavily-python`, `python-dotenv`, `docker`, `firecrawl-py` (完整列表请参见 `requirements.txt`)
- **部署方式**:
    - **主服务 (`tavily_search`, `firecrawl`)**: 通过 Gunicorn 和 Systemd 作为后台服务在主机上持久化运行。
    - **独立服务 (`python_sandbox`)**: 作为一个独立的、容器化的服务通过 **Docker Compose** 运行。

## 3. 部署与运行

### 3.1 主服务 (主机部署)

1.  **代码获取**: 将 `py_tool_server` 文件夹上传到服务器（例如 `/home/ren/py_tool_server`）。
2.  **进入目录**: `cd /home/ren/py_tool_server`
3.  **创建并激活虚拟环境**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
4.  **安装依赖**: `pip install -r requirements.txt`
5.  **生产环境部署**: 详细的 Systemd 和 Cloudflare Tunnel 配置请参考 `DEPLOYMENT_AND_USAGE.md`。

### 3.2 `python_sandbox` (Docker 部署)

`python_sandbox` 服务被设计为在 Docker 容器中运行，以实现最高级别的安全和隔离。部署细节请参考 `PYTHON_SANDBOX_GUIDE.md`。

## 4. API 使用方式

### 4.1 端点

- **主服务 URL**: `https://tools.10110531.xyz/api/v1/execute_tool`
- **Method**: `POST`
- **Content-Type**: `application/json`

*(注意: `python_sandbox` 使用独立的端点 `https://pythonsandbox.10110531.xyz/api/v1/python_sandbox`)*

### 4.2 请求体格式

请求体必须是一个包含以下两个字段的 JSON 对象：

- `tool_name` (string, required): 要执行的工具的名称。
- `parameters` (object, required): 一个包含该工具所需所有参数的字典。

**示例请求体:**
```json
{
  "tool_name": "firecrawl",
  "parameters": {
    "mode": "scrape",
    "parameters": {
      "url": "https://www.firecrawl.dev/"
    }
  }
}
```

### 4.3 成功响应

- **HTTP Status Code**: `200 OK`
- **Body**: 一个包含 `success: true` 和 `data` 字段的 JSON 对象。`data` 对象的结构由执行的工具决定。

### 4.4 失败响应

- **HTTP Status Code**:
    - `404 Not Found`: 如果请求的 `tool_name` 不存在。
    - `400 Bad Request`: 如果为工具提供的 `parameters` 未通过验证。
    - `500 Internal Server Error`: 如果工具在执行过程中发生意外错误。
- **Body**: 响应体将包含一个描述错误详情的 JSON 对象。

**示例 404 响应 (已更新):**
```json
{
    "detail": "Tool 'non_existent_tool' not found. Available tools on this endpoint are: ['tavily_search', 'firecrawl']"
}
```

## 5. 可用工具列表

---

### 5.1 `tavily_search`

- **描述**: 使用 Tavily API 执行网络搜索，以查找实时信息。
- **输入参数 (`parameters`)**:

| 参数名         | 类型   | 是否必需 | 默认值     | 描述                                     |
|----------------|--------|----------|------------|------------------------------------------|
| `query`        | string | **是**   | N/A        | 要执行的搜索查询。                       |
| `search_depth` | string | 否       | "advanced" | 搜索深度: "basic" 或 "advanced"。        |
| `max_results`  | integer| 否       | 5          | 要返回的最大搜索结果数量。               |

- **使用示例 (`curl` for Windows CMD)**:
  ```bash
  curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"tavily_search\", \"parameters\": {\"query\": \"Who is the founder of OpenAI?\"}}"
  ```

---

### 5.2 `firecrawl`

- **描述**: 一个强大的工具，用于抓取、爬取、搜索网页或通过 AI 提取结构化数据。通过 `mode` 参数选择具体功能。
- **输入参数 (`parameters`)**:

| 参数名       | 类型   | 是否必需 | 描述                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `mode`       | string | **是**   | 功能模式。可选值: `'scrape'`, `'search'`, `'crawl'`, `'map'`, `'extract'`, `'check_status'` |
| `parameters` | object | **是**   | 一个包含所选 `mode` 所需参数的字典。                                 |

#### `firecrawl` - `scrape` 模式

- **描述**: 抓取单个 URL 的内容。
- **`parameters` 字典内容**:
    - `url` (string, **是**): 要抓取的页面 URL。
    - `formats` (list, 否, 默认 `["markdown"]`): 需要的内容格式，如 `["markdown", "html"]`。

- **使用示例 (`curl` for Windows CMD)**:
  ```bash
  curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"firecrawl\", \"parameters\": {\"mode\": \"scrape\", \"parameters\": {\"url\": \"https://firecrawl.dev\"}}}"
  ```

#### `firecrawl` - `search` 模式

- **描述**: 执行网络搜索并返回结果。
- **`parameters` 字典内容**:
    - `query` (string, **是**): 搜索关键词。
    - `limit` (integer, 否, 默认 `5`): 返回结果数量。
    - `scrape_options` (object, 否): 对搜索结果进行抓取的选项。

- **使用示例 (`curl` for Windows CMD)**:
  ```bash
  curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"firecrawl\", \"parameters\": {\"mode\": \"search\", \"parameters\": {\"query\": \"What is Firecrawl?\"}}}"
  ```

#### `firecrawl` - `crawl` 模式

- **描述**: 启动一个异步的整站爬取任务。此模式会立即返回一个 `job_id`。
- **`parameters` 字典内容**:

| 参数名           | 类型   | 是否必需 | 默认值 | 描述                     |
|------------------|--------|----------|--------|--------------------------|
| `url`            | string | **是**   | N/A    | 开始爬取的 URL。         |
| `limit`          | integer| 否       | 10     | 最大爬取页面数量。       |
| `scrape_options` | object | 否       | None   | 对每个页面进行抓取的选项。 |

#### `firecrawl` - `map` 模式

- **描述**: 发现并返回一个网站的所有可达 URL。
- **`parameters` 字典内容**:

| 参数名   | 类型   | 是否必需 | 默认值 | 描述                 |
|----------|--------|----------|--------|----------------------|
| `url`    | string | **是**   | N/A    | 要映射的网站 URL。   |
| `search` | string | 否       | None   | 用于过滤 URL 的关键词。 |

#### `firecrawl` - `extract` 模式

- **描述**: 启动一个异步的 AI 数据提取任务。此模式会立即返回一个 `job_id`。
- **`parameters` 字典内容**:

| 参数名   | 类型        | 是否必需 | 默认值 | 描述                                   |
|----------|-------------|----------|--------|----------------------------------------|
| `urls`   | list[string]| **是**   | N/A    | 要提取数据的 URL 列表。                |
| `prompt` | string      | 否       | None   | 用于指导提取的自然语言提示。           |
| `schema` | object      | 否       | None   | 用于定义输出结构的 JSON Schema。       |

#### `firecrawl` - `check_status` 模式

- **描述**: 检查一个异步任务（如 `crawl` 或 `extract`）的状态和结果。
- **`parameters` 字典内容**:

| 参数名   | 类型   | 是否必需 | 描述           |
|----------|--------|----------|----------------|
| `job_id` | string | **是**   | 要查询的任务 ID。 |

---

### 5.3 `python_sandbox`

- **描述**: 在一个高度安全、隔离的 Docker 沙箱环境中执行 Python 代码。
- **API 端点**: `https://pythonsandbox.10110531.xyz/api/v1/python_sandbox` *(注意: 专用端点)*
- **输入参数 (`parameters`)**:

| 参数名 | 类型   | 是否必需 | 描述                     |
|----------|--------|----------|--------------------------|
| `code`   | string | **是**   | 要在沙箱中执行的 Python 代码。 |

- **使用示例 (`curl` for Windows CMD)**:
  ```bash
  curl -X POST "https://pythonsandbox.10110531.xyz/api/v1/python_sandbox" -H "Content-Type: application/json" -d "{\"parameters\": {\"code\": \"print('Hello from sandbox')\"}}"