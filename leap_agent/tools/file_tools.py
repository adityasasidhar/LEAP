"""File system tools for LEAP Agent.

These are plain Python functions (not LangChain tools).
The subagent executes them directly.
"""
import os
import glob
from pathlib import Path


def read_file(path: str) -> dict:
    """Read file contents."""
    try:
        path = os.path.expanduser(path)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return {
            "content": content[:10000],  # Limit raw content
            "size": len(content),
            "path": path,
            "truncated": len(content) > 10000,
        }
    except Exception as e:
        return {"error": str(e), "path": path}


def write_file(path: str, content: str) -> dict:
    """Write content to file."""
    try:
        path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "success": True,
            "path": path,
            "bytes_written": len(content),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "path": path}


def list_directory(path: str = ".") -> dict:
    """List directory contents."""
    try:
        path = os.path.expanduser(path)
        entries = os.listdir(path)
        
        files = []
        directories = []
        
        for entry in entries[:100]:  # Limit entries
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                directories.append(entry)
            else:
                size = os.path.getsize(full_path)
                files.append({"name": entry, "size": size})
        
        return {
            "path": path,
            "files": files,
            "directories": directories,
            "file_count": len(files),
            "dir_count": len(directories),
        }
    except Exception as e:
        return {"error": str(e), "path": path}


def search_files(pattern: str, directory: str = ".") -> dict:
    """Search for files matching pattern."""
    try:
        directory = os.path.expanduser(directory)
        search_pattern = os.path.join(directory, "**", pattern)
        matches = glob.glob(search_pattern, recursive=True)[:50]
        
        return {
            "pattern": pattern,
            "directory": directory,
            "matches": matches,
            "count": len(matches),
        }
    except Exception as e:
        return {"error": str(e), "pattern": pattern}


def file_info(path: str) -> dict:
    """Get file metadata."""
    try:
        path = os.path.expanduser(path)
        stat = os.stat(path)
        
        return {
            "path": path,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "is_file": os.path.isfile(path),
            "is_dir": os.path.isdir(path),
            "readable": os.access(path, os.R_OK),
            "writable": os.access(path, os.W_OK),
        }
    except Exception as e:
        return {"error": str(e), "path": path}


def replace_in_file(path: str, old_text: str, new_text: str) -> dict:
    """Replace text in a file."""
    try:
        path = os.path.expanduser(path)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if old_text not in content:
            return {"error": f"Text not found in file: {old_text[:50]}...", "path": path}
            
        new_content = content.replace(old_text, new_text)
       
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
           
        return {
            "success": True,
            "path": path,
            "replacements": content.count(old_text),
            "new_size": len(new_content)
        }
    except Exception as e:
        return {"error": str(e), "path": path}


def insert_in_file(path: str, content: str, line: int = -1) -> dict:
    """Insert content at line number (1-based) or append if -1."""
    try:
        path = os.path.expanduser(path)
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if line == -1:
            lines.append(content + "\n")
        else:
            if line < 1 or line > len(lines) + 1:
                return {"error": f"Line {line} out of range (1-{len(lines)+1})"}
            lines.insert(line - 1, content + "\n")
            
        new_content = "".join(lines)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return {
            "success": True,
            "path": path,
            "new_lines": len(lines),
            "inserted_at": line if line != -1 else "end"
        }
    except Exception as e:
        return {"error": str(e), "path": path}
