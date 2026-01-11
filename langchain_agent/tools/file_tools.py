"""File operation tools using LangChain @tool decorator."""
import os
import glob
from pathlib import Path
from datetime import datetime
from langchain_core.tools import tool


@tool
def read_file(path: str) -> str:
    """Read the contents of a file.
    
    Args:
        path: Absolute or relative path to the file
    """
    try:
        path = os.path.expanduser(path)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"File contents of '{path}':\n```\n{content}\n```"
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except PermissionError:
        return f"Error: Permission denied reading: {path}"
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file, creating directories if needed.
    
    Args:
        path: Absolute or relative path to the file
        content: Content to write to the file
    """
    try:
        path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to '{path}'"
    except PermissionError:
        return f"Error: Permission denied writing to: {path}"
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def list_directory(path: str = ".") -> str:
    """List contents of a directory.
    
    Args:
        path: Directory path (default: current directory)
    """
    try:
        path = os.path.expanduser(path)
        entries = []
        for entry in sorted(os.listdir(path)):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                entries.append(f"[DIR] {entry}/")
            else:
                size = os.path.getsize(full_path)
                entries.append(f"[FILE] {entry} ({_format_size(size)})")
        
        if not entries:
            return f"Directory '{path}' is empty"
        return f"Contents of '{path}':\n" + "\n".join(entries)
    except FileNotFoundError:
        return f"Error: Directory not found: {path}"
    except PermissionError:
        return f"Error: Permission denied accessing: {path}"
    except Exception as e:
        return f"Error listing directory: {e}"


@tool
def search_files(pattern: str, directory: str = ".") -> str:
    """Search for files matching a glob pattern.
    
    Args:
        pattern: Glob pattern (e.g., "*.py", "**/*.txt")
        directory: Base directory for search
    """
    try:
        directory = os.path.expanduser(directory)
        full_pattern = os.path.join(directory, pattern)
        matches = glob.glob(full_pattern, recursive=True)
        
        if not matches:
            return f"No files matching '{pattern}' found in '{directory}'"
        
        results = [f"Found {len(matches)} file(s) matching '{pattern}':"]
        for match in sorted(matches)[:50]:
            results.append(f"  - {match}")
        
        if len(matches) > 50:
            results.append(f"  ... and {len(matches) - 50} more")
        
        return "\n".join(results)
    except Exception as e:
        return f"Error searching files: {e}"


@tool
def file_info(path: str) -> str:
    """Get detailed information about a file.
    
    Args:
        path: Path to the file
    """
    try:
        path = os.path.expanduser(path)
        stat = os.stat(path)
        p = Path(path)
        
        info = [
            f"File Information for '{path}':",
            f"  Type: {'Directory' if p.is_dir() else 'File'}",
            f"  Size: {_format_size(stat.st_size)}",
            f"  Permissions: {oct(stat.st_mode)[-3:]}",
            f"  Modified: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Created: {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        
        if p.is_file():
            info.append(f"  Extension: {p.suffix or 'None'}")
            
        return "\n".join(info)
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error getting file info: {e}"


def _format_size(size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


# Export all tools
@tool
def replace_in_file(path: str, old_text: str, new_text: str) -> str:
    """Replace text in a file.
    
    Args:
        path: Path to the file
        old_text: The exact text to replace
        new_text: The new text to replace it with
    """
    try:
        path = os.path.expanduser(path)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if old_text not in content:
            return f"Error: Text not found in file: {old_text[:50]}..."
            
        new_content = content.replace(old_text, new_text)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return f"Successfully replaced {content.count(old_text)} occurrence(s) in '{path}'"
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error replacing text: {e}"


@tool
def insert_in_file(path: str, content: str, line: int = -1) -> str:
    """Insert content at a specific line number.
    
    Args:
        path: Path to the file
        content: The text to insert
        line: Line number to insert at (1-based), or -1 to append to end
    """
    try:
        path = os.path.expanduser(path)
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if line == -1:
            lines.append(content + "\n")
            inserted_at = "end"
        else:
            if line < 1 or line > len(lines) + 1:
                return f"Error: Line {line} out of range (1-{len(lines)+1})"
            lines.insert(line - 1, content + "\n")
            inserted_at = f"line {line}"
            
        new_file_content = "".join(lines)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_file_content)
            
        return f"Successfully inserted content at {inserted_at} of '{path}'"
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error inserting text: {e}"


# Export all tools
FILE_TOOLS = [read_file, write_file, list_directory, search_files, file_info, replace_in_file, insert_in_file]
