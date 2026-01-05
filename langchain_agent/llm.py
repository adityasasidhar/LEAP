"""LLM wrapper for Ollama integration via LangChain."""
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from .config import AgentConfig


def create_llm(config: AgentConfig) -> ChatOllama:
    """Create a ChatOllama instance with the given configuration."""
    return ChatOllama(
        model=config.model,
        temperature=config.temperature,
        base_url=config.base_url,
        num_predict=config.max_tokens,
    )


def format_messages(history: list[dict]) -> list:
    """Convert conversation history to LangChain message format."""
    messages = []
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        
        if role == "system":
            messages.append(SystemMessage(content=content))
        elif role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    
    return messages
