"""Configuration for the ReAct Agent."""
from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    """Configuration for the agent."""
    
    # Model settings
    model: str = "qwen3:4b"
    temperature: float = 0.7
    base_url: str = "http://localhost:11434"
    
    # Context settings
    max_history: int = 20
    max_tokens: int = 4096
    
    # Tool settings
    enable_file_tools: bool = True
    enable_shell_tools: bool = True
    enable_web_tools: bool = True
    enable_code_tools: bool = True
    enable_utility_tools: bool = True
    enable_crawl_tools: bool = True
    
    # Safety settings
    confirm_destructive: bool = True
    blocked_commands: list[str] = field(default_factory=lambda: [
        "rm -rf /", "mkfs", "dd if=", ":(){:|:&};:"
    ])
    
    # Output settings
    streaming: bool = True
    verbose: bool = False


# Available Ollama models
AVAILABLE_MODELS = [
    "qwen3:4b",
    "qwen3:1.7b", 
    "qwen3:0.6b",
    "gemma3:4b",
    "gemma3:1b",
    "deepseek-r1:1.5b",
    "ministral-3:14b",
    "ministral-3:8b",
    "ministral-3:3b",
    "gpt-oss:20b",
    "functiongemma:latest",
]
