"""LEAP Agent Configuration - optimized for 4GB VRAM."""
from dataclasses import dataclass, field


@dataclass
class LEAPConfig:
    """Configuration for LEAP Agent."""
    
    # Model settings - Sequential orchestration
    # Using smaller models for faster response on 4GB VRAM
    main_model: str = "qwen3:1.7b"    # 1.4GB - faster reasoning/planning
    sub_model: str = "gemma3:1b"      # 815MB - execution/filtering
    
    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    
    # Temperature settings
    main_temperature: float = 0.3    # Lower for consistent tool selection
    sub_temperature: float = 0.0     # Zero for deterministic filtering
    
    # Context limits (LEAP uses minimal context)
    max_catalogue_tokens: int = 100   # Tiny catalogue
    max_response_tokens: int = 500    # Filtered responses only
    
    # Sequential orchestration
    enable_sequential: bool = True    # Swap models to fit 4GB
    warmup_models: bool = True        # Pre-load models on startup
    
    # Response filtering
    enable_filtering: bool = True     # Subagent filters responses
    max_raw_response: int = 5000      # Max raw tool output before filtering
    
    # Monitoring
    verbose: bool = False
    track_memory: bool = True
    track_latency: bool = True


# Recommended model pairs for different VRAM sizes
MODEL_PAIRS = {
    "4gb": {
        "main": "qwen3:4b",       # 2.5GB
        "sub": "qwen3:1.7b",      # 1.4GB
        "description": "Balanced performance for 4GB VRAM"
    },
    "4gb_fast": {
        "main": "qwen3:4b",       # 2.5GB
        "sub": "functiongemma",   # 300MB - specialized tool calling
        "description": "Faster subagent, specialized for tool execution"
    },
    "4gb_light": {
        "main": "qwen3:1.7b",     # 1.4GB
        "sub": "gemma3:1b",       # 815MB
        "description": "Ultra-lightweight, fastest loading"
    },
    "8gb": {
        "main": "gemma3:4b",      # 3.3GB
        "sub": "qwen3:1.7b",      # 1.4GB
        "description": "Higher quality for 8GB VRAM"
    },
}
