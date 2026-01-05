#!/usr/bin/env python3
"""Benchmark runner for LEAP vs Baseline ReAct comparison."""
import json
import time
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime


@dataclass
class BenchmarkResult:
    """Result of a single benchmark task."""
    task_id: str
    task: str
    agent: str
    time_seconds: float
    success: bool
    tool_used: Optional[str] = None
    output_preview: str = ""
    error: Optional[str] = None


# Benchmark tasks
BENCHMARK_TASKS = [
    # File Operations
    ("F1", "List files in the langchain_agent directory"),
    ("F2", "Read the contents of pyproject.toml"),
    
    # Web & Information
    ("W1", "Search for OpenAI GPT-5 release date"),
    ("W2", "What is the current date and time?"),
    
    # Calculations
    ("C1", "Calculate 15% of 250"),
    ("C2", "Calculate the square root of 144"),
    ("C3", "Calculate 2^10 + 3^5"),
    
    # Shell Commands  
    ("S1", "Show the current working directory"),
    ("S2", "List environment info like OS and Python version"),
    
    # Code Analysis
    ("A1", "Analyze the structure of leap_agent/orchestrator.py"),
]


def run_leap_task(task: str, timeout: int = 120) -> tuple[float, str, bool]:
    """Run task with LEAP agent."""
    cmd = [
        "uv", "run", "leap",
        "-m", "qwen3:1.7b",
        "-s", "gemma3:1b",
        "-c", task,
        "--no-warmup"
    ]
    
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/home/aditya/PycharmProjects/LEAP"
        )
        elapsed = time.time() - start
        output = result.stdout + result.stderr
        success = result.returncode == 0 and len(output) > 50
        return elapsed, output, success
    except subprocess.TimeoutExpired:
        return timeout, "TIMEOUT", False
    except Exception as e:
        return time.time() - start, str(e), False


def run_baseline_task(task: str, timeout: int = 120) -> tuple[float, str, bool]:
    """Run task with Baseline ReAct agent."""
    cmd = [
        "uv", "run", "react-agent",
        "-m", "qwen3:1.7b",
        "-c", task,
    ]
    
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/home/aditya/PycharmProjects/LEAP"
        )
        elapsed = time.time() - start
        output = result.stdout + result.stderr
        success = result.returncode == 0 and len(output) > 50
        return elapsed, output, success
    except subprocess.TimeoutExpired:
        return timeout, "TIMEOUT", False
    except Exception as e:
        return time.time() - start, str(e), False


def extract_metrics_from_output(output: str) -> dict:
    """Extract LEAP metrics from verbose output."""
    metrics = {}
    if "Phase 1" in output:
        # Try to extract phase times
        import re
        phase1 = re.search(r"Phase 1.*?(\d+\.?\d*)s", output)
        phase2 = re.search(r"Phase 2.*?(\d+\.?\d*)s", output)
        phase3 = re.search(r"Phase 3.*?(\d+\.?\d*)s", output)
        if phase1:
            metrics["phase1"] = float(phase1.group(1))
        if phase2:
            metrics["phase2"] = float(phase2.group(1))
        if phase3:
            metrics["phase3"] = float(phase3.group(1))
        
        # Token reduction
        reduction = re.search(r"Token reduction: (\d+)%", output)
        if reduction:
            metrics["token_reduction"] = int(reduction.group(1))
        
        # Tool used
        tool = re.search(r"Tool: (\w+)", output)
        if tool:
            metrics["tool"] = tool.group(1)
    
    return metrics


def run_benchmark():
    """Run full benchmark suite."""
    print("=" * 60)
    print("LEAP vs Baseline ReAct Benchmark")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = []
    
    for task_id, task in BENCHMARK_TASKS:
        print(f"\n[{task_id}] {task[:50]}...")
        
        # Run LEAP
        print("  LEAP: ", end="", flush=True)
        leap_time, leap_output, leap_success = run_leap_task(task)
        leap_metrics = extract_metrics_from_output(leap_output)
        print(f"{leap_time:.1f}s ({'✓' if leap_success else '✗'})")
        
        results.append(BenchmarkResult(
            task_id=task_id,
            task=task,
            agent="LEAP",
            time_seconds=round(leap_time, 2),
            success=leap_success,
            tool_used=leap_metrics.get("tool"),
            output_preview=leap_output[-200:] if leap_output else "",
        ))
        
        # Run Baseline  
        print("  Base: ", end="", flush=True)
        base_time, base_output, base_success = run_baseline_task(task)
        print(f"{base_time:.1f}s ({'✓' if base_success else '✗'})")
        
        results.append(BenchmarkResult(
            task_id=task_id,
            task=task,
            agent="Baseline",
            time_seconds=round(base_time, 2),
            success=base_success,
            output_preview=base_output[-200:] if base_output else "",
        ))
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    leap_results = [r for r in results if r.agent == "LEAP"]
    base_results = [r for r in results if r.agent == "Baseline"]
    
    leap_times = [r.time_seconds for r in leap_results if r.success]
    base_times = [r.time_seconds for r in base_results if r.success]
    
    print(f"\nLEAP Agent:")
    print(f"  Success: {sum(1 for r in leap_results if r.success)}/{len(leap_results)}")
    print(f"  Avg Time: {sum(leap_times)/len(leap_times):.1f}s" if leap_times else "  N/A")
    
    print(f"\nBaseline Agent:")
    print(f"  Success: {sum(1 for r in base_results if r.success)}/{len(base_results)}")
    print(f"  Avg Time: {sum(base_times)/len(base_times):.1f}s" if base_times else "  N/A")
    
    # Save results
    with open("benchmark_results.json", "w") as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    print(f"\nResults saved to benchmark_results.json")
    
    return results


if __name__ == "__main__":
    run_benchmark()
