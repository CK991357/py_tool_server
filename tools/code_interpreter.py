import docker
from pydantic import BaseModel, Field
from docker.errors import DockerException, ContainerError

# --- Pydantic Input Schema ---
class CodeInterpreterInput(BaseModel):
    """Input schema for the Code Interpreter tool."""
    code: str = Field(description="The Python code to be executed in the sandbox.")

# --- Tool Class ---
class CodeInterpreterTool:
    """
    A tool for executing Python code in a secure, isolated Docker sandbox.
    """
    name = "code_interpreter"
    description = (
        "Executes a snippet of Python code in a sandboxed environment and returns the output. "
        "This tool is secure and has no access to the internet or the host filesystem."
    )
    input_schema = CodeInterpreterInput

    def __init__(self):
        """
        Initializes the Docker client.
        Raises an exception if Docker is not available.
        """
        try:
            self.docker_client = docker.from_env()
            # Ping the Docker daemon to ensure it's running
            self.docker_client.ping()
        except DockerException:
            # This provides a clear error if the Docker daemon isn't running on the server
            raise RuntimeError("Docker is not running or misconfigured. Please ensure the Docker daemon is active on the server.")

    async def execute(self, parameters: CodeInterpreterInput) -> dict:
        """
        Executes the provided Python code in a temporary, secure Docker container.
        """
        image_name = "python:3.11-slim"
        
        # Security-focused container configuration
        container_config = {
            "image": image_name,
            "command": ["python", "-c", parameters.code],
            "network_disabled": True,  # Disables all networking
            "mem_limit": "256m",       # Hard memory limit
            "cpu_period": 100000,      # CPU time period
            "cpu_quota": 50000,        # 0.5 CPU core limit
            "user": "1001:1001",       # Run as a non-root user (requires image support or setup)
            "remove": True,            # Automatically remove the container on exit
            "read_only": True,         # Make the container's root filesystem read-only
            "detach": False,           # Run attached to get logs directly
            "stdout": True,
            "stderr": True,
        }

        try:
            # Run the container and capture the output
            output_bytes = self.docker_client.containers.run(**container_config)
            stdout = output_bytes.decode('utf-8', errors='ignore')
            stderr = ""
            
            return {
                "success": True,
                "data": {"stdout": stdout, "stderr": stderr}
            }

        except ContainerError as e:
            # This error is raised when the code inside the container returns a non-zero exit code
            stdout = e.stdout.decode('utf-8', errors='ignore') if e.stdout else ""
            stderr = e.stderr.decode('utf-8', errors='ignore') if e.stderr else ""
            
            return {
                "success": True, # The tool itself ran successfully, even if the code failed
                "data": {"stdout": stdout, "stderr": stderr}
            }
            
        except Exception as e:
            # Handle other exceptions, e.g., image not found, Docker daemon error
            return {
                "success": False,
                "error": f"An unexpected error occurred while running the code interpreter: {str(e)}"
            }