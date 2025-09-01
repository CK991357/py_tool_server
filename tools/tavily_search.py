import os
from tavily import TavilyClient
from pydantic import BaseModel, Field

# Load the API key from environment variables once when the module is loaded.
api_key = os.getenv("TAVILY_API_KEY")
if not api_key:
    raise ValueError("TAVILY_API_KEY not found in environment variables. Please set it in the .env file.")

tavily_client = TavilyClient(api_key=api_key)

class TavilySearchInput(BaseModel):
    """Input schema for the Tavily Search tool."""
    query: str = Field(description="The search query to execute.")
    search_depth: str = Field(
        default="advanced",
        description="The depth of the search. 'basic' is faster, 'advanced' is more comprehensive."
    )
    max_results: int = Field(
        default=5,
        description="The maximum number of search results to return."
    )

class TavilySearchTool:
    """
    A tool for performing web searches using the Tavily API.
    """
    name = "tavily_search"
    description = (
        "Performs a web search using the Tavily API to find real-time information, "
        "answer questions, or research topics. Returns a list of search results with snippets and links."
    )
    input_schema = TavilySearchInput

    async def execute(self, parameters: TavilySearchInput) -> dict:
        """
        Executes the Tavily search.
        """
        try:
            # The Tavily client's search method returns a dictionary.
            search_result = tavily_client.search(
                query=parameters.query,
                search_depth=parameters.search_depth,
                max_results=parameters.max_results
            )
            return {
                "success": True,
                "data": search_result
            }
        except Exception as e:
            # Handle potential exceptions during the API call
            return {
                "success": False,
                "error": f"An error occurred during the Tavily search: {str(e)}"
            }