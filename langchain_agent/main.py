"""Entry point for the ReAct Agent CLI."""
import argparse
import sys

from .config import AgentConfig, AVAILABLE_MODELS
from .cli import run_cli


def main():
    parser = argparse.ArgumentParser(
        prog="react-agent",
        description="Baseline ReAct Agent - LangChain + Ollama",
    )
    
    parser.add_argument("-m", "--model", default="qwen3:4b", help="Ollama model (default: qwen3:4b)")
    parser.add_argument("--list-models", action="store_true", help="List models and exit")
    parser.add_argument("--no-streaming", action="store_true", help="Disable streaming")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature (default: 0.7)")
    parser.add_argument("-c", "--command", help="Run single command and exit")
    
    args = parser.parse_args()
    
    if args.list_models:
        print("Available models:")
        for m in AVAILABLE_MODELS:
            print(f"  • {m}")
        return 0
    
    config = AgentConfig(
        model=args.model,
        temperature=args.temperature,
        streaming=not args.no_streaming,
        verbose=args.verbose,
    )
    
    if args.command:
        from .agent import ReactAgent
        agent = ReactAgent(config)
        print(agent.run(args.command))
        return 0
    
    run_cli(config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
