"""LEAP Agent entry point."""
import argparse
import sys

from .config import LEAPConfig, MODEL_PAIRS
from .cli import run_cli


def main():
    parser = argparse.ArgumentParser(
        prog="leap",
        description="LEAP - Lightweight Edge Agent Protocol (4GB VRAM optimized)",
    )
    
    parser.add_argument(
        "--main-model", "-m",
        default="qwen3:4b",
        help="Main agent model (default: qwen3:4b)"
    )
    parser.add_argument(
        "--sub-model", "-s",
        default="qwen3:1.7b",
        help="Subagent model (default: qwen3:1.7b)"
    )
    parser.add_argument(
        "--pair", "-p",
        choices=list(MODEL_PAIRS.keys()),
        help="Use predefined model pair (4gb, 4gb_fast, 4gb_light, 8gb)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Disable verbose output"
    )
    parser.add_argument(
        "--no-warmup",
        action="store_true",
        help="Skip model warmup on startup"
    )
    parser.add_argument(
        "-c", "--command",
        help="Run single command and exit"
    )
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List available tools and exit"
    )
    
    args = parser.parse_args()
    
    # Build config
    if args.pair:
        pair = MODEL_PAIRS[args.pair]
        main_model = pair["main"]
        sub_model = pair["sub"]
    else:
        main_model = args.main_model
        sub_model = args.sub_model
    
    config = LEAPConfig(
        main_model=main_model,
        sub_model=sub_model,
        verbose=not args.quiet,
        warmup_models=not args.no_warmup,
    )
    
    # List tools
    if args.list_tools:
        from .orchestrator import LEAPOrchestrator
        agent = LEAPOrchestrator(LEAPConfig(warmup_models=False))
        print("Available tools:")
        for tool in sorted(agent.get_available_tools()):
            print(f"  • {tool}")
        return 0
    
    # Single command mode
    if args.command:
        from .orchestrator import LEAPOrchestrator
        agent = LEAPOrchestrator(config)
        result = agent.run(args.command)
        print(result)
        if config.verbose:
            metrics = agent.get_metrics()
            print(f"\n⏱  {metrics['total_time']:.1f}s")
        return 0
    
    # Interactive mode
    return run_cli(config)


if __name__ == "__main__":
    sys.exit(main())
