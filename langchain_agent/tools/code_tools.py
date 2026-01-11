"""Code analysis tools using LangChain @tool decorator."""
import os
import re
import ast
from langchain_core.tools import tool


@tool
def analyze_code(path: str) -> str:
    """Analyze the structure of a Python file (classes, functions, imports).
    
    Args:
        path: Path to the Python file
    """
    try:
        path = os.path.expanduser(path)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return f"Syntax error in file: {e}"
        
        analysis = [f"Code Analysis: {path}\n"]
        
        # Imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        if imports:
            analysis.append("**Imports:**")
            for imp in imports[:20]:
                analysis.append(f"  - {imp}")
            if len(imports) > 20:
                analysis.append(f"  ... and {len(imports) - 20} more")
            analysis.append("")
        
        # Classes
        classes = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                classes.append((node.name, methods, node.lineno))
        
        if classes:
            analysis.append("**Classes:**")
            for name, methods, line in classes:
                analysis.append(f"  - {name} (line {line})")
                for method in methods[:5]:
                    analysis.append(f"      - {method}()")
                if len(methods) > 5:
                    analysis.append(f"      ... and {len(methods) - 5} more methods")
            analysis.append("")
        
        # Functions
        functions = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                args = [arg.arg for arg in node.args.args]
                functions.append((node.name, args, node.lineno))
        
        if functions:
            analysis.append("**Functions:**")
            for name, args, line in functions:
                args_str = ", ".join(args) if args else ""
                analysis.append(f"  - {name}({args_str}) - line {line}")
            analysis.append("")
        
        lines = content.count('\n') + 1
        analysis.append(f"**Stats:** {lines} lines, {len(classes)} classes, {len(functions)} functions")
        
        return "\n".join(analysis)
        
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error analyzing code: {e}"


@tool
def find_definition(symbol: str, directory: str = ".") -> str:
    """Find where a symbol (function, class, variable) is defined.
    
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
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', '.venv']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            for i, line in enumerate(f, 1):
                                for pattern in patterns:
                                    if re.match(pattern, line):
                                        results.append(f"{filepath}:{i}: {line.strip()}")
                                        break
                    except:
                        continue
        
        if not results:
            return f"No definition found for '{symbol}' in {directory}"
        
        output = [f"Definitions of '{symbol}':\n"]
        for result in results[:20]:
            output.append(f"  {result}")
        if len(results) > 20:
            output.append(f"\n  ... and {len(results) - 20} more")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Error finding definition: {e}"


@tool
def grep_code(pattern: str, directory: str = ".", file_pattern: str = "*.py") -> str:
    """Search for a regex pattern in code files.
    
    Args:
        pattern: Regex pattern to search for
        directory: Directory to search in
        file_pattern: Glob pattern for files to search (default: *.py)
    """
    try:
        directory = os.path.expanduser(directory)
        results = []
        regex = re.compile(pattern, re.IGNORECASE)
        
        extensions = {
            "*.py": [".py"],
            "*.js": [".js", ".jsx"],
            "*.ts": [".ts", ".tsx"],
            "*": [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".c", ".cpp", ".h"],
        }
        
        exts = extensions.get(file_pattern, [file_pattern.replace("*", "")])
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', '.venv']]
            
            for file in files:
                if any(file.endswith(ext) for ext in exts):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            for i, line in enumerate(f, 1):
                                if regex.search(line):
                                    results.append((filepath, i, line.strip()))
                    except:
                        continue
        
        if not results:
            return f"No matches found for '{pattern}' in {directory}"
        
        output = [f"Found {len(results)} matches for '{pattern}':\n"]
        for filepath, lineno, line in results[:30]:
            output.append(f"  {filepath}:{lineno}: {line[:80]}{'...' if len(line) > 80 else ''}")
        
        if len(results) > 30:
            output.append(f"\n  ... and {len(results) - 30} more matches")
        
        return "\n".join(output)
        
    except re.error as e:
        return f"Invalid regex pattern: {e}"
    except Exception as e:
        return f"Error searching code: {e}"


@tool
def read_definition(path: str, name: str) -> str:
    """Read the source code of a specific function or class.
    
    Args:
        path: Path to the file
        name: Name of the function or class to read
    """
    try:
        path = os.path.expanduser(path)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return f"Syntax error in file: {e}"
            
        target = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == name:
                    target = node
                    break
                    
        if not target:
            return f"Error: Definition '{name}' not found in {path}"
            
        lines = content.splitlines()
        # ast.get_source_segment is available in Python 3.8+
        start = target.lineno - 1
        end = target.end_lineno
        
        definition_code = "\n".join(lines[start:end])
        return f"Definition of '{name}' in '{path}':\n```python\n{definition_code}\n```"
        
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error reading definition: {e}"


@tool
def replace_definition(path: str, name: str, new_content: str) -> str:
    """Replace the definition of a function or class with new content.
    
    Args:
        path: Path to the file
        name: Name of the function or class to replace
        new_content: The new source code for the definition
    """
    try:
        path = os.path.expanduser(path)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return f"Syntax error in file: {e}"
            
        target = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == name:
                    target = node
                    break
                    
        if not target:
            return f"Error: Definition '{name}' not found in {path}"
            
        lines = content.splitlines()
        start = target.lineno - 1
        end = target.end_lineno
        
        # Keep indentation of the original definition if new_content isn't indented
        original_indent = len(lines[start]) - len(lines[start].lstrip())
        new_lines = new_content.splitlines()
        if new_lines and (len(new_lines[0]) - len(new_lines[0].lstrip()) == 0) and original_indent > 0:
             # Add indentation to new content
             indent_str = " " * original_indent
             new_lines = [indent_str + line if line.strip() else line for line in new_lines]
             new_content = "\n".join(new_lines)

        # Reconstruct file content
        new_file_lines = lines[:start] + new_content.splitlines() + lines[end:]
        new_file_content = "\n".join(new_file_lines)
        
        # Verify syntax of new content
        try:
            ast.parse(new_file_content)
        except SyntaxError as e:
           return f"Error: New content would cause syntax error: {e}"
           
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_file_content)
            
        return f"Successfully replaced definition of '{name}' in '{path}'"
        
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error replacing definition: {e}"


# Export all tools
CODE_TOOLS = [analyze_code, find_definition, grep_code, read_definition, replace_definition]
