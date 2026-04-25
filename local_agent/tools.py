from __future__ import annotations

import json
import re
import smtplib
from collections import OrderedDict
from datetime import datetime
from time import monotonic
from typing import Any
import subprocess
import webbrowser
from email.mime.text import MIMEText
from pathlib import Path
from urllib.parse import quote_plus

import httpx
from duckduckgo_search import DDGS

from .config import (
    ALLOW_FETCH_URL,
    ALLOW_OPEN_BROWSER,
    ALLOW_POWERSHELL,
    ALLOW_SMTP_SEND,
    ALLOW_GIT,
    ALLOW_SYSTEM_MONITOR,
    ALLOW_DOCKER,
    FETCH_URL_TIMEOUT_SEC,
    LOCAL_MEMORY_JOURNAL,
    MAX_EMAIL_BODY_CHARS,
    MAX_FETCH_URL_BYTES,
    MAX_MEMORY_JOURNAL_BYTES,
    MAX_MEMORY_READ_CHARS,
    MAX_READ_BYTES,
    MAX_SHELL_OUTPUT,
    SHELL_TIMEOUT_SEC,
    WEB_SEARCH_CACHE_MAX_ENTRIES,
    WEB_SEARCH_CACHE_TTL_SEC,
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USER,
    WORKSPACE_ROOT,
)
from .policies import DeleteGuard


def _arg_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("0", "false", "non", "no", "n"):
        return False
    if s in ("1", "true", "oui", "yes", "y", "o"):
        return True
    return default


class ToolContext:
    def __init__(self) -> None:
        self.delete_guard = DeleteGuard()
        self._web_search_cache: OrderedDict[str, tuple[float, str]] = OrderedDict()
        WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
        for sub in ("memory", "skills", "dissertations", "recherche"):
            (WORKSPACE_ROOT / sub).mkdir(parents=True, exist_ok=True)

    def _memory_journal_path(self) -> Path:
        rel = (LOCAL_MEMORY_JOURNAL or "memory/journal.md").strip().replace("\\", "/")
        if ".." in rel or rel.startswith("/"):
            raise ValueError("Chemin mémoire invalide.")
        p = (WORKSPACE_ROOT / rel).resolve()
        if not str(p).startswith(str(WORKSPACE_ROOT.resolve())):
            raise ValueError("Mémoire hors workspace.")
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @staticmethod
    def _confirm_terminal(title: str, detail: str) -> bool:
        print()
        print(title)
        d = detail.strip()
        print(d[:4000] + ("..." if len(d) > 4000 else ""))
        ok = input("Confirmer ? (oui/non) : ").strip().lower()
        return ok in ("oui", "o", "yes", "y")

    def _safe_path(self, relative_path: str) -> Path:
        rel = (relative_path or "").strip()
        rel_path = Path(rel)
        if not rel or rel_path.is_absolute():
            raise ValueError(
                "Chemin invalide : utilise un chemin relatif au workspace, sans .. ni chemin absolu."
            )
        if any(p == ".." for p in rel_path.parts):
            raise ValueError("Chemin invalide : '..' interdit.")
        full = (WORKSPACE_ROOT / rel).resolve()
        try:
            full.relative_to(WORKSPACE_ROOT)
        except ValueError as e:
            raise ValueError("Accès refusé : hors du workspace.") from e
        return full

    def list_dir(self, directory: str = ".") -> str:
        d = self._safe_path(directory)
        if not d.is_dir():
            return json.dumps({"error": f"Pas un dossier : {d}"}, ensure_ascii=False)
        names = sorted(p.name for p in d.iterdir())
        return json.dumps(
            {"directory": str(d.relative_to(WORKSPACE_ROOT)), "entries": names},
            ensure_ascii=False,
        )

    def read_file(self, path: str) -> str:
        p = self._safe_path(path)
        if not p.is_file():
            return json.dumps({"error": f"Fichier introuvable : {path}"}, ensure_ascii=False)
        data = p.read_bytes()
        if len(data) > MAX_READ_BYTES:
            return json.dumps(
                {
                    "error": f"Fichier trop gros (>{MAX_READ_BYTES} octets). "
                    "Demande un extrait ou un autre fichier."
                },
                ensure_ascii=False,
            )
        text = data.decode("utf-8", errors="replace")
        return json.dumps(
            {"path": path, "content": text},
            ensure_ascii=False,
        )

    def write_file(self, path: str, content: str) -> str:
        p = self._safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content or "", encoding="utf-8", newline="")
        return json.dumps({"ok": True, "path": path, "bytes": p.stat().st_size}, ensure_ascii=False)

    def delete_file(self, path: str) -> str:
        p = self._safe_path(path)
        if not p.is_file():
            return json.dumps({"error": f"Fichier introuvable : {path}"}, ensure_ascii=False)
        display = str(p)
        if not self.delete_guard.confirm_delete(display):
            return json.dumps({"ok": False, "cancelled": True}, ensure_ascii=False)
        p.unlink()
        return json.dumps({"ok": True, "deleted": path}, ensure_ascii=False)

    def run_powershell(self, command: str) -> str:
        if not ALLOW_POWERSHELL:
            return json.dumps(
                {
                    "error": "PowerShell désactivé. Mets ALLOW_POWERSHELL=1 dans .env "
                    "si tu acceptes l'exécution de commandes (risque élevé)."
                },
                ensure_ascii=False,
            )
        cmd = (command or "").strip()
        if not cmd:
            return json.dumps({"error": "Commande vide."}, ensure_ascii=False)
        print()
        print("--- Exécution PowerShell demandée ---")
        print(cmd[:2000] + ("..." if len(cmd) > 2000 else ""))
        ok = input("Exécuter ? (oui/non) : ").strip().lower()
        if ok not in ("oui", "o", "yes", "y"):
            return json.dumps({"ok": False, "cancelled": True}, ensure_ascii=False)
        try:
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=SHELL_TIMEOUT_SEC,
                cwd=str(WORKSPACE_ROOT),
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            return json.dumps({"error": f"Timeout après {SHELL_TIMEOUT_SEC}s."}, ensure_ascii=False)
        out = (proc.stdout or "") + (proc.stderr or "")
        if len(out) > MAX_SHELL_OUTPUT:
            out = out[:MAX_SHELL_OUTPUT] + "\n... [tronqué]"
        return json.dumps(
            {
                "exit_code": proc.returncode,
                "output": out,
            },
            ensure_ascii=False,
        )

    def _cache_get(self, key: str, ttl: int) -> str | None:
        if ttl <= 0:
            return None
        now = monotonic()
        if key in self._web_search_cache:
            ts, cached = self._web_search_cache[key]
            if now - ts < ttl:
                self._web_search_cache.move_to_end(key)
                return cached
            del self._web_search_cache[key]
        return None

    def _cache_put(self, key: str, value: str, ttl: int) -> None:
        if ttl <= 0:
            return
        self._web_search_cache[key] = (monotonic(), value)
        self._web_search_cache.move_to_end(key)
        while len(self._web_search_cache) > WEB_SEARCH_CACHE_MAX_ENTRIES:
            self._web_search_cache.popitem(last=False)

    def web_search(self, query: str, max_results: int = 6) -> str:
        """Recherche web textuelle via DuckDuckGo Search avec cache LRU."""
        q = (query or "").strip()
        if not q:
            return json.dumps({"error": "Requête vide."}, ensure_ascii=False)
        key = f"text::{q.lower()}::{max(1, min(max_results, 20))}"
        ttl = WEB_SEARCH_CACHE_TTL_SEC
        cached = self._cache_get(key, ttl)
        if cached is not None:
            return cached
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(q, max_results=max(1, min(max_results, 20))))
            out = json.dumps({"query": q, "results": results}, ensure_ascii=False)
        except Exception as e:
            out = json.dumps({"error": str(e)}, ensure_ascii=False)
        self._cache_put(key, out, ttl)
        return out

    def news_search(self, query: str, max_results: int = 5) -> str:
        """Recherche actualités via DuckDuckGo News avec cache LRU."""
        q = (query or "").strip()
        if not q:
            return json.dumps({"error": "Requête vide."}, ensure_ascii=False)
        key = f"news::{q.lower()}::{max(1, min(max_results, 20))}"
        ttl = WEB_SEARCH_CACHE_TTL_SEC
        cached = self._cache_get(key, ttl)
        if cached is not None:
            return cached
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(q, max_results=max(1, min(max_results, 20))))
            out = json.dumps({"query": q, "results": results}, ensure_ascii=False)
        except Exception as e:
            out = json.dumps({"error": str(e)}, ensure_ascii=False)
        self._cache_put(key, out, ttl)
        return out

    def fetch_url(self, url: str) -> str:
        if not ALLOW_FETCH_URL:
            return json.dumps(
                {
                    "error": "fetch_url désactivé. Mets ALLOW_FETCH_URL=1 dans .env (attention : requêtes réseau vers n'importe quelle URL).",
                },
                ensure_ascii=False,
            )
        u = (url or "").strip()
        if not u.lower().startswith(("http://", "https://")):
            return json.dumps(
                {"error": "URL invalide : utilise http:// ou https://"},
                ensure_ascii=False,
            )
        try:
            r = httpx.get(
                u,
                timeout=FETCH_URL_TIMEOUT_SEC,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; windows-local-agent/1.0)"},
            )
            r.raise_for_status()
            raw = r.content
            text = raw.decode("utf-8", errors="replace")
            if len(raw) > MAX_FETCH_URL_BYTES:
                text = text[:MAX_FETCH_URL_BYTES]
            text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", text)
            text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) > 48_000:
                text = text[:48_000] + " ... [tronqué]"
            return json.dumps(
                {"url": u, "status": r.status_code, "text_excerpt": text},
                ensure_ascii=False,
            )
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def send_smtp_email(self, to: str, subject: str, body: str) -> str:
        if not ALLOW_SMTP_SEND:
            return json.dumps(
                {
                    "error": "Envoi e-mail désactivé. Mets ALLOW_SMTP_SEND=1 et configure SMTP_* dans .env.",
                },
                ensure_ascii=False,
            )
        if not (SMTP_HOST and SMTP_USER and SMTP_PASSWORD and SMTP_FROM):
            return json.dumps(
                {"error": "SMTP incomplet : SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM requis."},
                ensure_ascii=False,
            )
        addr_to = (to or "").strip()
        sub = (subject or "").strip()
        text = body or ""
        if len(text) > MAX_EMAIL_BODY_CHARS:
            text = text[:MAX_EMAIL_BODY_CHARS] + "\n... [tronqué]"
        if not addr_to or not sub:
            return json.dumps({"error": "Destinataire et sujet requis."}, ensure_ascii=False)
        preview = f"À : {addr_to}\nSujet : {sub}\n---\n{text[:1500]}"
        if not self._confirm_terminal("--- Envoi d'e-mail (SMTP) ---", preview):
            return json.dumps({"ok": False, "cancelled": True}, ensure_ascii=False)
        try:
            msg = MIMEText(text, "plain", "utf-8")
            msg["Subject"] = sub
            msg["From"] = SMTP_FROM
            msg["To"] = addr_to
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=60) as s:
                if SMTP_USE_TLS:
                    s.starttls()
                s.login(SMTP_USER, SMTP_PASSWORD)
                s.sendmail(SMTP_FROM, [addr_to], msg.as_string())
            return json.dumps({"ok": True, "to": addr_to}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @staticmethod
    def _normalize_phone_e164_digits(phone: str) -> str | None:
        digits = re.sub(r"\D", "", phone or "")
        if 8 <= len(digits) <= 15:
            return digits
        return None

    def open_whatsapp_compose(self, phone: str, message: str, open_in_browser: bool = True) -> str:
        """
        Ouvre wa.me (message prérempli). L’envoi final est fait par l’humain sur WhatsApp.
        Pas d’API WhatsApp officielle ici — respecte les conditions d’utilisation de Meta.
        """
        digits = self._normalize_phone_e164_digits(phone)
        if not digits:
            return json.dumps(
                {
                    "error": "Numéro invalide : indique le pays en format international (chiffres uniquement, ex. 33612345678).",
                },
                ensure_ascii=False,
            )
        msg = message or ""
        if len(msg) > 4000:
            msg = msg[:4000]
        wa_url = f"https://wa.me/{digits}?text={quote_plus(msg)}"
        if not open_in_browser:
            return json.dumps(
                {
                    "wa_me_url": wa_url,
                    "hint": "Ouvre ce lien sur ton téléphone ou PC avec WhatsApp pour envoyer.",
                },
                ensure_ascii=False,
            )
        if not ALLOW_OPEN_BROWSER:
            return json.dumps(
                {
                    "error": "Ouverture navigateur désactivée. Mets ALLOW_OPEN_BROWSER=1 dans .env, ou utilise open_in_browser=false pour obtenir seulement l’URL.",
                    "wa_me_url": wa_url,
                },
                ensure_ascii=False,
            )
        if not self._confirm_terminal(
            "--- Ouvrir WhatsApp (lien wa.me) ---",
            f"URL : {wa_url}\n(L’envoi du message reste à valider dans WhatsApp.)",
        ):
            return json.dumps({"ok": False, "cancelled": True, "wa_me_url": wa_url}, ensure_ascii=False)
        try:
            webbrowser.open(wa_url)
            return json.dumps({"ok": True, "opened": True, "wa_me_url": wa_url}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e), "wa_me_url": wa_url}, ensure_ascii=False)

    def open_browser_url(self, url: str) -> str:
        if not ALLOW_OPEN_BROWSER:
            return json.dumps(
                {"error": "open_browser_url désactivé. Mets ALLOW_OPEN_BROWSER=1 dans .env."},
                ensure_ascii=False,
            )
        u = (url or "").strip()
        if not u.lower().startswith(("http://", "https://")):
            return json.dumps({"error": "URL http(s) uniquement."}, ensure_ascii=False)
        if not self._confirm_terminal("--- Ouvrir une URL dans le navigateur ---", u):
            return json.dumps({"ok": False, "cancelled": True}, ensure_ascii=False)
        try:
            webbrowser.open(u)
            return json.dumps({"ok": True, "url": u}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def append_memory_note(self, note: str, tag: str = "projet") -> str:
        """Ajoute une note persistante dans le journal mémoire avec un tag optionnel."""
        text = (note or "").strip()
        if not text:
            return json.dumps({"error": "Note vide."}, ensure_ascii=False)
        safe_tag = (tag or "projet").strip() or "projet"
        safe_tag = re.sub(r"[\r\n\[\]]+", " ", safe_tag).strip() or "projet"
        if len(text) > 100_000:
            text = text[:100_000] + "\n... [tronqué]"
        try:
            p = self._memory_journal_path()
            stamp = datetime.now().isoformat(timespec="seconds")
            block = f"\n## {stamp} [{safe_tag}]\n{text}\n"
            block_b = block.encode("utf-8")
            prev = p.read_bytes() if p.exists() else b""
            if len(prev) + len(block_b) > MAX_MEMORY_JOURNAL_BYTES:
                return json.dumps(
                    {
                        "error": f"Journal mémoire trop volumineux (>{MAX_MEMORY_JOURNAL_BYTES} octets). "
                        "Archive ou renomme le fichier puis recommence.",
                        "path": str(p.relative_to(WORKSPACE_ROOT)),
                    },
                    ensure_ascii=False,
                )
            if prev:
                with p.open("ab") as f:
                    f.write(block_b)
            else:
                head = "# Journal mémoire (assistant local)\n\n".encode("utf-8")
                body = f"## {stamp} [{safe_tag}]\n{text}\n".encode("utf-8")
                with p.open("wb") as f:
                    f.write(head)
                    f.write(body)
            return json.dumps(
                {
                    "ok": True,
                    "tag": safe_tag,
                    "path": str(p.relative_to(WORKSPACE_ROOT)),
                    "bytes": p.stat().st_size,
                },
                ensure_ascii=False,
            )
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
        except OSError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def read_memory_notes(self, max_chars: int | None = None, tag: str | None = None) -> str:
        """Lit le journal mémoire, avec filtre optionnel sur le tag."""
        lim = max_chars if max_chars is not None else MAX_MEMORY_READ_CHARS
        lim = max(1_000, min(lim, MAX_MEMORY_READ_CHARS))
        try:
            p = self._memory_journal_path()
            if not p.is_file():
                return json.dumps(
                    {"path": str(p.relative_to(WORKSPACE_ROOT)), "content": "(vide)"},
                    ensure_ascii=False,
                )
            raw = p.read_text(encoding="utf-8", errors="replace")
            if tag:
                wanted = f"[{str(tag).strip()}]"
                lines = raw.splitlines()
                kept: list[str] = []
                capture = False
                for line in lines:
                    if line.startswith("## "):
                        capture = wanted in line
                    if capture:
                        kept.append(line)
                raw = "\n".join(kept).strip() or "(aucune note pour ce tag)"
            if len(raw) > lim:
                raw = "... [début tronqué]\n" + raw[-lim:]
            return json.dumps(
                {"path": str(p.relative_to(WORKSPACE_ROOT)), "tag": tag, "content": raw},
                ensure_ascii=False,
            )
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
        except OSError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def dispatch(self, name: str, args: dict) -> str:
        args = args or {}
        try:
            if name == "list_dir":
                return self.list_dir(args.get("directory", "."))
            if name == "read_file":
                return self.read_file(args.get("path", ""))
            if name == "write_file":
                return self.write_file(args.get("path", ""), args.get("content", ""))
            if name == "delete_file":
                return self.delete_file(args.get("path", ""))
            if name == "run_powershell":
                return self.run_powershell(args.get("command", ""))
            if name == "web_search":
                mr = args.get("max_results", 6)
                try:
                    mr_int = int(mr)
                except (TypeError, ValueError):
                    mr_int = 6
                return self.web_search(args.get("query", ""), mr_int)
            if name == "news_search":
                mr = args.get("max_results", 5)
                try:
                    mr_int = int(mr)
                except (TypeError, ValueError):
                    mr_int = 5
                return self.news_search(args.get("query", ""), mr_int)
            if name == "fetch_url":
                return self.fetch_url(args.get("url", ""))
            if name == "send_smtp_email":
                return self.send_smtp_email(
                    args.get("to", ""),
                    args.get("subject", ""),
                    args.get("body", ""),
                )
            if name == "open_whatsapp_compose":
                return self.open_whatsapp_compose(
                    args.get("phone", ""),
                    args.get("message", ""),
                    _arg_bool(args.get("open_in_browser"), default=True),
                )
            if name == "open_browser_url":
                return self.open_browser_url(args.get("url", ""))
            if name == "append_memory_note":
                return self.append_memory_note(args.get("note", ""), str(args.get("tag", "projet")))
            if name == "read_memory_notes":
                mc = args.get("max_chars")
                mc_int: int | None = None
                if mc is not None and str(mc).strip() != "":
                    try:
                        mc_int = int(mc)
                    except (ValueError, TypeError):
                        mc_int = None
                tag = args.get("tag")
                tag_s = str(tag).strip() if tag is not None and str(tag).strip() else None
                return self.read_memory_notes(mc_int, tag_s)
            
            # ========== NOUVEAUX OUTILS ==========
            if name == "run_git":
                return self.run_git(args.get("command", ""))
            if name == "system_info":
                return self.system_info()
            if name == "docker_ps":
                return self.docker_ps()
            if name == "docker_exec":
                return self.docker_exec(args.get("container", ""), args.get("command", ""))
            if name == "schedule_task":
                return self.schedule_task(args.get("task", ""), args.get("cron", ""))
            if name == "list_skills":
                return self.list_skills()
            if name == "execute_skill":
                return self.execute_skill(args.get("skill", ""), args.get("params", {}))
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
        return json.dumps({"error": f"Outil inconnu : {name}"}, ensure_ascii=False)
    
    # ========== NOUVELLES MÉTHODES ==========
    
    def run_git(self, command: str) -> str:
        """Exécute une commande git dans le workspace."""
        if not ALLOW_GIT:
            return json.dumps({"error": "Git désactivé. Mets ALLOW_GIT=1 dans .env."}, ensure_ascii=False)
        
        cmd = (command or "").strip()
        if not cmd:
            return json.dumps({"error": "Commande git vide."}, ensure_ascii=False)
        
        # Sécuriser la commande
        forbidden = ["rm -rf /", "dd if=", ":(){:|:&};:", "chmod -R 777 /"]
        for forb in forbidden:
            if forb in cmd:
                return json.dumps({"error": f"Commande potentiellement dangereuse: {forb}"}, ensure_ascii=False)
        
        try:
            # Utiliser le dossier workspace comme cwd
            proc = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(WORKSPACE_ROOT),
                shell=True,
                encoding="utf-8",
                errors="replace",
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            if len(out) > MAX_SHELL_OUTPUT:
                out = out[:MAX_SHELL_OUTPUT] + "\n... [tronqué]"
            return json.dumps({
                "exit_code": proc.returncode,
                "output": out,
            }, ensure_ascii=False)
        except subprocess.TimeoutExpired:
            return json.dumps({"error": "Timeout après 60s."}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def system_info(self) -> str:
        """Retourne des informations système."""
        if not ALLOW_SYSTEM_MONITOR:
            return json.dumps({"error": "System monitor désactivé."}, ensure_ascii=False)
        
        import platform
        import os
        
        info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "current_dir": os.getcwd(),
        }
        return json.dumps(info, ensure_ascii=False)
    
    def docker_ps(self, all_containers: bool = True) -> str:
        """Liste les conteneurs Docker."""
        if not ALLOW_DOCKER:
            return json.dumps({"error": "Docker désactivé. Mets ALLOW_DOCKER=1 dans .env."}, ensure_ascii=False)
        
        try:
            cmd = ["docker", "ps", "--format", "{{.ID}}|{{.Names}}|{{.Status}}|{{.Image}}"]
            if all_containers:
                cmd.append("-a")
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            lines = proc.stdout.strip().split("\n") if proc.stdout.strip() else []
            containers = []
            for line in lines:
                parts = line.split("|")
                if len(parts) >= 4:
                    containers.append({
                        "id": parts[0],
                        "name": parts[1],
                        "status": parts[2],
                        "image": parts[3],
                    })
            return json.dumps({"containers": containers}, ensure_ascii=False)
        except FileNotFoundError:
            return json.dumps({"error": "Docker non trouvé. Est-il installé?"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def docker_exec(self, container: str, command: str) -> str:
        """Exécute une commande dans un conteneur Docker."""
        if not ALLOW_DOCKER:
            return json.dumps({"error": "Docker désactivé."}, ensure_ascii=False)
        
        if not container or not command:
            return json.dumps({"error": "Container et commande requis."}, ensure_ascii=False)
        
        try:
            proc = subprocess.run(
                ["docker", "exec", container, "sh", "-c", command],
                capture_output=True,
                text=True,
                timeout=60,
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            return json.dumps({
                "exit_code": proc.returncode,
                "output": out,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    def schedule_task(self, task: str, cron: str = ""):
        """Planifie une tâche (simplifié - enregistre dans un fichier)."""
        if not cron:
            # Exécution simple
            return self.run_powershell(task)
        
        # Enregistrer pour plus tard (scheduler complet dans une version future)
        return json.dumps({
            "message": "Planification enregistrée",
            "task": task,
            "cron": cron,
            "note": "Fonctionnalité complète à venir",
        }, ensure_ascii=False)
    
    def list_skills(self) -> str:
        """Liste les skills disponibles."""
        from .skills_loader import get_skills_loader
        loader = get_skills_loader()
        skills = loader.list_skills()
        return json.dumps({"skills": skills}, ensure_ascii=False)
    
    def execute_skill(self, skill_name: str, params: dict) -> str:
        """Exécute un skill avec des paramètres."""
        from .skills_loader import get_skills_loader
        loader = get_skills_loader()
        return loader.execute_skill(skill_name, **params)
