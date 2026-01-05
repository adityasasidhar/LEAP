"""General-purpose utility tools using LangChain @tool decorator."""
import math
import json
import uuid
import hashlib
import base64
import ast
from datetime import datetime
from langchain_core.tools import tool


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely. Supports sqrt, sin, cos, log, pi, e, etc.
    
    Args:
        expression: Mathematical expression to evaluate
    """
    safe_dict = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'pow': pow,
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'pi': math.pi,
        'e': math.e,
        'floor': math.floor,
        'ceil': math.ceil,
    }
    
    try:
        if any(c in expression for c in ['import', 'exec', 'eval', 'open', '__']):
            return "Error: Expression contains forbidden keywords"
        
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        return f"Result: {expression} = {result}"
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error evaluating expression: {e}"


@tool
def get_datetime(format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Get the current date and time.
    
    Args:
        format: DateTime format string (default: YYYY-MM-DD HH:MM:SS)
    """
    now = datetime.now()
    try:
        formatted = now.strftime(format)
        return f"""Current Date/Time:
  Formatted: {formatted}
  ISO: {now.isoformat()}
  Unix Timestamp: {int(now.timestamp())}
  Timezone: {now.astimezone().tzname()}"""
    except Exception as e:
        return f"Error formatting datetime: {e}"


@tool
def generate_uuid() -> str:
    """Generate a unique UUID4 identifier."""
    new_uuid = str(uuid.uuid4())
    return f"Generated UUID: {new_uuid}"


@tool
def json_parse(text: str) -> str:
    """Parse and pretty-print a JSON string.
    
    Args:
        text: JSON string to parse
    """
    try:
        parsed = json.loads(text)
        formatted = json.dumps(parsed, indent=2)
        return f"Parsed JSON:\n```json\n{formatted}\n```"
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"


@tool
def json_create(data: str) -> str:
    """Create JSON from a Python dictionary-like string.
    
    Args:
        data: Python dictionary-like string
    """
    try:
        parsed = ast.literal_eval(data)
        json_str = json.dumps(parsed, indent=2)
        return f"Created JSON:\n```json\n{json_str}\n```"
    except Exception as e:
        return f"Error creating JSON: {e}"


@tool
def hash_text(text: str, algorithm: str = "sha256") -> str:
    """Calculate hash of text.
    
    Args:
        text: Text to hash
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)
    """
    algorithms = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512,
    }
    
    if algorithm.lower() not in algorithms:
        return f"Error: Unknown algorithm '{algorithm}'. Use: {', '.join(algorithms.keys())}"
    
    hasher = algorithms[algorithm.lower()]()
    hasher.update(text.encode('utf-8'))
    return f"{algorithm.upper()} hash: {hasher.hexdigest()}"


@tool
def base64_encode(text: str) -> str:
    """Encode text to base64.
    
    Args:
        text: Text to encode
    """
    encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    return f"Base64 encoded:\n{encoded}"


@tool
def base64_decode(text: str) -> str:
    """Decode base64 to text.
    
    Args:
        text: Base64 string to decode
    """
    try:
        decoded = base64.b64decode(text.encode('utf-8')).decode('utf-8')
        return f"Decoded text:\n{decoded}"
    except Exception as e:
        return f"Error decoding base64: {e}"


# Export all tools
UTILITY_TOOLS = [calculate, get_datetime, generate_uuid, json_parse, json_create, hash_text, base64_encode, base64_decode]
