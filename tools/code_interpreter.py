import docker
import asyncio
import logging
from pydantic import BaseModel, Field
from docker.errors import DockerException, ContainerError, ImageNotFound, NotFound
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import json
import base64

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
import sys, traceback, io, json, base64, os
from io import BytesIO
import glob

# --- Capture matplotlib title ---
title_holder = [None] # Use a list to hold the title
try:
    import matplotlib.pyplot as plt
    original_title_func = plt.title
    def new_title_func(label, *args, **kwargs):
        title_holder[0] = label
        return original_title_func(label, *args, **kwargs)
    plt.title = new_title_func
except ImportError:
    pass # Matplotlib not available or used

# --- Redirect stdout/stderr ---
old_stdout = sys.stdout
old_stderr = sys.stderr
sys.stdout = buffer_stdout = io.StringIO()
sys.stderr = buffer_stderr = io.StringIO()

stdout_val = ""
stderr_val = ""
file_output = None

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
    # Pass matplotlib into the exec context if it was imported
    exec_globals = {{'__builtins__': safe_builtins}}
    if 'plt' in locals():
        exec_globals['plt'] = plt
        
    exec({repr(parameters.code)}, exec_globals)
    stdout_val = buffer_stdout.getvalue()
    stderr_val = buffer_stderr.getvalue()
except Exception as e:
    stdout_val = buffer_stdout.getvalue()
    stderr_val = buffer_stderr.getvalue() + '\\n' + traceback.format_exc()
finally:
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    
    # --- 扫描/tmp目录查找生成的文件 ---
    try:
        # 查找常见的办公文档和PDF文件
        file_patterns = [
            '/tmp/*.docx',
            '/tmp/*.xlsx', 
            '/tmp/*.pptx',
            '/tmp/*.pdf',
            '/tmp/*.png',
            '/tmp/*.jpg',
            '/tmp/*.jpeg'
        ]
        
        found_files = []
        for pattern in file_patterns:
            found_files.extend(glob.glob(pattern))
        
        # 如果找到文件，读取第一个文件并编码为Base64
        if found_files:
            file_path = found_files[0]  # 取第一个找到的文件
            filename = os.path.basename(file_path)
            
            # 确定文件类型和MIME类型
            file_ext = filename.split('.')[-1].lower()
            mime_types = {{
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'pdf': 'application/pdf',
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg'
            }}
            
            file_type_map = {{
                'docx': 'word',
                'xlsx': 'excel', 
                'pptx': 'ppt',
                'pdf': 'pdf',
                'png': 'image',
                'jpg': 'image',
                'jpeg': 'image'
            }}
            
            mime_type = mime_types.get(file_ext, 'application/octet-stream')
            file_type = file_type_map.get(file_ext, 'binary')
            
            # 读取文件并编码为Base64
            with open(file_path, 'rb') as f:
                file_content = f.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            file_output = {{
                "type": file_type,
                "filename": filename,
                "mime_type": mime_type,
                "data_base64": file_base64
            }}
            
            # 如果是图片，添加标题信息
            if file_type == 'image':
                file_output["title"] = title_holder[0] if title_holder[0] else "Generated Image"
    except Exception as e:
        # 文件扫描或读取失败，不影响主流程
        pass

# --- Format output ---
if file_output:
    # 如果有文件输出，优先返回文件
    print(json.dumps(file_output))
else:
    # 检查是否是直接输出的图片base64
    stripped_stdout = stdout_val.strip()
    is_image = False
    if stripped_stdout.startswith(('iVBORw0KGgo', '/9j/')):
        try:
            base64.b64decode(stripped_stdout, validate=True)
            is_image = True
        except Exception:
            is_image = False

    if is_image:
        captured_title = title_holder[0] if title_holder[0] else "Generated Chart"
        output_data = {{
            "type": "image",
            "title": captured_title,
            "image_base64": stripped_stdout
        }}
        print(json.dumps(output_data))
    else:
        # 对于非文件输出，返回文本
        output_data = {{
            "type": "text",
            "stdout": stdout_val,
            "stderr": stderr_val
        }}
        print(json.dumps(output_data))
"""

        try:
            # 以同步阻塞方式运行容器，直接获取输出
            output = self.docker_client.containers.run(
                image=image_name,
                command=["python", "-c", runner_script],
                network_disabled=True,   # 无网络
                environment={'MPLCONFIGDIR': '/tmp'},
                mem_limit="1g",          # 内存上限
                cpu_period=100_000,
                cpu_quota=50_000,        # 0.5 核
                remove=True,             # 执行后自动删除
                read_only=True,          # 只读文件系统
                tmpfs={'/tmp': 'size=100M,mode=1777'},  # 可写的tmpfs用于保存文件
                stdout=True,
                stderr=True,
                detach=False             # 同步执行，等待结果返回
            )
            
            # 解码输出
            stdout = output.decode('utf-8', errors='ignore')
            
            # 尝试解析JSON输出
            try:
                parsed_output = json.loads(stdout)
                return {
                    "success": True,
                    "data": {
                        "stdout": parsed_output,
                        "stderr": "",  # 在此模式下，stderr通常合并到stdout
                        "exit_code": 0
                    }
                }
            except json.JSONDecodeError:
                # 如果不是JSON，则作为纯文本返回
                return {
                    "success": True,
                    "data": {
                        "stdout": stdout,
                        "stderr": "",
                        "exit_code": 0
                    }
                }
            
        except ContainerError as e:
            # 容器内代码执行出错 (非零退出码)
            stdout = e.stdout.decode('utf-8', errors='ignore') if e.stdout else ""
            stderr = e.stderr.decode('utf-8', errors='ignore') if e.stderr else ""
            
            # 尝试解析可能的JSON输出
            try:
                parsed_stdout = json.loads(stdout) if stdout else stdout
                return {
                    "success": True, # 成功执行了代码，但代码本身有错误
                    "data": {
                        "stdout": parsed_stdout,
                        "stderr": stderr,
                        "exit_code": e.exit_status
                    }
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
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