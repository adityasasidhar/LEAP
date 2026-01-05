"""Code analysis tools for LEAP Agent."""
import ast
import os
import re


def analyze_code(path: str) -> dict:
    """Analyze Python file structure."""
    try:
        path = os.path.expanduser(path)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        classes = []
        functions = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                classes.append({"name": node.name, "methods": methods, "line": node.lineno})
            elif isinstance(node, ast.FunctionDef) and not isinstance(node, ast.AsyncFunctionDef):
                if not any(node.lineno > c["line"] for c in classes if "methods" in c):
                    functions.append({"name": node.name, "line": node.lineno})
            elif isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        return {
            "path": path,
            "classes": classes[:20],
            "functions": functions[:30],
            "imports": imports[:30],
            "lines": len(content.splitlines()),
        }
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}", "path": path}
    except Exception as e:
        return {"error": str(e), "path": path}

    except Exception as e:
        return {"error": str(e), "path": path}


def find_definition(symbol: str, directory: str = ".") -> dict:
    """Find where a symbol is defined.
    
    Args:
        symbol: The name of the symbol to find
        directory: Directory to search in
    """
    try:
        directory = os.path.expanduser(directory)
        results = []
        
        patterns = [
            rf'^(?:def|class)\s+{re.escape(symbol)}\s*[\(:]',
            rf'^{re.escape(symbol)}\s*=',
            rf'^\s+{re.escape(symbol)}\s*=',
        ]
        
        extensions = ['.py', '.js', '.ts', '.jsx', '.tsx']
        
        for root, _, files in os.walk(directory):
            if '.git' in root or '__pycache__' in root or 'node_modules' in root:
                continue
                
            for fname in files:
                if not any(fname.endswith(ext) for ext in extensions):
                    continue
                    
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f, 1):
                            for pattern in patterns:
                                if re.match(pattern, line):
                                    results.append({
                                        "file": fpath,
                                        "line": i,
                                        "content": line.strip()
                                    })
                                    break
                except:
                    continue
        
        return {
            "symbol": symbol,
            "directory": directory,
            "definitions": results,
            "count": len(results),
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def grep_code(pattern: str, directory: str = ".") -> dict:
    """Search for pattern in code files."""
    try:
        directory = os.path.expanduser(directory)
        matches = []
        
        extensions = ['.py', '.js', '.ts', '.java', '.go', '.rs', '.c', '.cpp', '.h']
        
        for root, _, files in os.walk(directory):
            if '.git' in root or '__pycache__' in root or 'node_modules' in root:
                continue
                
            for fname in files:
                if not any(fname.endswith(ext) for ext in extensions):
                    continue
                    
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                matches.append({
                                    "file": fpath,
                                    "line": i,
                                    "content": line.strip()[:100],
                                })
                                if len(matches) >= 50:
                                    break
                except:
                    continue
                    
                if len(matches) >= 50:
                    break
            if len(matches) >= 50:
                break
        
        return {
            "pattern": pattern,
            "directory": directory,
            "matches": matches,
            "count": len(matches),
        }
    except Exception as e:
        return {"error": str(e), "pattern": pattern}


def read_definition(path: str, name: str) -> dict:
    """Read source code of a function or class."""
    try:
        path = os.path.expanduser(path)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        target = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == name:
                    target = node
                    break
        
        if not target:
            return {"error": f"Definition '{name}' not found", "path": path}
            
        lines = content.splitlines()
        start = target.lineno - 1
        end = target.end_lineno
        
        return {
            "name": name,
            "type": type(target).__name__,
            "content": "\n".join(lines[start:end]),
            "path": path,
            "lines": end - start
        }
    except Exception as e:
        return {"error": str(e), "path": path}


def replace_definition(path: str, name: str, new_content: str) -> dict:
    """Replace definition of a function or class."""
    try:
        path = os.path.expanduser(path)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        target = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == name:
                    target = node
                    break
        
        if not target:
            return {"error": f"Definition '{name}' not found", "path": path}
            
        lines = content.splitlines()
        start = target.lineno - 1
        end = target.end_lineno
        
        # Indentation handling
        original_indent = len(lines[start]) - len(lines[start].lstrip())
        new_lines = new_content.splitlines()
        if new_lines and (len(new_lines[0]) - len(new_lines[0].lstrip()) == 0) and original_indent > 0:
             indent_str = " " * original_indent
             new_lines = [indent_str + line if line.strip() else line for line in new_lines]
             new_content = "\n".join(new_lines)
             
        new_file_lines = lines[:start] + new_content.splitlines() + lines[end:]
        new_file_content = "\n".join(new_file_lines)
        
        # Verify syntax
        try:
            ast.parse(new_file_content)
        except SyntaxError as e:
           return {"error": f"Syntax error in new content: {e}", "path": path}
           
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_file_content)
            
        return {
            "success": True,
            "name": name,
            "path": path,
            "old_lines": end - start,
            "new_lines": len(new_content.splitlines())
        }
    except Exception as e:
        return {"error": str(e), "path": path}
