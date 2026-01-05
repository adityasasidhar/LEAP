"""Tool registry for ReAct Agent - exports LangChain tool instances."""
from .file_tools import FILE_TOOLS
from .shell_tools import SHELL_TOOLS
from .web_tools import WEB_TOOLS
from .code_tools import CODE_TOOLS
from .utility_tools import UTILITY_TOOLS
from .crawl_tools import CRAWL_TOOLS

# All tools as a flat list for LangChain agent
ALL_TOOLS = FILE_TOOLS + SHELL_TOOLS + WEB_TOOLS + CODE_TOOLS + UTILITY_TOOLS + CRAWL_TOOLS

__all__ = [
    "ALL_TOOLS",
    "FILE_TOOLS",
    "SHELL_TOOLS",
    "WEB_TOOLS",
    "CODE_TOOLS",
    "UTILITY_TOOLS",
    "CRAWL_TOOLS",
]
