"""Main ReAct Agent using LangChain with LangChain-Ollama for inference."""
from typing import Optional, Generator
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from .config import AgentConfig
from .llm import create_llm
from .prompts import SYSTEM_PROMPT
from .tools import ALL_TOOLS


class ReactAgent:
    """Baseline ReAct Agent - A general-purpose AI assistant powered by Ollama."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the agent with configuration."""
        self.config = config or AgentConfig()
        self.llm = create_llm(self.config)
        self.tools = self._get_enabled_tools()
        self.history: list = []
        
        # Create the ReAct agent with tools bound to LLM
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=SYSTEM_PROMPT,
        )
        
    def _get_enabled_tools(self) -> list:
        """Get tools based on configuration."""
        from .tools import FILE_TOOLS, SHELL_TOOLS, WEB_TOOLS, CODE_TOOLS, UTILITY_TOOLS, CRAWL_TOOLS
        
        tools = []
        if self.config.enable_file_tools:
            tools.extend(FILE_TOOLS)
        if self.config.enable_shell_tools:
            tools.extend(SHELL_TOOLS)
        if self.config.enable_web_tools:
            tools.extend(WEB_TOOLS)
        if self.config.enable_code_tools:
            tools.extend(CODE_TOOLS)
        if self.config.enable_utility_tools:
            tools.extend(UTILITY_TOOLS)
        if self.config.enable_crawl_tools:
            tools.extend(CRAWL_TOOLS)
        return tools
    
    def run(self, user_input: str) -> str:
        """Run the agent on a user input.
        
        Args:
            user_input: The user's message/question
            
        Returns:
            The agent's final response
        """
        self.history.append(HumanMessage(content=user_input))
        
        result = self.agent.invoke({
            "messages": self.history,
        })
        
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            response = last_message.content if hasattr(last_message, 'content') else str(last_message)
            self.history = messages
            return response
        
        return "No response generated."
    
    def run_streaming(self, user_input: str) -> Generator[str, None, None]:
        """Run the agent with streaming output."""
        self.history.append(HumanMessage(content=user_input))
        
        last_content = ""
        final_messages = self.history.copy()
        
        for event in self.agent.stream({"messages": self.history}):
            if "agent" in event:
                messages = event["agent"].get("messages", [])
                for msg in messages:
                    if hasattr(msg, 'content') and msg.content:
                        new_content = msg.content[len(last_content):]
                        if new_content:
                            yield new_content
                            last_content = msg.content
                final_messages = event["agent"].get("messages", final_messages)
            
            if "tools" in event:
                messages = event["tools"].get("messages", [])
                for msg in messages:
                    if hasattr(msg, 'content'):
                        content = str(msg.content)
                        yield f"\n\n[TOOL] Tool result:\n```\n{content[:500]}{'...' if len(content) > 500 else ''}\n```\n\n"
                        last_content = ""
        
        self.history = final_messages
    
    def clear_history(self):
        """Clear conversation history."""
        self.history = []
    
    def set_model(self, model: str):
        """Change the Ollama model."""
        self.config.model = model
        self.llm = create_llm(self.config)
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=SYSTEM_PROMPT,
        )
    
    def get_available_tools(self) -> list[str]:
        """Get list of available tool names."""
        return [t.name for t in self.tools]
