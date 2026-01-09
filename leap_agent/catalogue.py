"""Lightweight Tool Catalogue - The core LEAP innovation.

Traditional protocols: 15,000+ tokens of verbose JSON schemas
LEAP: 50-100 tokens of minimal name + description pairs

The key insight: Modern LLMs already know how to use common tools
from training data. They don't need verbose schemas in every request.
"""

# Minimal tool catalogue - just name + brief description + maybe a hint for complex tools
TOOL_CATALOGUE = {
    # File operations
    "read_file": "Read file contents",
    "write_file": "Write content to file (overwrite)",
    "replace_in_file": "Replace text in file",
    "insert_in_file": "Insert text/lines in file",
    "list_directory": "List directory contents",
    "search_files": "Find files by pattern",
    "file_info": "Get file metadata",
    
    # Shell operations
    "run_shell_command": "Execute shell command",
    "get_shell_env": "Get system environment info",
    
    # Web/Search operations
    "web_search": "Search the web",
    "news_search": "Search recent news",
    "fetch_url": "Fetch webpage content",
    "crawl_webpage": "Crawl and extract from URL",
    
    # Code operations
    "analyze_code": "Analyze Python file structure",
    "grep_code": "Search pattern in code files",
    "find_definition": "Find definition of symbol",
    "read_definition": "Read source of function/class",
    "replace_definition": "Replace source of function/class",
    
    # Utility operations
    "calculate": "Evaluate math expression",
    "get_current_time": "Get current date/time",
    "parse_json": "Parse/format JSON",
}


def get_catalogue_prompt() -> str:
    """Format catalogue as minimal prompt text."""
    lines = ["Available tools:"]
    for name, desc in TOOL_CATALOGUE.items():
        lines.append(f"  {name}: {desc}")
    return "\n".join(lines)


def get_catalogue_tokens() -> int:
    """Estimate token count of catalogue."""
    text = get_catalogue_prompt()
    # Rough estimate: ~4 chars per token
    return len(text) // 4


# Tool execution specs - used by subagent, NOT sent to main agent
TOOL_SPECS = {
    "read_file": {
        "function": "tools.file_tools.read_file",
        "params": ["path"],
        "filterable_fields": ["content", "size", "error"],
    },
    "write_file": {
        "function": "tools.file_tools.write_file",
        "params": ["path", "content"],
        "filterable_fields": ["success", "bytes_written", "error"],
    },
    "replace_in_file": {
        "function": "tools.file_tools.replace_in_file",
        "params": ["path", "old_text", "new_text"],
        "filterable_fields": ["success", "replacements", "error"],
    },
    "insert_in_file": {
        "function": "tools.file_tools.insert_in_file",
        "params": ["path", "content", "line"],
        "filterable_fields": ["success", "inserted_at", "error"],
    },
    "list_directory": {
        "function": "tools.file_tools.list_directory",
        "params": ["path"],
        "filterable_fields": ["files", "directories", "count"],
    },
    "search_files": {
        "function": "tools.file_tools.search_files",
        "params": ["pattern", "directory"],
        "filterable_fields": ["matches", "count"],
    },
    "file_info": {
        "function": "tools.file_tools.file_info",
        "params": ["path"],
        "filterable_fields": ["size", "modified", "type", "permissions"],
    },
    "run_shell_command": {
        "function": "tools.shell_tools.run_command",
        "params": ["command"],
        "filterable_fields": ["stdout", "stderr", "exit_code", "success"],
    },
    "get_shell_env": {
        "function": "tools.shell_tools.get_environment",
        "params": [],
        "filterable_fields": ["os", "python", "user", "cwd"],
    },
    "web_search": {
        "function": "tools.web_tools.web_search",
        "params": ["query", "num_results"],
        "filterable_fields": ["results", "titles", "urls", "snippets"],
    },
    "news_search": {
        "function": "tools.web_tools.news_search",
        "params": ["query", "num_results"],
        "filterable_fields": ["articles", "titles", "sources", "dates"],
    },
    "fetch_url": {
        "function": "tools.web_tools.fetch_url",
        "params": ["url"],
        "filterable_fields": ["content", "title", "length"],
    },
    "crawl_webpage": {
        "function": "tools.web_tools.crawl_webpage",
        "params": ["url"],
        "filterable_fields": ["content", "title", "links", "images"],
    },
    "analyze_code": {
        "function": "tools.code_tools.analyze_code",
        "params": ["path"],
        "filterable_fields": ["classes", "functions", "imports", "lines"],
    },
    "grep_code": {
        "function": "tools.code_tools.grep_code",
        "params": ["pattern", "directory"],
        "filterable_fields": ["matches", "files", "count"],
    },
    "find_definition": {
        "function": "tools.code_tools.find_definition",
        "params": ["symbol", "directory"],
        "filterable_fields": ["definitions", "count"],
    },
    "read_definition": {
        "function": "tools.code_tools.read_definition",
        "params": ["path", "name"],
        "filterable_fields": ["content", "name", "lines"],
    },
    "replace_definition": {
        "function": "tools.code_tools.replace_definition",
        "params": ["path", "name", "new_content"],
        "filterable_fields": ["success", "name", "old_lines", "new_lines"],
    },
    "calculate": {
        "function": "tools.utility_tools.calculate",
        "params": ["expression"],
        "filterable_fields": ["result"],
    },
    "get_current_time": {
        "function": "tools.utility_tools.get_datetime",
        "params": [],
        "filterable_fields": ["datetime", "timestamp", "timezone"],
    },
    "parse_json": {
        "function": "tools.utility_tools.json_parse",
        "params": ["text"],
        "filterable_fields": ["parsed", "valid"],
    },
}


if __name__ == "__main__":
    print("LEAP Tool Catalogue")
    print("=" * 50)
    print(get_catalogue_prompt())
    print(f"\nEstimated tokens: ~{get_catalogue_tokens()}")
    print(f"Traditional MCP would be: ~15,000+ tokens")
    print(f"Token reduction: ~{15000 // get_catalogue_tokens()}x")
