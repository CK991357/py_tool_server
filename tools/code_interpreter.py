import docker
import asyncio
import logging
from pydantic import BaseModel, Field
from docker.errors import DockerException, ContainerError, ImageNotFound, NotFound
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic Input Schema ---
class CodeInterpreterInput(BaseModel):
    """Input schema for the Code Interpreter tool."""
    code: str = Field(description="The Python code to be executed in the sandbox.")

# --- Tool Class ---
class CodeInterpreterTool:
    """
    Executes Python code in a secure, isolated Docker sandbox.
    Returns stdout/stderr. No network, no host filesystem, mem+CPU capped.
    """
    name = "python_sandbox"
    description = (
        "Executes a snippet of Python code in a sandboxed environment and returns the output. "
        "This tool is secure and has no access to the internet or the host filesystem."
    )
    input_schema = CodeInterpreterInput

    def __init__(self):
        self.docker_client = None
        self.initialize_docker_client()

    def initialize_docker_client(self):
        """Initialize Docker client with error handling"""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()  # 确认 Docker 可用
            logger.info("Docker client initialized successfully")
        except DockerException as e:
            logger.warning(f"Docker initialization failed: {e}")
            logger.warning("Container will continue without Docker access")
            self.docker_client = None

    def check_image(self, image_name):
        """Checks if the Docker image exists locally, raises error if not."""
        if not self.docker_client:
            raise RuntimeError("Docker client not available")
        try:
            self.docker_client.images.get(image_name)
            logger.info(f"Image '{image_name}' found locally.")
        except ImageNotFound:
            logger.error(f"Image '{image_name}' not found.")
            raise RuntimeError(
                f"Docker image '{image_name}' not found. "
                f"Please build it first, for example, by running 'docker-compose build --no-cache' in the 'tools' directory."
            )

    async def execute(self, parameters: CodeInterpreterInput) -> dict:
        if not self.docker_client:
            return {
                "success": False, 
                "error": "Docker daemon not available. Please ensure Docker is running and accessible."
            }
            
        image_name = "tools-python-sandbox"
        
        # 确保镜像可用
        try:
            # We are not awaiting here because check_image is synchronous
            self.check_image(image_name)
        except Exception as e:
            return {"success": False, "error": f"Image preparation failed: {e}"}
        
        # 创建安全的执行环境
        runner_script = f"""
import sys, traceback, io
old_stdout = sys.stdout
old_stderr = sys.stderr
sys.stdout = buffer_stdout = io.StringIO()
sys.stderr = buffer_stderr = io.StringIO()

try:
    # 限制可用的内置函数
    # A more comprehensive but still safe list of built-in functions
    safe_builtins = {{
        # Core & Essential
        '__import__': __import__,
        'print': print,
        'repr': repr,
        # Data Types & Conversions
        'bool': bool, 'int': int, 'float': float, 'str': str,
        'list': list, 'dict': dict, 'set': set, 'tuple': tuple,
        'type': type,
        # Iteration & Data Structures
        'len': len, 'range': range, 'sorted': sorted, 'reversed': reversed,
        'zip': zip, 'enumerate': enumerate, 'slice': slice,
        # Math
        'abs': abs, 'max': max, 'min': min, 'sum': sum, 'round': round,
        'pow': pow, 'divmod': divmod,
        # Object Model & Introspection
        'isinstance': isinstance, 'issubclass': issubclass,
        'hasattr': hasattr, 'getattr': getattr, 'setattr': setattr,
    }}
    exec({repr(parameters.code)}, {{'__builtins__': safe_builtins}})
    stdout = buffer_stdout.getvalue()
    stderr = buffer_stderr.getvalue()
except Exception as e:
    stdout = buffer_stdout.getvalue()
    stderr = buffer_stderr.getvalue() + '\\n' + traceback.format_exc()
finally:
    sys.stdout = old_stdout
    sys.stderr = old_stderr

# 输出结果
print(stdout, end='')
print(stderr, file=sys.stderr, end='')
"""

        try:
            # 以同步阻塞方式运行容器，直接获取输出
            output = self.docker_client.containers.run(
                image=image_name,
                command=["python", "-c", runner_script],
                network_disabled=True,   # 无网络
                environment={'MPLCONFIGDIR': '/tmp'}, # ADDED
                mem_limit="1g",          # 内存上限
                cpu_period=100_000,
                cpu_quota=50_000,        # 0.5 核
                remove=True,             # 执行后自动删除
                read_only=True,          # 只读文件系统
                tmpfs={'/tmp': 'size=100M,mode=1777'},  # ADDED
                stdout=True,
                stderr=True,
                detach=False             # 同步执行，等待结果返回
            )
            
            # 解码输出
            stdout = output.decode('utf-8', errors='ignore')
            
            return {
                "success": True,
                "data": {
                    "stdout": stdout,
                    "stderr": "",  # 在此模式下，stderr通常合并到stdout
                    "exit_code": 0 # 如果执行到这里，说明没有抛出异常，exit_code为0
                }
            }
            
        except ContainerError as e:
            # 容器内代码执行出错 (非零退出码)
            stdout = e.stdout.decode('utf-8', errors='ignore') if e.stdout else ""
            stderr = e.stderr.decode('utf-8', errors='ignore') if e.stderr else ""
                
            return {
                "success": True, # 成功执行了代码，但代码本身有错误
                "data": {
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": e.exit_status
                }
            }
        except Exception as e:
            logger.error(f"Sandbox error: {e}")
            return {"success": False, "error": f"Sandbox error: {e}"}

# --- FastAPI Application ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    global code_interpreter_instance
    code_interpreter_instance = CodeInterpreterTool()
    yield
    # 关闭时清理
    if code_interpreter_instance and code_interpreter_instance.docker_client:
        code_interpreter_instance.docker_client.close()

app = FastAPI(lifespan=lifespan)

@app.post('/api/v1/python_sandbox')
async def run_python_sandbox(request_data: dict):
    """
    API endpoint to execute Python code in a sandbox.
    Expects a dictionary with a 'parameters' key, which in turn contains a 'code' key.
    """
    try:
        # 提取嵌套的 'code' 字段
        code_to_execute = request_data.get('parameters', {}).get('code')
        if not code_to_execute:
            raise HTTPException(
                status_code=422, 
                detail="Missing 'code' field within 'parameters' in the request body."
            )

        # 创建 CodeInterpreterInput 实例
        input_data = CodeInterpreterInput(code=code_to_execute)

        result = await code_interpreter_instance.execute(input_data)
        if result.get("success"):
            return result.get("data")
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Internal server error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.get('/health')
async def health_check():
    """Health check endpoint"""
    try:
        if code_interpreter_instance and code_interpreter_instance.docker_client:
            code_interpreter_instance.docker_client.ping()
            return {"status": "healthy", "docker": "connected"}
        else:
            return {"status": "degraded", "docker": "not_available"}
    except Exception as e:
        return {"status": "degraded", "docker": f"error: {e}"}

@app.get('/')
async def root():
    """Root endpoint with basic info"""
    return {
        "message": "Python Sandbox API",
        "version": "1.0",
        "endpoints": {
            "execute_code": "POST /api/v1/python_sandbox",
            "health_check": "GET /health"
        }
    }