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

from .config import (
    ALLOW_FETCH_URL,
    ALLOW_OPEN_BROWSER,
    ALLOW_POWERSHELL,
    ALLOW_SMTP_SEND,
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
        rel = (relative_path or "").strip().replace("/", "\\")
        if not rel or rel.startswith("..") or Path(rel).is_absolute():
            raise ValueError(
                "Chemin invalide : utilise un chemin relatif au workspace, sans .. ni chemin absolu."
            )
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

    def web_search(self, query: str) -> str:
        q = (query or "").strip()
        if not q:
            return json.dumps({"error": "Requête vide."}, ensure_ascii=False)
        key = q.lower()
        ttl = WEB_SEARCH_CACHE_TTL_SEC
        if ttl > 0:
            now = monotonic()
            if key in self._web_search_cache:
                ts, cached = self._web_search_cache[key]
                if now - ts < ttl:
                    self._web_search_cache.move_to_end(key)
                    return cached
                del self._web_search_cache[key]
        url = f"https://api.duckduckgo.com/?q={quote_plus(q)}&format=json&no_html=1"
        try:
            r = httpx.get(url, timeout=15.0, follow_redirects=True)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
        abstract = (data.get("AbstractText") or "").strip()
        answer = (data.get("Answer") or "").strip()
        related = data.get("RelatedTopics") or []
        snippets: list[str] = []
        for item in related[:8]:
            if isinstance(item, dict) and item.get("Text"):
                snippets.append(str(item["Text"])[:300])
        out = json.dumps(
            {
                "query": q,
                "abstract": abstract,
                "answer": answer,
                "related_snippets": snippets,
            },
            ensure_ascii=False,
        )
        if ttl > 0:
            self._web_search_cache[key] = (monotonic(), out)
            self._web_search_cache.move_to_end(key)
            while len(self._web_search_cache) > WEB_SEARCH_CACHE_MAX_ENTRIES:
                self._web_search_cache.popitem(last=False)
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
            if len(raw) > MAX_FETCH_URL_BYTES:
                raw = raw[:MAX_FETCH_URL_BYTES]
            text = raw.decode("utf-8", errors="replace")
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

    def append_memory_note(self, note: str) -> str:
        """Mémoire persistante sur le disque (dossier workspace/memory)."""
        text = (note or "").strip()
        if not text:
            return json.dumps({"error": "Note vide."}, ensure_ascii=False)
        if len(text) > 100_000:
            text = text[:100_000] + "\n... [tronqué]"
        try:
            p = self._memory_journal_path()
            stamp = datetime.now().isoformat(timespec="seconds")
            block = f"\n## {stamp}\n{text}\n"
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
                body = f"## {stamp}\n{text}\n".encode("utf-8")
                with p.open("wb") as f:
                    f.write(head)
                    f.write(body)
            return json.dumps(
                {"ok": True, "path": str(p.relative_to(WORKSPACE_ROOT)), "bytes": p.stat().st_size},
                ensure_ascii=False,
            )
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
        except OSError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def read_memory_notes(self, max_chars: int | None = None) -> str:
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
            if len(raw) > lim:
                raw = "... [début tronqué]\n" + raw[-lim:]
            return json.dumps(
                {"path": str(p.relative_to(WORKSPACE_ROOT)), "content": raw},
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
                return self.web_search(args.get("query", ""))
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
                return self.append_memory_note(args.get("note", ""))
            if name == "read_memory_notes":
                mc = args.get("max_chars")
                mc_int: int | None = None
                if mc is not None and str(mc).strip() != "":
                    try:
                        mc_int = int(mc)
                    except (ValueError, TypeError):
                        mc_int = None
                return self.read_memory_notes(mc_int)
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
        return json.dumps({"error": f"Outil inconnu : {name}"}, ensure_ascii=False)
