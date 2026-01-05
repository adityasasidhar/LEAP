"""Shell command execution tools using LangChain @tool decorator."""
import subprocess
import os
import platform
import shlex
from langchain_core.tools import tool


# Commands that are blocked for safety
BLOCKED_PATTERNS = [
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    "dd if=",
    ":(){:|:&};:",
    "chmod -R 777 /",
    "> /dev/sda",
    "mv /* ",
    "wget | sh",
    "curl | sh",
]


@tool
def run_command(command: str, timeout: int = 30) -> str:
    """Execute a shell command and return the output.
    
    Args:
        command: The shell command to execute
        timeout: Maximum execution time in seconds (default: 30)
    """
    # Safety check
    for pattern in BLOCKED_PATTERNS:
        if pattern in command:
            return f"Error: Command blocked for safety reasons. Pattern '{pattern}' is not allowed."
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),
        )
        
        output_parts = []
        if result.stdout:
            output_parts.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output_parts.append(f"STDERR:\n{result.stderr}")
        
        output = "\n".join(output_parts) if output_parts else "(no output)"
        
        status = "✓ Success" if result.returncode == 0 else f"✗ Failed (exit code: {result.returncode})"
        
        return f"Command: `{command}`\nStatus: {status}\n\n{output}"
        
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error executing command: {e}"


@tool
def get_environment() -> str:
    """Get system environment information including OS, Python version, shell, and user."""
    info = [
        "System Environment:",
        f"  OS: {platform.system()} {platform.release()}",
        f"  Platform: {platform.platform()}",
        f"  Architecture: {platform.machine()}",
        f"  Python: {platform.python_version()}",
        f"  Shell: {os.environ.get('SHELL', 'unknown')}",
        f"  User: {os.environ.get('USER', 'unknown')}",
        f"  Home: {os.path.expanduser('~')}",
        f"  CWD: {os.getcwd()}",
    ]
    return "\n".join(info)


@tool
def get_process_list() -> str:
    """Get a list of running processes sorted by CPU usage."""
    try:
        result = subprocess.run(
            "ps aux --sort=-%cpu | head -15",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return f"Top Processes:\n{result.stdout}"
    except Exception as e:
        return f"Error getting process list: {e}"


@tool
def check_command_exists(command: str) -> str:
    """Check if a command exists in PATH.
    
    Args:
        command: Command name to check
    """
    try:
        result = subprocess.run(
            f"which {shlex.quote(command)}",
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return f"Command '{command}' exists at: {result.stdout.strip()}"
        else:
            return f"Command '{command}' not found in PATH"
    except Exception as e:
        return f"Error checking command: {e}"


# Export all tools
SHELL_TOOLS = [run_command, get_environment, get_process_list, check_command_exists]
