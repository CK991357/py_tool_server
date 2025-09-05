import docker
import io
import sys
from pydantic import BaseModel, Field
from docker.errors import DockerException, ContainerError

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

    # ---------- 生命周期 ----------
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()          # 确认 Docker 可用
        except DockerException as e:
            raise RuntimeError("Docker daemon not reachable") from e

    # ---------- 执行入口 ----------
    async def execute(self, parameters: CodeInterpreterInput) -> dict:
        image_name = "python:3.11-slim"
        # 把用户代码写进容器内文件，避免 -c 单行语法问题
        runner_script = (
            "import sys, traceback\n"
            "code = sys.stdin.read()\n"
            "try:\n"
            "    exec(code, {'__builtins__': {'print': print, 'len': len, 'range': range, "
            "'str': str, 'int': int, 'float': float, 'bool': bool, "
            "'list': list, 'dict': dict, 'set': set, 'tuple': tuple}})\n"
            "except Exception as e:\n"
            "    traceback.print_exc()\n"
        )

        container_config = {
            "image": image_name,
            "command": ["python", "-c", runner_script],
            "network_disabled": True,   # 无网络
            "mem_limit": "256m",        # 内存上限
            "cpu_period": 100_000,
            "cpu_quota": 50_000,        # 0.5 核
            "user": "1001:1001",        # 非 root（镜像需存在 uid 1001）
            "remove": True,             # 退出即删
            "read_only": True,          # 只读根文件系统
            "detach": False,            # 同步执行
            "stdout": True,
            "stderr": True,
        }

        try:
            # 把用户代码作为 stdin 喂给容器
            output_bytes = self.docker_client.containers.run(
                **container_config,
                input=parameters.code.encode(),
            )
            stdout = output_bytes.decode(errors="ignore")
            stderr = ""
            return {"success": True, "data": {"stdout": stdout, "stderr": stderr}}

        except ContainerError as e:
            stdout = (e.stdout or b"").decode(errors="ignore")
            stderr = (e.stderr or b"").decode(errors="ignore")
            return {"success": True, "data": {"stdout": stdout, "stderr": stderr}}

        except Exception as e:
            return {"success": False, "error": f"Sandbox error: {e}"}