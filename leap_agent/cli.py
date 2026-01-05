"""LEAP Agent CLI - Interactive interface."""
import sys
import readline
from typing import Optional

from .orchestrator import LEAPOrchestrator
from .config import LEAPConfig, MODEL_PAIRS
from .inference import test_ollama_connection


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"


def print_colored(text: str, color: str = Colors.RESET, bold: bool = False):
    prefix = Colors.BOLD if bold else ""
    print(f"{prefix}{color}{text}{Colors.RESET}")


def print_banner():
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ██╗     ███████╗ █████╗ ██████╗                             ║
║   ██║     ██╔════╝██╔══██╗██╔══██╗                            ║
║   ██║     █████╗  ███████║██████╔╝                            ║
║   ██║     ██╔══╝  ██╔══██║██╔═══╝                             ║
║   ███████╗███████╗██║  ██║██║                                 ║
║   ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝                                 ║
║                                                               ║
║   Lightweight Edge Agent Protocol                             ║
║   Optimized for 4GB VRAM • Sequential Orchestration           ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print_colored(banner, Colors.CYAN, bold=True)


def print_help():
    help_text = """
Commands:
  /help      Show this help
  /quit      Exit  
  /metrics   Show last task metrics
  /tools     List available tools
  /models    Show model pair info
  /verbose   Toggle verbose mode
  /clear     Clear screen
"""
    print_colored(help_text, Colors.YELLOW)


def run_cli(config: Optional[LEAPConfig] = None):
    """Run interactive LEAP CLI."""
    config = config or LEAPConfig()
    
    print_banner()
    
    # Check Ollama connection
    if not test_ollama_connection():
        print_colored("❌ Ollama not running! Start with: ollama serve", Colors.RED)
        return 1
    
    print_colored(f"  Main: {config.main_model} | Sub: {config.sub_model}", Colors.DIM)
    print_colored("  Type /help for commands, /quit to exit\n", Colors.DIM)
    
    # Initialize agent
    print_colored("🔧 Initializing LEAP agent...", Colors.YELLOW)
    try:
        agent = LEAPOrchestrator(config)
        print_colored(f"✅ Ready! {len(agent.get_available_tools())} tools loaded\n", Colors.GREEN)
    except Exception as e:
        print_colored(f"❌ Failed to initialize: {e}", Colors.RED)
        return 1
    
    # Command history
    try:
        readline.read_history_file(".leap_history")
    except FileNotFoundError:
        pass
    
    while True:
        try:
            print_colored("You: ", Colors.GREEN, bold=True)
            user_input = input().strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                cmd = user_input.lower().split()[0]
                
                if cmd in ["/quit", "/exit", "/q"]:
                    print_colored("\n👋 Goodbye!", Colors.CYAN)
                    break
                elif cmd == "/help":
                    print_help()
                elif cmd == "/metrics":
                    metrics = agent.get_metrics()
                    print_colored("\n📊 Last Task Metrics:", Colors.YELLOW)
                    for k, v in metrics.items():
                        print(f"   {k}: {v}")
                    print()
                elif cmd == "/tools":
                    tools = agent.get_available_tools()
                    print_colored(f"\n🔧 Tools ({len(tools)}):", Colors.YELLOW)
                    for t in sorted(tools):
                        print(f"   • {t}")
                    print()
                elif cmd == "/models":
                    print_colored("\n🤖 Current Model Pair:", Colors.YELLOW)
                    print(f"   Main: {config.main_model}")
                    print(f"   Sub:  {config.sub_model}")
                    print_colored("\n📋 Available Pairs:", Colors.YELLOW)
                    for name, pair in MODEL_PAIRS.items():
                        print(f"   {name}: {pair['main']} + {pair['sub']}")
                        print(f"      {pair['description']}")
                    print()
                elif cmd == "/verbose":
                    config.verbose = not config.verbose
                    agent.config.verbose = config.verbose
                    state = "ON" if config.verbose else "OFF"
                    print_colored(f"Verbose mode: {state}", Colors.YELLOW)
                elif cmd == "/clear":
                    print("\033[2J\033[H")
                    print_banner()
                else:
                    print_colored(f"Unknown command: {cmd}", Colors.RED)
                continue
            
            # Process query
            print()
            print_colored("LEAP: ", Colors.BLUE, bold=True)
            
            try:
                response = agent.run(user_input)
                print(response)
                
                # Show brief metrics
                if config.track_latency:
                    metrics = agent.get_metrics()
                    print_colored(
                        f"\n⏱  {metrics['total_time']:.1f}s | "
                        f"Tool: {metrics['tool'] or 'none'} | "
                        f"Reduction: {metrics['token_reduction']}",
                        Colors.DIM
                    )
            except Exception as e:
                print_colored(f"Error: {e}", Colors.RED)
            
            print()
            
        except KeyboardInterrupt:
            print_colored("\n\nUse /quit to exit.", Colors.DIM)
        except EOFError:
            print_colored("\n👋 Goodbye!", Colors.CYAN)
            break
    
    # Save history
    try:
        readline.write_history_file(".leap_history")
    except:
        pass
    
    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
