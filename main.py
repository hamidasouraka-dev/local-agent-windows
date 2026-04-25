"""
Agent local Windows — ligne de commande.
Lance : python main.py
"""

from __future__ import annotations

import atexit
import json
import sys
import time
from datetime import datetime
from pathlib import Path

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
import httpx

# === AUTO-DETECT: Le modèle supporte-t-il les outils? ===
USE_SIMPLE_MODE = False
OLLAMA_URL = "http://127.0.0.1:11434"

def check_tools_support():
    """Test si le modèle accepte les outils"""
    global USE_SIMPLE_MODE
    try:
        client = httpx.Client(timeout=30.0)
        # Test simple avec le modèle
        response = client.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": "Dis juste 'ok'"}],
                "stream": False
            }
        )
        client.close()
        if response.status_code == 200:
            print(f"✓ Modèle {OLLAMA_MODEL} OK")
        else:
            print(f"⚠ Erreur {response.status_code}, mode simple")
            USE_SIMPLE_MODE = True
    except Exception as e:
        print(f"⚠ Mode simple: {e}")
        USE_SIMPLE_MODE = True

# Test au démarrage si Ollama
if AGENT_BACKEND == "ollama":
    check_tools_support()

# Mode simple (sans outils) si le modèle ne supporte pas les tools
USE_SIMPLE_MODE = False


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


def _print_help() -> None:
    """Affiche les commandes disponibles du REPL."""
    print("Commandes disponibles :")
    print("  /help                              Affiche cette aide")
    print("  /new                               Efface l'historique de conversation")
    print("  /memory [tag]                      Affiche le journal mémoire (filtrable)")
    print("  /status                            Affiche backend/modèle/options")
    print("  /history                           Résume l'historique en mémoire")
    print("  /model <nom>                       Change le modèle pour la session")
    print("  /search <requête> [max=6]          Lance web_search")
    print("  /news <requête> [max=5]            Lance news_search")
    print("  /note <tag> <texte>                Ajoute une note mémoire taggée")
    print("  /export                            Exporte la session en markdown")
    print("  /autopilot [minutes] <objectif>    Mode autonome (défaut 60 min)")
    print("  /paste                             Saisie multiligne (fin avec /fin)")
    print("  /quit                              Quitte l'agent")


def _pretty_json_or_raw(s: str) -> str:
    try:
        return json.dumps(json.loads(s), ensure_ascii=False, indent=2)
    except Exception:
        return s


def _memory_content_from_json(s: str) -> str:
    try:
        data = json.loads(s)
    except Exception:
        return s
    content = data.get("content")
    if isinstance(content, str):
        return content
    return json.dumps(data, ensure_ascii=False, indent=2)


def _parse_optional_int(raw: str, default: int) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _export_session(agent: GroqAgent | OllamaAgent, title: str = "session") -> Path:
    """Exporte l'historique courant dans workspace/memory et retourne le chemin."""
    hist = getattr(agent, "_history", [])
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    p = Path(WORKSPACE_ROOT) / "memory" / f"{title}-{stamp}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Export {title}\n"]
    for msg in hist:
        role = msg.get("role", "?")
        content = str(msg.get("content", "")).strip()
        lines.append(f"\n## {role}\n{content}\n")
    p.write_text("\n".join(lines), encoding="utf-8", newline="")
    return p


def _run_autopilot(agent: GroqAgent | OllamaAgent, objective: str, minutes: int) -> None:
    """Exécute des tours autonomes bornés (temps/tours), avec checkpoints et journal."""
    minutes = max(1, min(minutes, 60))
    deadline = time.monotonic() + (minutes * 60)
    started = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = Path(WORKSPACE_ROOT) / "memory" / f"autopilot-log-{started}.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        f"# Journal Autopilot\n\n- Début: {datetime.now().isoformat(timespec='seconds')}\n- Objectif: {objective}\n",
        encoding="utf-8",
        newline="",
    )
    turn = 0
    checkpoint_every = 10
    prompt = (
        f"Objectif prioritaire : {objective}\n"
        "Travaille en autonomie complète. Si un détail manque, propose 2 à 4 choix clairs "
        "et sélectionne l'option la plus raisonnable pour continuer sans bloquer."
    )
    print(f"Autopilot lancé pour {minutes} min. Objectif: {objective}")
    print(f"Journal autopilot : {log_path}")
    no_progress_streak = 0
    while time.monotonic() < deadline and turn < 120:
        turn += 1
        print(f"\n--- Autopilot tour {turn} ---")
        try:
            reply = agent.run_turn(prompt)
        except Exception as e:
            print(f"Erreur autopilot : {e}")
            break
        print("Agent >", reply)
        with log_path.open("a", encoding="utf-8", newline="") as f:
            f.write(f"\n\n## Tour {turn}\n{reply}\n")
        low = reply.lower()
        if "tâche terminée" in low or "mission terminée" in low:
            print("Autopilot: arrêt (objectif déclaré terminé).")
            break
        if "aucune progression" in low or "je ne peux pas" in low or "bloqué" in low:
            no_progress_streak += 1
        else:
            no_progress_streak = 0
        if no_progress_streak >= 3:
            print("Autopilot: arrêt (progression insuffisante sur 3 tours).")
            break
        if turn % checkpoint_every == 0:
            cp = _export_session(agent, title="autopilot-checkpoint")
            print(f"Checkpoint exporté : {cp}")
        prompt = (
            "Continue le travail en autonomie. Avance concrètement (code/tests/docs) et "
            "ne me redemande pas de validation sauf action risquée."
        )
    final_export = _export_session(agent, title="autopilot-final")
    with log_path.open("a", encoding="utf-8", newline="") as f:
        f.write(
            f"\n\n- Fin: {datetime.now().isoformat(timespec='seconds')}\n"
            f"- Tours: {turn}\n"
            f"- Export final: {final_export}\n"
        )
    print("Autopilot: fin du budget temps/tours.")
    print(f"Export final : {final_export}")


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
    print("  Commandes : /help, /status, /history, /memory, /search, /news, /note, /model, /export, /autopilot, /quit, /new, /paste")
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
        if line.lower() == "/help":
            _print_help()
            continue
        if line.lower() == "/status":
            model = getattr(agent, "_model", "?")
            print(f"Backend: {backend}")
            print(f"Modèle: {model}")
            print(f"Tours en historique: {len(getattr(agent, '_history', []))}")
            print(f"PowerShell: {'ON' if ALLOW_POWERSHELL else 'OFF'} | fetch_url: {'ON' if ALLOW_FETCH_URL else 'OFF'} | browser: {'ON' if ALLOW_OPEN_BROWSER else 'OFF'} | smtp: {'ON' if ALLOW_SMTP_SEND else 'OFF'}")
            continue
        if line.lower() == "/history":
            hist = getattr(agent, "_history", [])
            print(f"Messages en mémoire: {len(hist)}")
            for msg in hist[-6:]:
                role = msg.get("role", "?")
                content = str(msg.get("content", "")).replace("\n", " ").strip()
                print(f"- {role}: {content[:140]}")
            continue
        if line.lower().startswith("/memory"):
            parts = line.split(maxsplit=1)
            tag = parts[1].strip() if len(parts) > 1 else None
            out = agent._ctx.read_memory_notes(tag=tag)
            print(_memory_content_from_json(out))
            continue
        if line.lower().startswith("/search "):
            payload = line[len("/search ") :].strip()
            if not payload:
                print("Usage: /search <requête> [max]")
                continue
            query = payload
            max_results = 6
            if " " in payload:
                left, right = payload.rsplit(" ", 1)
                if right.isdigit():
                    query = left.strip()
                    max_results = max(1, min(int(right), 20))
            print(_pretty_json_or_raw(agent._ctx.web_search(query, max_results=max_results)))
            continue
        if line.lower().startswith("/news "):
            payload = line[len("/news ") :].strip()
            if not payload:
                print("Usage: /news <requête> [max]")
                continue
            query = payload
            max_results = 5
            if " " in payload:
                left, right = payload.rsplit(" ", 1)
                if right.isdigit():
                    query = left.strip()
                    max_results = max(1, min(int(right), 20))
            print(_pretty_json_or_raw(agent._ctx.news_search(query, max_results=max_results)))
            continue
        if line.lower().startswith("/note "):
            payload = line[len("/note ") :].strip()
            if not payload or " " not in payload:
                print("Usage: /note <tag> <texte>")
                continue
            tag, note = payload.split(" ", 1)
            print(_pretty_json_or_raw(agent._ctx.append_memory_note(note, tag=tag)))
            continue
        if line.lower().startswith("/model "):
            new_model = line[len("/model ") :].strip()
            if not new_model:
                print("Usage: /model <nom>")
                continue
            setattr(agent, "_model", new_model)
            print(f"Modèle de session mis à jour : {new_model}")
            continue
        if line.lower() == "/export":
            p = _export_session(agent, title="session")
            print(f"Session exportée : {p}")
            continue
        if line.lower().startswith("/autopilot"):
            parts = line.split(maxsplit=2)
            minutes = 60
            objective = ""
            if len(parts) == 2:
                if parts[1].isdigit():
                    minutes = _parse_optional_int(parts[1], 60)
                else:
                    objective = parts[1]
            elif len(parts) >= 3:
                minutes = _parse_optional_int(parts[1], 60) if parts[1].isdigit() else 60
                objective = parts[2] if parts[1].isdigit() else " ".join(parts[1:])
            if not objective:
                objective = input("Objectif autopilot > ").strip()
            if not objective:
                print("Objectif vide, annulé.")
                continue
            _run_autopilot(agent, objective, minutes)
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
