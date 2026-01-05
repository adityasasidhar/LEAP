#!/usr/bin/env python3
"""Advanced benchmark: Coding tasks with token usage tracking."""
import json
import time
import subprocess
import re
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CodingBenchmarkResult:
    """Result for coding benchmark."""
    task_id: str
    task: str
    agent: str
    time_seconds: float
    success: bool
    output_length: int  # Approximate token proxy
    output_preview: str = ""


# Complex coding/building tasks
CODING_TASKS = [
    # Code Writing
    ("CODE1", "Write a Python function that finds the nth Fibonacci number using recursion with memoization"),
    ("CODE2", "Write a Python class called Rectangle with methods for area, perimeter, and a __str__ method"),
    ("CODE3", "Write a bash script that finds all Python files larger than 1KB in the current directory"),
    
    # Code Analysis & Debugging
    ("DEBUG1", "Find and explain any bugs in this code: def factorial(n): return n * factorial(n-1)"),
    ("DEBUG2", "Analyze the leap_agent/orchestrator.py and list all public methods"),
    
    # Building & Creating
    ("BUILD1", "Create a simple HTML page with a calculator that can add two numbers using JavaScript"),
    ("BUILD2", "Write a Python script that reads a JSON file and prints its keys"),
    
    # Multi-step Tasks
    ("MULTI1", "List all Python files in leap_agent, then count the total lines of code"),
    ("MULTI2", "Search for the word 'def' in orchestrator.py and count how many functions there are"),
]


def run_leap_task(task: str, timeout: int = 120) -> tuple[float, str, bool]:
    """Run task with LEAP agent."""
    cmd = [
        "uv", "run", "leap",
        "-m", "qwen3:1.7b", "-s", "gemma3:1b",
        "-c", task, "--no-warmup"
    ]
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, 
                               timeout=timeout, cwd="/home/aditya/PycharmProjects/LEAP")
        elapsed = time.time() - start
        output = result.stdout + result.stderr
        success = result.returncode == 0 and len(output) > 100
        return elapsed, output, success
    except subprocess.TimeoutExpired:
        return timeout, "TIMEOUT", False
    except Exception as e:
        return time.time() - start, str(e), False


def run_baseline_task(task: str, timeout: int = 120) -> tuple[float, str, bool]:
    """Run task with Baseline ReAct agent."""
    cmd = ["uv", "run", "react-agent", "-m", "qwen3:1.7b", "-c", task]
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=timeout, cwd="/home/aditya/PycharmProjects/LEAP")
        elapsed = time.time() - start
        output = result.stdout + result.stderr
        success = result.returncode == 0 and len(output) > 100
        return elapsed, output, success
    except subprocess.TimeoutExpired:
        return timeout, "TIMEOUT", False
    except Exception as e:
        return time.time() - start, str(e), False


def estimate_tokens(text: str) -> int:
    """Rough token estimate (chars / 4)."""
    return len(text) // 4


def run_coding_benchmark():
    """Run coding benchmark suite."""
    print("=" * 70)
    print("CODING BENCHMARK: LEAP vs Baseline ReAct")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = []
    
    for task_id, task in CODING_TASKS:
        print(f"\n[{task_id}] {task[:60]}...")
        
        # LEAP
        print("  LEAP: ", end="", flush=True)
        leap_time, leap_out, leap_ok = run_leap_task(task)
        leap_tokens = estimate_tokens(leap_out)
        print(f"{leap_time:.1f}s, ~{leap_tokens} tok ({'✓' if leap_ok else '✗'})")
        
        results.append(CodingBenchmarkResult(
            task_id=task_id, task=task, agent="LEAP",
            time_seconds=round(leap_time, 2), success=leap_ok,
            output_length=leap_tokens,
            output_preview=leap_out[-300:] if leap_out else ""
        ))
        
        # Baseline
        print("  Base: ", end="", flush=True)
        base_time, base_out, base_ok = run_baseline_task(task)
        base_tokens = estimate_tokens(base_out)
        print(f"{base_time:.1f}s, ~{base_tokens} tok ({'✓' if base_ok else '✗'})")
        
        results.append(CodingBenchmarkResult(
            task_id=task_id, task=task, agent="Baseline",
            time_seconds=round(base_time, 2), success=base_ok,
            output_length=base_tokens,
            output_preview=base_out[-300:] if base_out else ""
        ))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    leap = [r for r in results if r.agent == "LEAP"]
    base = [r for r in results if r.agent == "Baseline"]
    
    leap_times = [r.time_seconds for r in leap if r.success]
    base_times = [r.time_seconds for r in base if r.success]
    leap_tokens = [r.output_length for r in leap if r.success]
    base_tokens = [r.output_length for r in base if r.success]
    
    print(f"\n{'Metric':<20} {'LEAP':>15} {'Baseline':>15}")
    print("-" * 50)
    print(f"{'Success Rate':<20} {f'{sum(1 for r in leap if r.success)}/{len(leap)}':>15} {f'{sum(1 for r in base if r.success)}/{len(base)}':>15}")
    print(f"{'Avg Time (s)':<20} {f'{sum(leap_times)/len(leap_times):.1f}' if leap_times else 'N/A':>15} {f'{sum(base_times)/len(base_times):.1f}' if base_times else 'N/A':>15}")
    print(f"{'Avg Tokens':<20} {f'{sum(leap_tokens)//len(leap_tokens)}' if leap_tokens else 'N/A':>15} {f'{sum(base_tokens)//len(base_tokens)}' if base_tokens else 'N/A':>15}")
    print(f"{'Total Tokens':<20} {sum(leap_tokens):>15} {sum(base_tokens):>15}")
    
    # Save
    with open("coding_benchmark_results.json", "w") as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    print(f"\nResults saved to coding_benchmark_results.json")
    
    return results


if __name__ == "__main__":
    run_coding_benchmark()
