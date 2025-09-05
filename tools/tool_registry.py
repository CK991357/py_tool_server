from typing import Dict, Any
from pydantic import ValidationError

# Import the tool classes
from .tavily_search import TavilySearchTool
from .code_interpreter import CodeInterpreterTool as PythonSandboxTool

# --- Tool Registry ---
# This dictionary maps tool names to their corresponding implementation classes.
# To add a new tool, simply import its class and add it here.
TOOL_REGISTRY = {
    TavilySearchTool.name: TavilySearchTool,
    PythonSandboxTool.name: PythonSandboxTool,
    # Future tools can be registered here, e.g.:
    # "read_file": ReadFileTool,
}

async def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Finds, validates, and executes the specified tool with the given parameters.

    Args:
        tool_name: The name of the tool to execute.
        parameters: A dictionary of parameters for the tool.

    Returns:
        A dictionary containing the result of the tool execution.

    Raises:
        ValueError: If the tool_name is not found in the registry.
        ValidationError: If the provided parameters do not match the tool's input schema.
    """
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Tool '{tool_name}' not found. Available tools are: {list(TOOL_REGISTRY.keys())}")

    tool_class = TOOL_REGISTRY[tool_name]
    
    # --- Input Validation using Pydantic ---
    try:
        # Get the Pydantic model from the tool class
        input_schema = tool_class.input_schema
        # Validate the incoming parameters against the schema
        validated_parameters = input_schema(**parameters)
    except ValidationError as e:
        # If validation fails, return a structured error
        return {
            "success": False,
            "error": "Input validation failed",
            "details": e.errors()
        }
    
    # --- Tool Execution ---
    try:
        # Instantiate the tool and execute it with validated parameters
        tool_instance = tool_class()
        result = await tool_instance.execute(validated_parameters)
        return result
    except Exception as e:
        # Catch-all for any other errors during tool execution
        return {
            "success": False,
            "error": f"An error occurred while executing tool '{tool_name}': {str(e)}"
        }
