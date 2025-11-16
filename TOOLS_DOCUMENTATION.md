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
    "detail": "Tool 'non_existent_tool' not found. Available tools on this endpoint are: ['tavily_search', 'firecrawl', 'stockfish_analyzer']"
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

### 5.3 `crawl4ai`

- **描述**: 一个强大的开源工具，用于抓取网页、深度爬取网站、提取结构化数据、导出PDF和捕获截图。支持多种深度爬取策略（BFS、DFS、BestFirst）、批量URL处理、AI驱动的数据提取和高级内容过滤。所有输出都作为内存流返回（二进制数据为base64格式）。
- **输入参数 (`parameters`)**:

| 参数名       | 类型   | 是否必需 | 描述                                                                 |
|--------------|--------|----------|----------------------------------------------------------------------|
| `mode`       | string | **是**   | 功能模式。可选值: `'scrape'`, `'deep_crawl'`, `'extract'`, `'batch_crawl'`, `'pdf_export'`, `'screenshot'` |
| `parameters` | object | **是**   | 一个包含所选 `mode` 所需参数的字典。                                 |

#### `crawl4ai` - `scrape` 模式

- **描述**: 抓取单个URL的内容，支持多种输出格式和可选截图/PDF导出。
- **`parameters` 字典内容**:

| 参数名                   | 类型    | 是否必需 | 默认值    | 描述                                      |
|--------------------------|---------|----------|-----------|-------------------------------------------|
| `url`                    | string  | **是**   | N/A       | 要抓取的页面URL。                         |
| `format`                 | string  | 否       | "markdown"| 输出格式: `'markdown'`, `'html'`, `'text'` |
| `css_selector`           | string  | 否       | None      | 用于提取特定内容的CSS选择器。             |
| `include_links`          | boolean | 否       | true      | 是否在输出中包含链接。                    |
| `include_images`         | boolean | 否       | true      | 是否在输出中包含图片。                    |
| `return_screenshot`      | boolean | 否       | false     | 是否返回base64格式的截图。                |
| `return_pdf`             | boolean | 否       | false     | 是否返回base64格式的PDF。                 |
| `screenshot_quality`     | integer | 否       | 70        | 截图JPEG质量 (10-100)。                  |
| `screenshot_max_width`   | integer | 否       | 1920      | 截图最大宽度。                            |
| `word_count_threshold`   | integer | 否       | 10        | 内容块的最小词数阈值。                    |
| `exclude_external_links` | boolean | 否       | true      | 从内容中移除外部链接。                    |

- **使用示例 (`curl` for Windows CMD)**:
  ```bash
  curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"crawl4ai\", \"parameters\": {\"mode\": \"scrape\", \"parameters\": {\"url\": \"https://example.com\", \"format\": \"markdown\", \"return_screenshot\": true, \"screenshot_quality\": 80}}}"
  ```

#### `crawl4ai` - `deep_crawl` 模式

- **描述**: 深度爬取整个网站，支持多种爬取策略和关键词相关性评分。
- **`parameters` 字典内容**:

| 参数名             | 类型          | 是否必需 | 默认值    | 描述                                      |
|--------------------|---------------|----------|-----------|-------------------------------------------|
| `url`              | string        | **是**   | N/A       | 开始深度爬取的URL。                       |
| `max_depth`        | integer       | 否       | 2         | 最大爬取深度。                            |
| `max_pages`        | integer       | 否       | 50        | 最大爬取页面数量。                        |
| `strategy`         | string        | 否       | "bfs"     | 爬取策略: `'bfs'`, `'dfs'`, `'best_first'` |
| `include_external` | boolean       | 否       | false     | 是否跟随外部链接。                        |
| `keywords`         | list[string]  | 否       | None      | 用于相关性评分的关键词。                  |
| `url_patterns`     | list[string]  | 否       | None      | 要包含的URL模式。                         |
| `stream`           | boolean       | 否       | false     | 是否逐步流式返回结果。                    |

- **使用示例 (`curl` for Windows CMD)**:
  ```bash
  curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"crawl4ai\", \"parameters\": {\"mode\": \"deep_crawl\", \"parameters\": {\"url\": \"https://example.com\", \"max_depth\": 3, \"strategy\": \"bfs\", \"keywords\": [\"product\", \"price\"]}}}"
  ```

#### `crawl4ai` - `extract` 模式

- **描述**: 从网页提取结构化数据，支持CSS选择器和LLM两种提取策略。
- **`parameters` 字典内容**:

| 参数名              | 类型          | 是否必需 | 默认值  | 描述                                      |
|---------------------|---------------|----------|---------|-------------------------------------------|
| `url`               | string        | **是**   | N/A     | 要提取数据的URL。                         |
| `schema_definition` | object        | **是**   | N/A     | 用于数据提取的JSON schema定义。           |
| `css_selector`      | string        | 否       | None    | 提取的基础CSS选择器。                     |
| `extraction_type`   | string        | 否       | "css"   | 提取策略类型: `'css'`, `'llm'`。          |
| `prompt`            | string        | 否       | None    | LLM提取的提示语。                         |

- **使用示例 (`curl` for Windows CMD)**:
  ```bash
  curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"crawl4ai\", \"parameters\": {\"mode\": \"extract\", \"parameters\": {\"url\": \"https://example.com\", \"schema_definition\": {\"title\": \"string\", \"description\": \"string\"}, \"extraction_type\": \"css\"}}}"
  ```

#### `crawl4ai` - `batch_crawl` 模式

- **描述**: 批量爬取多个URL，支持并发处理。
- **`parameters` 字典内容**:

| 参数名            | 类型          | 是否必需 | 默认值  | 描述                          |
|-------------------|---------------|----------|---------|-------------------------------|
| `urls`            | list[string]  | **是**   | N/A     | 要爬取的URL列表。             |
| `stream`          | boolean       | 否       | false   | 是否在完成时流式返回结果。    |
| `concurrent_limit`| integer       | 否       | 3       | 最大并发爬取数。              |

- **使用示例 (`curl` for Windows CMD)**:
  ```bash
  curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"crawl4ai\", \"parameters\": {\"mode\": \"batch_crawl\", \"parameters\": {\"urls\": [\"https://example.com/page1\", \"https://example.com/page2\"], \"concurrent_limit\": 2}}}"
  ```

#### `crawl4ai` - `pdf_export` 模式

- **描述**: 将网页导出为PDF格式。
- **`parameters` 字典内容**:

| 参数名              | 类型    | 是否必需 | 默认值  | 描述                          |
|---------------------|---------|----------|---------|-------------------------------|
| `url`               | string  | **是**   | N/A     | 要导出为PDF的URL。            |
| `return_as_base64`  | boolean | 否       | true    | 是否返回base64字符串。        |

- **使用示例 (`curl` for Windows CMD)**:
  ```bash
  curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"crawl4ai\", \"parameters\": {\"mode\": \"pdf_export\", \"parameters\": {\"url\": \"https://example.com\", \"return_as_base64\": true}}}"
  ```

#### `crawl4ai` - `screenshot` 模式

- **描述**: 捕获网页截图，支持压缩和质量控制。
- **`parameters` 字典内容**:

| 参数名              | 类型    | 是否必需 | 默认值  | 描述                          |
|---------------------|---------|----------|---------|-------------------------------|
| `url`               | string  | **是**   | N/A     | 要截图的URL。                 |
| `full_page`         | boolean | 否       | true    | 是否捕获整个页面。            |
| `return_as_base64`  | boolean | 否       | true    | 是否返回base64字符串。        |
| `quality`           | integer | 否       | 70      | 截图JPEG质量 (10-100)。      |
| `max_width`         | integer | 否       | 1920    | 截图最大宽度。                |
| `max_height`        | integer | 否       | 5000    | 截图最大高度。                |

- **使用示例 (`curl` for Windows CMD)**:
  ```bash
  curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"crawl4ai\", \"parameters\": {\"mode\": \"screenshot\", \"parameters\": {\"url\": \"https://example.com\", \"quality\": 85, \"max_width\": 1200}}}"
  ```

---

### 5.4 `python_sandbox`

- **描述**: 在一个高度安全、隔离的 Docker 沙箱环境中执行 Python 代码，支持数据分析、可视化和生成 Base64 编码的 PNG 图像。
- **API 端点**: `https://pythonsandbox.10110531.xyz/api/v1/python_sandbox` *(注意: 专用端点)*
- **输入参数 (`parameters`)**:

| 参数名 | 类型   | 是否必需 | 描述                                |
|----------|--------|----------|-------------------------------------|
| `code`   | string | **是**   | 要在沙箱中执行的 Python 代码，可包含 `matplotlib` 和 `seaborn` 绘图代码。 |

- **成功响应示例 (`stdout` 包含 Base64 图像)**:
  ```json
  {
      "stdout": "iVBORw0KGgoAAAA... (Base64 encoded PNG image data)",
      "stderr": "",
      "exit_code": 0
  }
  ```
  *(注: `stdout` 中 Base64 字符串的实际内容会非常长)*

- **使用示例 (`curl` for Windows CMD) - 数据可视化**:
  ```bash
  curl -X POST "https://pythonsandbox.10110531.xyz/api/v1/python_sandbox" -H "Content-Type: application/json" -d "{ \"parameters\": { \"code\": \"import matplotlib\\nmatplotlib.use('Agg')\\nimport matplotlib.pyplot as plt\\nimport io\\nimport base64\\nplt.plot([0,1,2],[0,1,0]);buf=io.BytesIO();plt.savefig(buf,format='png',bbox_inches='tight');buf.seek(0);print(base64.b64encode(buf.read()).decode());buf.close();plt.close('all')\" } }"
  ```

- **使用示例 (`curl` for Windows CMD) - 文本输出**:
  ```bash
  curl -X POST "https://pythonsandbox.10110531.xyz/api/v1/python_sandbox" -H "Content-Type: application/json" -d "{\"parameters\": {\"code\": \"print('Hello from sandbox')\"}}"
  ```
---

### 5.5 `stockfish_analyzer`

- **描述**: 一个强大的国际象棋分析工具，使用 Stockfish 引擎。通过不同的模式获取最佳走法、前几步走法或进行局面评估。
- **输入参数 (`parameters`)**:

| 参数名 | 类型 | 是否必需 | 描述 |
|---|---|---|---|
| `mode` | string | **是** | 分析模式。可选值: `'get_best_move'`, `'get_top_moves'`, `'evaluate_position'`。 |
| `fen` | string | **是** | 当前棋盘局面的 FEN 字符串。 |
| `options` | object | 否 | 可选的分析参数，详见下表。 |

#### `stockfish_analyzer` - `options` 字典内容

| 参数名 | 类型 | 是否必需 | 默认值 | 描述 |
|---|---|---|---|---|
| `skill_level` | integer | 否 | 20 | Stockfish 的技能等级 (0-20)。 |
| `depth` | integer | 否 | 15 | 分析深度 (1-30)。值越高，分析越强但越慢。 |
| `count` | integer | 否 | 3 | 仅在 `mode` 为 `'get_top_moves'` 时有效。返回的最佳走法数量 (1-10)。 |

- **使用示例 (`curl` for Windows CMD) - 获取最佳走法**:
  ```bash
  curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"stockfish_analyzer\", \"parameters\": {\"mode\": \"get_best_move\", \"fen\": \"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\"}}"
  ```

- **使用示例 (`curl` for Windows CMD) - 获取前 5 步走法**:
  ```bash
  curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"stockfish_analyzer\", \"parameters\": {\"mode\": \"get_top_moves\", \"fen\": \"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\", \"options\": {\"count\": 5}}}"
  ```
