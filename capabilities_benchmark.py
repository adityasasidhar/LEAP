#!/usr/bin/env python3
"""Capabilities Benchmark: Testing breadth of agent skills."""
import json
import time
import subprocess
import re
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CapabilityResult:
    """Result for capability benchmark."""
    category: str
    task_id: str
    task: str
    agent: str
    time_seconds: float
    success: bool
    output_preview: str = ""


# Broad capabilities tasks
TASKS = [
    # 1. Research & Synthesis
    ("RES1", "Research", "Research the history of Python 3.0 release and summarize the key controversies in 3 bullet points."),
    ("RES2", "Research", "Find the 3 most popular Python web frameworks in 2024 and list their GitHub star counts."),
    
    # 2. Creative & Structured Writing
    ("WRT1", "Writing", "Write a haiku about recursion."),
    ("WRT2", "Writing", "Create a JSON schema for a 'User' profile with fields: name, age, email, and preferences."),
    
    # 3. System & Environment
    ("SYS1", "System", "Check if 'docker' is installed and running on this system."),
    ("SYS2", "System", "Find the largest file in the current directory."),
    
    # 4. Logic & Reasoning
    ("LOG1", "Logic", "If I have 3 apples and I eat one, then buy two more, how many do I have?"),
    ("LOG2", "Logic", "Solve this riddle: I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?"),
]


def run_agent_task(agent_cmd: list, task: str, timeout: int = 120) -> tuple[float, str, bool]:
    """Run task with specified agent."""
    start = time.time()
    try:
        # Construct command
        full_cmd = agent_cmd + ["-c", task]
        
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/home/aditya/PycharmProjects/LEAP"
        )
        elapsed = time.time() - start
        final_output = result.stdout + result.stderr
        
        # Simple success heuristic: non-empty output and no error code
        # Ideally, we'd have an LLM judge this, but for now we look for reasonable output length
        success = result.returncode == 0 and len(final_output.strip()) > 20
        
        return elapsed, final_output, success
    except subprocess.TimeoutExpired:
        return timeout, "TIMEOUT", False
    except Exception as e:
        return time.time() - start, str(e), False


def run_benchmark():
    """Run capabilities benchmark suite."""
    print("=" * 80)
    print("CAPABILITIES BENCHMARK: Breadth of Skills")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    results = []
    
    # Run LEAP first, then Baseline
    agents = [
        ("LEAP", ["uv", "run", "leap", "-m", "qwen3:1.7b", "-s", "gemma3:1b", "--no-warmup"]),
        ("Baseline", ["uv", "run", "react-agent", "-m", "qwen3:1.7b"])
    ]
    
    for agent_name, agent_cmd in agents:
        print(f"\n--- Testing {agent_name} Agent ---")
        
        for task_id, category, task in TASKS:
            print(f"\n[{task_id}] ({category}) {task[:60]}...")
            
            elapsed, output, success = run_agent_task(agent_cmd, task)
            
            # Print brief preview of answer (first line or so)
            preview = output.strip().split('\n')[-1] if output else "No output"
            if len(preview) > 80: preview = preview[:77] + "..."
            print(f"  Result: {elapsed:.1f}s | Success: {success}")
            print(f"  > {preview}")
            
            results.append(CapabilityResult(
                category=category,
                task_id=task_id, task=task, agent=agent_name,
                time_seconds=round(elapsed, 2), success=success,
                output_preview=output[-300:] if output else ""
            ))
            
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    categories = sorted(list(set(t[1] for t in TASKS)))
    
    print(f"{'Category':<15} | {'LEAP (Avg s)':<15} | {'Baseline (Avg s)':<15}")
    print("-" * 55)
    
    for cat in categories:
        leap_res = [r for r in results if r.agent == "LEAP" and r.category == cat]
        base_res = [r for r in results if r.agent == "Baseline" and r.category == cat]
        
        leap_time = sum(r.time_seconds for r in leap_res) / len(leap_res) if leap_res else 0
        base_time = sum(r.time_seconds for r in base_res) / len(base_res) if base_res else 0
        
        print(f"{cat:<15} | {leap_time:<15.1f} | {base_time:<15.1f}")

    # Save
    with open("capabilities_benchmark_results.json", "w") as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    print(f"\nResults saved to capabilities_benchmark_results.json")


if __name__ == "__main__":
    run_benchmark()
