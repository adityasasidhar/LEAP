"""Utility tools for LEAP Agent."""
import json
import math
from datetime import datetime


def calculate(expression: str) -> dict:
    """Evaluate mathematical expression safely."""
    try:
        # Safe math context
        safe_dict = {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow, "len": len,
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
            "tan": math.tan, "log": math.log, "log10": math.log10,
            "exp": math.exp, "pi": math.pi, "e": math.e,
            "floor": math.floor, "ceil": math.ceil,
        }
        
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        
        return {
            "expression": expression,
            "result": result,
            "type": type(result).__name__,
        }
    except Exception as e:
        return {"error": str(e), "expression": expression}


def get_datetime(format: str = "%Y-%m-%d %H:%M:%S") -> dict:
    """Get current date and time."""
    now = datetime.now()
    
    return {
        "datetime": now.strftime(format),
        "timestamp": now.timestamp(),
        "iso": now.isoformat(),
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "hour": now.hour,
        "minute": now.minute,
    }


def json_parse(text: str) -> dict:
    """Parse JSON text."""
    try:
        parsed = json.loads(text)
        return {
            "valid": True,
            "parsed": parsed,
            "type": type(parsed).__name__,
        }
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "error": str(e),
        }
