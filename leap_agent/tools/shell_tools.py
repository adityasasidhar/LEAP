"""Shell tools for LEAP Agent."""
import subprocess
import os
import platform


def run_command(command: str, timeout: int = 30) -> dict:
    """Execute shell command."""
    # Safety check
    dangerous = ["rm -rf /", "mkfs", "dd if=", ":(){:|:&};:"]
    if any(d in command for d in dangerous):
        return {"error": "Command blocked for safety", "command": command}
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd()
        )
        
        return {
            "command": command,
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:1000],
            "exit_code": result.returncode,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out", "command": command, "timeout": timeout}
    except Exception as e:
        return {"error": str(e), "command": command}


def get_environment() -> dict:
    """Get system environment info."""
    return {
        "os": platform.system(),
        "os_version": platform.release(),
        "python": platform.python_version(),
        "user": os.getenv("USER", "unknown"),
        "home": os.path.expanduser("~"),
        "cwd": os.getcwd(),
        "shell": os.getenv("SHELL", "unknown"),
    }
