"""Interactive CLI for the ReAct Agent."""
import sys
import readline
from typing import Optional

from .agent import ReactAgent
from .config import AgentConfig, AVAILABLE_MODELS


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"


def print_colored(text: str, color: str = Colors.RESET, bold: bool = False):
    prefix = Colors.BOLD if bold else ""
    print(f"{prefix}{color}{text}{Colors.RESET}")


def print_banner():
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ██████╗ ███████╗ █████╗  ██████╗████████╗                   ║
║   ██╔══██╗██╔════╝██╔══██╗██╔════╝╚══██╔══╝                   ║
║   ██████╔╝█████╗  ███████║██║        ██║                      ║
║   ██╔══██╗██╔══╝  ██╔══██║██║        ██║                      ║
║   ██║  ██║███████╗██║  ██║╚██████╗   ██║                      ║
║   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝   ╚═╝                      ║
║                                                               ║
║   Baseline ReAct Agent • LangChain + Ollama                   ║
║   Type /help for commands, /quit to exit                      ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print_colored(banner, Colors.CYAN, bold=True)


def print_help():
    help_text = """
Commands:
  /help     Show this help
  /quit     Exit
  /clear    Clear history
  /model    Switch or show model
  /models   List models
  /tools    List tools
"""
    print_colored(help_text, Colors.YELLOW)


def run_cli(config: Optional[AgentConfig] = None):
    config = config or AgentConfig()
    agent = ReactAgent(config)
    
    print_banner()
    print_colored(f"  Model: {config.model} | Tools: {len(agent.tools)}", Colors.DIM)
    print()
    
    try:
        readline.read_history_file(".react_agent_history")
    except FileNotFoundError:
        pass
    
    while True:
        try:
            print_colored("You: ", Colors.GREEN, bold=True)
            
            lines = []
            while True:
                line = input()
                if line.endswith("\\"):
                    lines.append(line[:-1])
                else:
                    lines.append(line)
                    break
            
            user_input = "\n".join(lines).strip()
            
            if not user_input:
                continue
            
            if user_input.startswith("/"):
                cmd = user_input.lower().split()[0]
                args = user_input.split()[1:] if len(user_input.split()) > 1 else []
                
                if cmd in ["/quit", "/exit"]:
                    print_colored("\nGoodbye! 👋", Colors.CYAN)
                    break
                elif cmd == "/help":
                    print_help()
                elif cmd == "/clear":
                    agent.clear_history()
                    print_colored("History cleared.", Colors.YELLOW)
                elif cmd == "/models":
                    print_colored("\nModels:", Colors.YELLOW)
                    for m in AVAILABLE_MODELS:
                        marker = "  → " if m == config.model else "    "
                        print(f"{marker}{m}")
                elif cmd == "/model":
                    if args:
                        agent.set_model(args[0])
                        print_colored(f"Switched to: {args[0]}", Colors.GREEN)
                    else:
                        print_colored(f"Current: {config.model}", Colors.YELLOW)
                elif cmd == "/tools":
                    print_colored("\nTools:", Colors.YELLOW)
                    for t in sorted(agent.get_available_tools()):
                        print(f"  • {t}")
                else:
                    print_colored(f"Unknown: {cmd}", Colors.RED)
                continue
            
            print()
            print_colored("Agent: ", Colors.BLUE, bold=True)
            
            if config.streaming:
                try:
                    for chunk in agent.run_streaming(user_input):
                        print(chunk, end="", flush=True)
                    print()
                except KeyboardInterrupt:
                    print_colored("\n(Cancelled)", Colors.DIM)
            else:
                print(agent.run(user_input))
            
            print()
            
        except KeyboardInterrupt:
            print_colored("\n\nUse /quit to exit.", Colors.DIM)
        except EOFError:
            print_colored("\nGoodbye! 👋", Colors.CYAN)
            break
    
    try:
        readline.write_history_file(".react_agent_history")
    except:
        pass


if __name__ == "__main__":
    run_cli()
