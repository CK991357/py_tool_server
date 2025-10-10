import os
from firecrawl import Firecrawl
from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Any, Optional

# 1. 从环境变量加载 API Key
api_key = os.getenv("FIRECRAWL_API_KEY")
if not api_key:
    raise ValueError("FIRECRAWL_API_KEY not found in environment variables. Please set it in the .env file.")

firecrawl_client = Firecrawl(api_key=api_key)

# 2. 为不同的子功能定义输入模型以进行验证

class ScrapeParams(BaseModel):
    url: str = Field(description="The URL of the page to scrape.")
    formats: List[str] = Field(default=["markdown"], description="List of formats, e.g., ['markdown', 'html'].")
    # ... 可以根据需要添加更多参数

class SearchParams(BaseModel):
    query: str = Field(description="The search query.")
    limit: int = Field(default=5, description="Number of search results.")
    scrape_options: Optional[Dict[str, Any]] = Field(default=None, description="Options for scraping search results.")

class CrawlParams(BaseModel):
    url: str = Field(description="The starting URL for the crawl.")
    limit: int = Field(default=10, description="Maximum number of pages to crawl.")
    scrape_options: Optional[Dict[str, Any]] = Field(default=None, description="Options for scraping each page.")
    
class MapParams(BaseModel):
    url: str = Field(description="The URL of the website to map.")
    search: Optional[str] = Field(default=None, description="Optional search term to filter URLs.")

class ExtractParams(BaseModel):
    urls: List[str] = Field(description="A list of URLs to extract structured data from.")
    prompt: Optional[str] = Field(default=None, description="A natural language prompt for data extraction.")
    schema_definition: Optional[Dict[str, Any]] = Field(default=None, alias="schema", description="A JSON schema to define the output structure.")

class CheckStatusParams(BaseModel):
    job_id: str = Field(description="The job ID of the crawl or extract task to check.")

# 3. 定义总的工具输入模型
class FirecrawlInput(BaseModel):
    mode: Literal['scrape', 'search', 'crawl', 'map', 'extract', 'check_status'] = Field(
        description="The Firecrawl function to execute."
    )
    parameters: Dict[str, Any] = Field(
        description="Parameters for the selected mode, matching the respective schema."
    )

# 4. 创建工具类
class FirecrawlTool:
    name = "firecrawl"
    description = (
        "A powerful tool to scrape, crawl, search, map, or extract structured data from web pages. "
        "Modes: 'scrape' for a single URL, 'search' for a web query, 'crawl' for an entire website, "
        "'map' to get all links, 'extract' for AI-powered data extraction, and 'check_status' for async jobs."
    )
    input_schema = FirecrawlInput

    async def execute(self, parameters: FirecrawlInput) -> dict:
        try:
            mode = parameters.mode
            params = parameters.parameters

            result = None
            if mode == 'scrape':
                validated_params = ScrapeParams(**params)
                result = firecrawl_client.scrape(
                    url=validated_params.url,
                    formats=validated_params.formats
                )
            elif mode == 'search':
                validated_params = SearchParams(**params)
                result = firecrawl_client.search(
                    query=validated_params.query,
                    limit=validated_params.limit,
                    scrape_options=validated_params.scrape_options
                )
            elif mode == 'crawl':
                validated_params = CrawlParams(**params)
                # crawl API 返回一个任务ID
                job_id = firecrawl_client.crawl(
                    url=validated_params.url,
                    limit=validated_params.limit,
                    scrape_options=validated_params.scrape_options
                )
                result = {"status": "crawl job started", "job_id": job_id}
            elif mode == 'map':
                validated_params = MapParams(**params)
                result = firecrawl_client.map(
                    url=validated_params.url,
                    search=validated_params.search
                )
            elif mode == 'extract':
                validated_params = ExtractParams(**params)
                # extract API 返回一个任务ID
                job_id = firecrawl_client.extract(
                    urls=validated_params.urls,
                    prompt=validated_params.prompt,
                    schema=validated_params.schema_definition
                )
                result = {"status": "extract job started", "job_id": job_id}
            elif mode == 'check_status':
                validated_params = CheckStatusParams(**params)
                result = firecrawl_client.check_crawl_status(validated_params.job_id)
            else:
                return {"success": False, "error": f"Invalid mode '{mode}'."}

            return {"success": True, "data": result}

        except Exception as e:
            # 包含Pydantic验证错误
            return {"success": False, "error": f"An error occurred in Firecrawl tool: {str(e)}"}