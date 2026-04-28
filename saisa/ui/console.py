"""Rich console output helpers."""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

SAISA_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "tool": "dim cyan",
    "agent": "bold magenta",
    "user": "bold blue",
    "dim": "dim",
})

console = Console(theme=SAISA_THEME)
err_console = Console(stderr=True, theme=SAISA_THEME)


def print_banner(model_name: str, workspace: str) -> None:
    banner = Text()
    banner.append("  SAISA ", style="bold white on magenta")
    banner.append("  v2.0  ", style="bold white on blue")
    banner.append("  Coding Agent  ", style="bold white on dark_green")
    console.print()
    console.print(Panel(banner, border_style="magenta", expand=False))
    console.print(f"  [dim]Model:[/]     [bold]{model_name}[/]")
    console.print(f"  [dim]Workspace:[/] [bold]{workspace}[/]")
    console.print("  [dim]Commands:[/]  [bold]/help[/] [dim]|[/] [bold]/new[/] [dim]|[/] [bold]/swarm[/] [dim]|[/] [bold]/memory[/] [dim]|[/] [bold]/context[/] [dim]|[/] [bold]/quit[/]")
    console.print()


def print_help() -> None:
    table = Table(title="Commands", border_style="dim", show_header=True, header_style="bold cyan")
    table.add_column("Command", style="bold")
    table.add_column("Description")
    table.add_row("/help", "Show this help")
    table.add_row("/new", "Clear conversation history")
    table.add_row("/model <name>", "Switch model for this session")
    table.add_row("/save [name]", "Save current session")
    table.add_row("/sessions", "List saved sessions")
    table.add_row("/load <id>", "Load a saved session")
    table.add_row("/status", "Show current configuration")
    table.add_row("/tree [path]", "Show project tree")
    table.add_row("/diff", "Show git diff")
    table.add_row("/context [path]", "Auto-detect project stack and frameworks")
    table.add_row("/swarm <task>", "Run multi-agent swarm (architect+developer+security)")
    table.add_row("/memory", "Show persistent memory stats")
    table.add_row("/autopilot <task>", "Autonomous mode: plan, execute, verify")
    table.add_row("/saas <name> [stack]", "Generate full SaaS project (auth+payments+API)")
    table.add_row("/tiers", "Show LLM provider tiers (free -> premium)")
    table.add_row("/register <user> <pass>", "Create a user account")
    table.add_row("/login <user> <pass>", "Login and load API keys")
    table.add_row("/addkey <provider> <key>", "Store an API key in your vault")
    table.add_row("/keys", "List stored API keys")
    table.add_row("/compact", "Toggle compact mode (less verbose)")
    table.add_row("/quit", "Exit SAISA")
    console.print(table)


def print_tool_call(name: str, arguments: dict[str, Any]) -> None:
    args_short = _summarize_args(name, arguments)
    console.print(f"  [tool]> {name}[/tool]({args_short})", highlight=False)


def print_tool_result(name: str, output: str) -> None:
    try:
        data = json.loads(output)
        if "error" in data:
            console.print(f"  [error]  Error: {data['error']}[/error]")
            return
        # for file reads, show a compact view
        if name == "read_file" and "content" in data:
            path = data.get("path", "?")
            lines = data.get("total_lines", "?")
            console.print(f"  [success]  Read {path} ({lines} lines)[/]")
            return
        if name == "tree":
            console.print("  [success]  Tree displayed[/]")
            return
        if name in ("write_file", "edit_file", "create_directory"):
            path = data.get("path", "?")
            console.print(f"  [success]  {name}: {path}[/]")
            return
        if name == "run_command":
            ec = data.get("exit_code", "?")
            style = "success" if ec == 0 else "error"
            console.print(f"  [{style}]  exit {ec}[/]")
            if ec != 0 and data.get("stderr"):
                stderr_short = data["stderr"][:200]
                console.print(f"  [dim]{stderr_short}[/]")
            return
        if name.startswith("git_"):
            stdout = data.get("stdout", "").strip()
            if stdout:
                short = stdout[:200]
                console.print(f"  [dim]{short}[/]")
            return
        if name == "search_code":
            total = data.get("total", 0)
            console.print(f"  [success]  {total} matches[/]")
            return
        # generic
        console.print("  [dim]  OK[/]")
    except (json.JSONDecodeError, TypeError):
        short = output[:100]
        console.print(f"  [dim]{short}[/]")


def print_assistant(text: str) -> None:
    console.print()
    try:
        md = Markdown(text)
        console.print(md)
    except Exception:
        console.print(text)
    console.print()


def print_error(msg: str) -> None:
    console.print(f"[error]{msg}[/error]")


def print_info(msg: str) -> None:
    console.print(f"[info]{msg}[/info]")


def print_status(provider: str, workspace: str, history_len: int) -> None:
    console.print(f"  [dim]Provider:[/]  [bold]{provider}[/]")
    console.print(f"  [dim]Workspace:[/] [bold]{workspace}[/]")
    console.print(f"  [dim]History:[/]   [bold]{history_len} messages[/]")


def _summarize_args(name: str, args: dict[str, Any]) -> str:
    """Create a short summary of tool arguments for display."""
    if name in ("read_file", "write_file", "edit_file"):
        return args.get("path", "?")
    if name == "run_command":
        cmd = args.get("command", "?")
        return cmd[:80] + ("..." if len(cmd) > 80 else "")
    if name == "search_code":
        return args.get("pattern", "?")
    if name == "find_files":
        return args.get("pattern", "?")
    if name == "tree":
        return args.get("path", ".")
    if name == "git_commit":
        return args.get("message", "?")[:60]
    if name == "git_checkout":
        return args.get("branch", "?")
    if name == "list_directory":
        return args.get("path", ".")
    # generic
    parts = [f"{k}={repr(v)[:30]}" for k, v in list(args.items())[:3]]
    return ", ".join(parts)
