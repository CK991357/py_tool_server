from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from dotenv import load_dotenv

# 在所有其他导入之前加载.env文件中的环境变量
load_dotenv()

# 导入我们真实的工具执行器
from tools.tool_registry import execute_tool

app = FastAPI(
    title="Python Tool Server",
    description="An extensible server for executing various tools via API.",
    version="0.1.0",
)

class ToolExecutionRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]

@app.get("/")
def read_root():
    """ A simple endpoint to check if the server is running. """
    return {"status": "Python Tool Server is running"}

@app.post("/api/v1/execute_tool")
async def api_execute_tool(request: ToolExecutionRequest):
    """
    Executes a specified tool with the given parameters.
    This is the main endpoint for the tool server.
    """
    try:
        # 调用工具执行器
        result = await execute_tool(request.tool_name, request.parameters)
        
        # 如果工具执行本身失败，也可能需要一个特定的HTTP状态码
        if isinstance(result, dict) and result.get("success") == False:
            # 检查是否有验证错误
            if "validation_details" in result:
                 raise HTTPException(status_code=400, detail=result) # Bad Request for validation errors
            # 其他工具执行错误
            raise HTTPException(status_code=500, detail=result)

        return result
    except ValueError as e:
        # 如果工具不存在，返回 404
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # 处理其他所有执行期间的错误
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# To run this server, you would use a command like:
# uvicorn main:app --host 0.0.0.0 --port 8827 --reload