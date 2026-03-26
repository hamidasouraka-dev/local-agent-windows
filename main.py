"""
Agent local Windows — ligne de commande.
Lance : python main.py
"""

from __future__ import annotations

import atexit
import sys

from local_agent.config import (
    AGENT_BACKEND,
    AGENT_OWNER_NAME,
    AGENT_PERFORMANCE_MODE,
    ALLOW_FETCH_URL,
    ALLOW_OPEN_BROWSER,
    ALLOW_POWERSHELL,
    ALLOW_SMTP_SEND,
    GROQ_MODEL,
    OLLAMA_CRITIC_MODEL,
    OLLAMA_MODEL,
    SELF_EVAL_ENABLED,
    WORKSPACE_ROOT,
)
from local_agent.groq_agent import GroqAgent
from local_agent.ollama_agent import OllamaAgent


def _read_multiline_until_fin() -> str:
    """Lit plusieurs lignes jusqu’à une ligne contenant uniquement /fin (collage de specs, code, etc.)."""
    print("(Multiligne — colle ton texte, puis une ligne avec seulement /fin)", flush=True)
    lines: list[str] = []
    while True:
        try:
            raw = input()
        except (EOFError, KeyboardInterrupt):
            raise
        if raw.strip() == "/fin":
            break
        lines.append(raw)
    return "\n".join(lines).strip()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass

    backend = AGENT_BACKEND if AGENT_BACKEND in ("groq", "ollama") else "groq"
    print("Agent local — Windows")
    print(f"  Performance: {'max (prompt court, cache web, client HTTP réutilisé)' if AGENT_PERFORMANCE_MODE else 'standard (AGENT_PERFORMANCE_MODE=0)'}")
    print(f"  Backend   : {backend}")
    if backend == "ollama":
        print("  Inférence : locale (Ollama sur ton PC)")
    else:
        print("  Inférence : cloud Groq (mémoire fichier = disque local uniquement)")
    print(f"  Workspace : {WORKSPACE_ROOT}")
    print("  Mémoire   : memory/journal.md + outils append_memory_note / read_memory_notes")
    print("  Skills    : dossier skills/  |  Dissertations : dissertations/")
    if backend == "ollama":
        print(f"  Modèle    : {OLLAMA_MODEL}")
        crit = OLLAMA_CRITIC_MODEL or OLLAMA_MODEL
        print(f"  Critique  : {crit}")
        print(f"  Auto-éval.: {'oui' if SELF_EVAL_ENABLED else 'non (SELF_EVAL=0)'}")
    else:
        print(f"  Modèle    : {GROQ_MODEL}")
    print(f"  PowerShell: {'activé' if ALLOW_POWERSHELL else 'désactivé (ALLOW_POWERSHELL=1 pour activer)'}")
    print(f"  fetch_url : {'activé' if ALLOW_FETCH_URL else 'désactivé (ALLOW_FETCH_URL=1 pour pages web en texte)'}")
    print(f"  E-mail SMTP: {'activé' if ALLOW_SMTP_SEND else 'désactivé (ALLOW_SMTP_SEND=1 + SMTP_*)'}")
    print(f"  Navigateur : {'activé' if ALLOW_OPEN_BROWSER else 'désactivé (ALLOW_OPEN_BROWSER=1 pour URLs + wa.me)'}")
    print("  WhatsApp   : open_whatsapp_compose (wa.me — tu confirmes l’envoi dans l’app)")
    if AGENT_OWNER_NAME:
        print(f"  Créateur   : {AGENT_OWNER_NAME}")
    print("  Commandes : /quit sortir, /new nouvelle conversation, /paste texte long (fin = ligne /fin)")
    print()

    try:
        if backend == "ollama":
            agent: GroqAgent | OllamaAgent = OllamaAgent()
        else:
            agent = GroqAgent()
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Impossible de démarrer l'agent : {e}", file=sys.stderr)
        sys.exit(1)

    atexit.register(agent.close)

    while True:
        try:
            line = input("Toi > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir.")
            break
        if not line:
            continue
        if line.lower() in ("/quit", "/exit", "/q"):
            print("Au revoir.")
            break
        if line.lower() in ("/new", "/clear"):
            agent.clear_history()
            print("Historique effacé.")
            continue
        if line.lower() in ("/paste", "/long", "/multiline"):
            try:
                line = _read_multiline_until_fin()
            except (EOFError, KeyboardInterrupt):
                print("\nSaisie multiligne annulée.")
                continue
            if not line:
                print("(Message vide, ignoré.)")
                continue

        try:
            reply = agent.run_turn(line)
        except Exception as e:
            reply = f"Erreur : {e}"
        print()
        print("Agent >", reply)
        print()


if __name__ == "__main__":
    main()
