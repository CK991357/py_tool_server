# Firecrawl 工具使用指南

## 1. 概述

`firecrawl` 工具是 `py_tool_server` 服务中的一个强大功能模块，它通过封装 [Firecrawl API](https://www.firecrawl.dev/)，提供了先进的网页抓取、爬取、搜索和 AI 数据提取能力。

本工具的核心设计思想是通过一个统一的 `tool_name: "firecrawl"` 入口，利用 `mode` 参数来调用其多样化的子功能。

## 2. 核心调用方式

所有对 `firecrawl` 工具的调用都遵循统一的请求结构。

- **端点**: `https://tools.10110531.xyz/api/v1/execute_tool`
- **请求体**:
  ```json
  {
    "tool_name": "firecrawl",
    "parameters": {
      "mode": "<功能模式>",
      "parameters": {
        "<该模式对应的具体参数>": "..."
      }
    }
  }
  ```

## 3. 功能模式详解

### 3.1 `scrape` - 单页抓取

- **功能**: 抓取指定单个 URL 的内容，并将其转换为 LLM 友好的格式。
- **实现方式**: 调用 `firecrawl-py` SDK 的 `scrape()` 方法。这是一个同步操作，会立即返回抓取结果。
- **参数 (`parameters` 字典):**
  - `url` (string, **必需**): 要抓取的页面 URL。
  - `formats` (list, 可选, 默认 `["markdown"]`): 一个包含所需内容格式的列表。可选值包括 `"markdown"`, `"html"`, `"rawHtml"`, `"screenshot"`, `"links"` 等。
- **使用与测试 (Windows CMD):**
  ```bash
  curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"firecrawl\", \"parameters\": {\"mode\": \"scrape\", \"parameters\": {\"url\": \"https://docs.firecrawl.dev/\"}}}"
  ```
- **预期成功响应**:
  ```json
  {
      "success": true,
      "data": {
          "markdown": "# Firecrawl Docs\n\nWelcome to the Firecrawl documentation...",
          "metadata": {
              "title": "Firecrawl Docs",
              "sourceURL": "https://docs.firecrawl.dev/"
          },
          // ... 其他请求的格式数据
      }
  }
  ```

### 3.2 `search` - 网络搜索

- **功能**: 执行网络搜索，类似于搜索引擎，并可选择性地直接抓取搜索结果的内容。
- **实现方式**: 调用 SDK 的 `search()` 方法。同步操作，立即返回结果。
- **参数 (`parameters` 字典):**
  - `query` (string, **必需**): 搜索的关键词。
  - `limit` (integer, 可选, 默认 `5`): 希望返回的搜索结果数量。
  - `scrape_options` (object, 可选): 如果提供此参数，将对返回的每个搜索结果执行抓取。例如: `{"formats": ["markdown"]}`。
- **使用与测试 (Windows CMD):**
  ```bash
  curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"firecrawl\", \"parameters\": {\"mode\": \"search\", \"parameters\": {\"query\": \"What is Firecrawl?\"}}}"
  ```
- **预期成功响应**:
  ```json
  {
      "success": true,
      "data": [
          {
              "url": "https://firecrawl.dev",
              "title": "Firecrawl | Home Page",
              "description": "Turn websites into LLM-ready data with Firecrawl"
          },
          // ... 其他搜索结果
      ]
  }
  ```

### 3.3 `map` - 网站地图

- **功能**: 快速发现并列出一个网站上所有可访问的链接。
- **实现方式**: 调用 SDK 的 `map()` 方法。同步操作，立即返回结果。
- **参数 (`parameters` 字典):**
  - `url` (string, **必需**): 要映射的网站的根 URL。
  - `search` (string, 可选): 提供一个关键词，可以对结果进行过滤和排序。
- **使用与测试 (Windows CMD):**
  ```bash
  curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"firecrawl\", \"parameters\": {\"mode\": \"map\", \"parameters\": {\"url\": \"https://firecrawl.dev\"}}}"
  ```
- **预期成功响应**:
  ```json
  {
      "success": true,
      "data": {
          "links": [
              { "url": "https://firecrawl.dev/pricing", "title": "Firecrawl Pricing" },
              { "url": "https://firecrawl.dev/blog", "title": "Firecrawl Blog" }
              // ... 其他链接
          ]
      }
  }
  ```

### 3.4 `crawl` & `extract` - 异步任务

- **功能**:
  - `crawl`: 启动一个异步任务，从一个起始 URL 开始，爬取整个网站的所有页面。
  - `extract`: 启动一个异步任务，使用 AI 从一个或多个 URL 中提取结构化的 JSON 数据。
- **实现方式**: 调用 SDK 的 `crawl()` 或 `extract()` 方法。这些方法是非阻塞的，会立即返回一个任务 ID。
- **`crawl` 的参数 (`parameters` 字典):**
  - `url` (string, **必需**): 爬取的起始 URL。
  - `limit` (integer, 可选, 默认 `10`): 最大爬取页面数。
- **`extract` 的参数 (`parameters` 字典):**
  - `urls` (list, **必需**): 一个包含一个或多个 URL 的列表。
  - `prompt` (string, 可选): 指导 AI 提取数据的自然语言提示。
  - `schema` (object, 可选): 定义输出数据结构的 JSON Schema。
- **启动任务的响应**:
  ```json
  {
      "success": true,
      "data": {
          "status": "crawl job started", // 或 "extract job started"
          "job_id": "some-unique-job-identifier"
      }
  }
  ```

### 3.5 `check_status` - 检查异步任务状态

- **功能**: 查询一个 `crawl` 或 `extract` 任务的当前状态和最终结果。
- **实现方式**: 调用 SDK 的 `check_crawl_status()` 方法。
- **参数 (`parameters` 字典):**
  - `job_id` (string, **必需**): 之前启动任务时获取到的 `job_id`。
- **使用与测试 (Windows CMD):**
  ```bash
  # 将 "some-unique-job-identifier" 替换为真实的 job_id
  curl -X POST "https://tools.10110531.xyz/api/v1/execute_tool" -H "Content-Type: application/json" -d "{\"tool_name\": \"firecrawl\", \"parameters\": {\"mode\": \"check_status\", \"parameters\": {\"job_id\": \"some-unique-job-identifier\"}}}"
  ```
- **预期成功响应 (当任务完成时):**
  ```json
  {
      "success": true,
      "data": {
          "status": "completed",
          "total": 5,
          "data": [
              { "markdown": "...", "metadata": {...} },
              { "markdown": "...", "metadata": {...} }
              // ... 其他页面的数据
          ]
      }
  }
  ```

## 4. 异步任务工作流

对于 `crawl` 和 `extract` 这两个功能，需要遵循一个两步流程：

1.  **启动任务**: 发送一个 `mode: "crawl"` 或 `mode: "extract"` 的请求，并从响应中获取 `job_id`。
2.  **轮询结果**: 在一小段时间后（例如几秒或几十秒，取决于任务大小），发送一个 `mode: "check_status"` 的请求，并附上 `job_id`。重复此步骤，直到响应中的 `status` 变为 `"completed"`，然后就可以在 `data` 字段中获取最终结果。