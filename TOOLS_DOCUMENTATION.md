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
    - **部署方式**: 通过 Gunicorn 和 Systemd 作为后台服务持久化运行。

## 3. 安装与运行

1.  **代码获取**: 将 `py_tool_server` 文件夹上传到服务器（例如 `/home/ren/py_tool_server`）。
2.  **进入目录**: `cd /home/ren/py_tool_server`
3.  **创建并激活虚拟环境**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
4.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```
5.  **本地测试运行**:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8827
    ```
6.  **生产环境部署**: 详细的 Systemd 和 Cloudflare Tunnel 配置请参考 `server_configuration.md` 中的“阶段四”。

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

- **描述**: 在一个高度安全、隔离的沙箱环境中执行 Python 代码片段，并返回其标准输出和标准错误。此工具无法访问网络或主机文件系统，确保了代码执行的安全性。

- **输入参数 (`parameters`)**:

| 参数名 | 类型   | 是否必需 | 默认值 | 描述                     |
|----------|--------|----------|--------|--------------------------|
| `code`   | string | **是**   | N/A    | 要在沙箱中执行的 Python 代码。 |


- **输出 (`data` 字段内容)**:
  成功时，`data` 字段是一个包含以下两个键的 JSON 对象：
    - `stdout` (string): 代码执行后的标准输出内容。
    - `stderr` (string): 代码执行期间产生的任何错误信息。如果代码成功运行，此字段将为空字符串。

- **使用示例 (`curl`)**:
  ```bash
  curl -X POST 'https://tools.10110531.xyz/api/v1/python_sandbox' \
  --header 'Content-Type: application/json' \
  --data '{
      "tool_name": "python_sandbox",
      "parameters": {
          "code": "import sys\nprint('Hello from the sandbox!')\nprint('Error message', file=sys.stderr)"
      }
  }'
  ```

- **示例成功响应**:
  ```json
  {
      "success": true,
      "data": {
          "stdout": "Hello from the sandbox!\n",
          "stderr": "Error message\n"
      }
  }
  ```