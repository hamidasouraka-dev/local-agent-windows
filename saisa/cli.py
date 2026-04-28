"""SAISA CLI — the main entry point."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from . import __version__
from .config import PROVIDER, WORKSPACE_ROOT


@click.command()
@click.option("--provider", "-p", default=PROVIDER, help="LLM provider: ollama, groq, openai, anthropic")
@click.option("--model", "-m", default="", help="Override model name")
@click.option("--workspace", "-w", default=str(WORKSPACE_ROOT), help="Workspace directory")
@click.option("--no-stream", is_flag=True, help="Disable streaming output")
@click.option("--run", "-r", default="", help="Run a single command and exit")
@click.version_option(version=__version__)
def main(
    provider: str,
    model: str,
    workspace: str,
    no_stream: bool,
    run: str,
) -> None:
    """SAISA - Super AI Self-Autonomous coding agent.

    A powerful terminal-based AI pair-programmer.
    """
    # Apply runtime overrides
    import saisa.config as cfg

    cfg.PROVIDER = provider
    cfg.WORKSPACE_ROOT = Path(workspace).resolve()
    cfg.STREAMING = not no_stream

    if model:
        _apply_model_override(provider, model)

    from .agent import CodingAgent
    from .providers import get_provider
    from .ui.console import (
        console,
        print_assistant,
        print_banner,
        print_error,
        print_help,
        print_info,
        print_status,
        print_tool_call,
        print_tool_result,
    )
    from .ui.input import UserInput

    # Initialise provider
    try:
        llm = get_provider(provider)
    except Exception as e:
        print_error(f"Failed to connect: {e}")
        sys.exit(1)

    agent = CodingAgent(llm)
    use_stream = cfg.STREAMING

    # Single-shot mode
    if run:
        _run_single(agent, run, use_stream, print_tool_call, print_tool_result, print_assistant)
        llm.close()
        return

    # Interactive REPL
    print_banner(llm.model_name, str(cfg.WORKSPACE_ROOT))
    user_input = UserInput()

    while True:
        line = user_input.read()
        if line is None:
            print_info("\nBye!")
            break

        text = line.strip()
        if not text:
            continue

        # Handle commands
        if text.startswith("/"):
            handled = _handle_command(
                text, agent, llm, cfg, print_help, print_info, print_error, print_status
            )
            if handled == "quit":
                break
            if handled:
                continue

        # Normal user turn
        try:
            if use_stream:
                full = ""
                for token in agent.run_turn_streaming(
                    text,
                    on_tool_start=print_tool_call,
                    on_tool_end=print_tool_result,
                ):
                    console.print(token, end="", highlight=False)
                    full += token
                if full:
                    console.print()  # newline after streaming
            else:
                reply = agent.run_turn(text)
                print_assistant(reply)
        except KeyboardInterrupt:
            print_info("\n[Interrupted]")
        except Exception as e:
            print_error(f"Error: {e}")

    llm.close()


def _apply_model_override(provider: str, model: str) -> None:
    import saisa.config as cfg

    p = provider.lower()
    if p == "ollama":
        cfg.OLLAMA_MODEL = model
    elif p == "groq":
        cfg.GROQ_MODEL = model
    elif p == "openai":
        cfg.OPENAI_MODEL = model
    elif p in ("anthropic", "claude"):
        cfg.ANTHROPIC_MODEL = model


def _run_single(agent, text, use_stream, on_tool_start, on_tool_end, print_fn) -> None:  # type: ignore
    from .ui.console import console

    if use_stream:
        for token in agent.run_turn_streaming(text, on_tool_start=on_tool_start, on_tool_end=on_tool_end):
            console.print(token, end="", highlight=False)
        console.print()
    else:
        reply = agent.run_turn(text)
        print_fn(reply)


def _handle_command(
    text: str,
    agent,  # type: ignore
    llm,  # type: ignore
    cfg,  # type: ignore
    print_help,  # type: ignore
    print_info,  # type: ignore
    print_error,  # type: ignore
    print_status,  # type: ignore
) -> str | bool:
    parts = text.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd in ("/quit", "/exit", "/q"):
        print_info("Bye!")
        return "quit"

    if cmd == "/help":
        print_help()
        return True

    if cmd == "/new":
        agent.clear_history()
        print_info("Conversation cleared.")
        return True

    if cmd == "/status":
        print_status(llm.model_name, str(cfg.WORKSPACE_ROOT), len(agent.history))
        return True

    if cmd == "/model":
        if not arg:
            print_info(f"Current model: {llm.model_name}")
        else:
            print_info(f"Model change requires restart: saisa --model {arg}")
        return True

    if cmd == "/save":
        from .session import save_session

        path = save_session(agent.history, llm.model_name, session_id=arg)
        print_info(f"Session saved: {path}")
        return True

    if cmd == "/sessions":
        from .session import list_sessions

        sessions = list_sessions()
        if not sessions:
            print_info("No saved sessions.")
        else:
            for s in sessions[:10]:
                print_info(f"  {s['id']}  ({s['provider']}, {s['messages']} msgs, {s['created']})")
        return True

    if cmd == "/load":
        if not arg:
            print_error("Usage: /load <session-id>")
            return True
        from pathlib import Path as P

        from .session import list_sessions, load_session

        sessions = list_sessions()
        match = next((s for s in sessions if s["id"] == arg), None)
        if not match:
            print_error(f"Session '{arg}' not found.")
            return True
        _, history = load_session(P(match["path"]))
        agent.history = history
        print_info(f"Loaded session '{arg}' ({len(history)} messages)")
        return True

    if cmd == "/tree":
        from .tools.file_tools import tree

        result = tree(arg or ".")
        from .ui.console import console

        console.print(result)
        return True

    if cmd == "/diff":
        import json

        from .tools.git_tools import git_diff

        result = json.loads(git_diff())
        stdout = result.get("stdout", "")
        if stdout:
            from rich.syntax import Syntax

            from .ui.console import console

            console.print(Syntax(stdout, "diff", theme="monokai"))
        else:
            print_info("No changes.")
        return True

    if cmd == "/compact":
        print_info("Compact mode toggled.")
        return True

    if cmd == "/memory":
        from .memory import Memory

        mem = Memory()
        stats = mem.stats()
        print_info(f"  Entries: {stats['total_entries']}")
        for cat, count in stats.get("categories", {}).items():
            print_info(f"    {cat}: {count}")
        return True

    if cmd == "/context":
        from .tools.project_tools import detect_project_context

        result = detect_project_context(arg or ".")
        from .ui.console import console

        console.print(result)
        return True

    if cmd == "/swarm":
        if not arg:
            from .swarm import AVAILABLE_AGENTS

            print_info("Available agents:")
            for name, role in AVAILABLE_AGENTS.items():
                print_info(f"  {name}: {role.specialty}")
            print_info("\nUsage: /swarm <task>")
        else:
            from .swarm import SwarmOrchestrator
            from .ui.console import console

            swarm = SwarmOrchestrator(llm)
            print_info("Running swarm: architect -> developer -> security...")
            results = swarm.run_swarm(arg)
            for r in results:
                console.print(f"\n[bold cyan]--- {r.get('agent', '?')} ---[/]")
                console.print(r.get("response", r.get("error", "No output")))
        return True

    if cmd in ("/autopilot", "/auto", "/pilot"):
        if not arg:
            print_error("Usage: /autopilot <objective>")
            print_info("Example: /autopilot Create a REST API with user auth using FastAPI")
            return True

        from .autopilot import Autopilot
        from .ui.console import console

        pilot = Autopilot(
            provider=llm,
            on_step_start=lambda s: console.print(f"\n[bold yellow][~] Step {s.id}: {s.description}[/]"),
            on_step_end=lambda s: console.print(
                f"[bold {'green' if s.status.value == 'done' else 'red'}]"
                f"  [{s.status.value}] {s.result[:150]}[/] ({s.duration:.1f}s)"
            ),
        )

        # Phase 1: Plan
        console.print(f"\n[bold magenta]AUTOPILOT[/] Planning: {arg}\n")
        plan = pilot.plan(arg)
        console.print(pilot.get_plan_summary(plan))

        # Phase 2: Execute
        console.print("\n[bold magenta]AUTOPILOT[/] Executing...\n")
        for event in pilot.execute(plan):
            if event["event"] == "task_complete":
                console.print(
                    f"\n[bold green]Done![/] {event['steps_done']}/{event['steps_total']} steps "
                    f"in {event['total_duration']}s"
                )
            elif event["event"] == "task_failed":
                console.print(f"\n[bold red]Failed at step {event['failed_step']}[/]")

        # Phase 3: Verify
        console.print("\n[bold magenta]AUTOPILOT[/] Verifying...\n")
        verification = pilot.verify(plan)
        status = "SUCCESS" if verification.get("success") else "ISSUES FOUND"
        console.print(f"[bold {'green' if verification.get('success') else 'yellow'}]{status}[/]")
        console.print(verification.get("summary", ""))
        issues = verification.get("issues", [])
        if issues:
            for issue in issues:
                console.print(f"  [yellow]- {issue}[/]")

        return True

    if cmd == "/tiers":
        from .tiers import list_tiers

        print_info(list_tiers())
        return True

    if cmd == "/saas":
        if not arg:
            print_info("Usage: /saas <project-name> [stack]")
            print_info("Stacks: fastapi (default), express")
            print_info("Example: /saas my-startup fastapi")
            return True
        parts_saas = arg.split(maxsplit=1)
        saas_name = parts_saas[0]
        saas_stack = parts_saas[1] if len(parts_saas) > 1 else "fastapi"
        from .tools.saas_templates import generate_saas
        from .ui.console import console

        result = generate_saas(saas_name, saas_stack)
        data = json.loads(result)
        if "error" in data:
            print_error(data["error"])
        else:
            console.print(f"[bold green]SaaS project created![/] {data['path']}")
            console.print(f"  Stack: {data['stack']}")
            console.print(f"  Files: {len(data['files_created'])}")
            for feat in data.get("features", []):
                console.print(f"  [dim]- {feat}[/]")
        return True

    if cmd == "/register":
        from .users import UserManager

        um = UserManager()
        parts_reg = arg.split(maxsplit=2)
        if len(parts_reg) < 2:
            print_error("Usage: /register <username> <password> [role]")
            return True
        username = parts_reg[0]
        password = parts_reg[1]
        role = parts_reg[2] if len(parts_reg) > 2 else "developer"
        result = um.register(username, password, role)
        if "error" in result:
            print_error(result["error"])
        else:
            print_info(f"User '{username}' registered as {role}")
        return True

    if cmd == "/login":
        from .users import UserManager, auto_configure_provider

        um = UserManager()
        parts_login = arg.split(maxsplit=1)
        if len(parts_login) < 2:
            print_error("Usage: /login <username> <password>")
            return True
        result = um.login(parts_login[0], parts_login[1])
        if "error" in result:
            print_error(result["error"])
        else:
            print_info(f"Logged in as {result['username']} ({result['role']})")
            # Auto-configure API keys from vault
            for prov in ["groq", "openai", "anthropic"]:
                env_map = auto_configure_provider(um, prov)
                if env_map:
                    print_info(f"  API key loaded for {prov}")
        return True

    if cmd == "/addkey":
        from .users import UserManager

        um = UserManager()
        parts_key = arg.split(maxsplit=1)
        if len(parts_key) < 2:
            print_error("Usage: /addkey <provider> <api-key>")
            print_info("Providers: groq, openai, anthropic")
            return True
        result = um.add_api_key(parts_key[0], parts_key[1])
        if "error" in result:
            print_error(result["error"])
        else:
            print_info(f"API key added for {parts_key[0]}: {result['key_masked']}")
        return True

    if cmd == "/keys":
        from .users import UserManager

        um = UserManager()
        keys = um.list_api_keys()
        if not keys:
            print_info("No API keys stored. Use /addkey <provider> <key>")
        else:
            for k in keys:
                print_info(f"  {k['provider']}: {k['key_masked']} ({k.get('label', '')})")
        return True

    print_error(f"Unknown command: {cmd}. Type /help for available commands.")
    return True


if __name__ == "__main__":
    main()
