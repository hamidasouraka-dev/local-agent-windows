"""File system tools — read, write, edit, tree."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MAX_READ_SIZE = 500_000  # ~500 KB


def read_file(path: str, offset: int = 0, limit: int = 0) -> str:
    """Read a file with optional line offset and limit."""
    p = Path(path).resolve()
    if not p.is_file():
        return json.dumps({"error": f"File not found: {path}"})
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return json.dumps({"error": str(e)})

    lines = content.split("\n")
    total = len(lines)
    if offset > 0:
        lines = lines[offset:]
    if limit > 0:
        lines = lines[:limit]

    text = "\n".join(lines)
    if len(text) > MAX_READ_SIZE:
        text = text[:MAX_READ_SIZE] + "\n... [truncated]"

    return json.dumps({
        "path": str(p),
        "total_lines": total,
        "showing": f"{offset + 1}-{offset + len(lines)}",
        "content": text,
    })


def write_file(path: str, content: str) -> str:
    """Create or overwrite a file."""
    p = Path(path).resolve()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return json.dumps({"ok": True, "path": str(p), "bytes": p.stat().st_size})
    except Exception as e:
        return json.dumps({"error": str(e)})


def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Surgical search-and-replace edit. old_string must appear exactly once."""
    p = Path(path).resolve()
    if not p.is_file():
        return json.dumps({"error": f"File not found: {path}"})
    try:
        content = p.read_text(encoding="utf-8")
    except Exception as e:
        return json.dumps({"error": str(e)})

    count = content.count(old_string)
    if count == 0:
        return json.dumps({
            "error": "old_string not found in file. Verify the exact text to replace.",
            "path": str(p),
        })
    if count > 1:
        return json.dumps({
            "error": f"old_string found {count} times. Provide more context to make it unique.",
            "path": str(p),
        })

    new_content = content.replace(old_string, new_string, 1)
    p.write_text(new_content, encoding="utf-8")
    return json.dumps({"ok": True, "path": str(p), "replacements": 1})


def create_directory(path: str) -> str:
    """Create a directory (and parents)."""
    p = Path(path).resolve()
    try:
        p.mkdir(parents=True, exist_ok=True)
        return json.dumps({"ok": True, "path": str(p)})
    except Exception as e:
        return json.dumps({"error": str(e)})


def list_directory(path: str = ".") -> str:
    """List files and directories."""
    p = Path(path).resolve()
    if not p.is_dir():
        return json.dumps({"error": f"Not a directory: {path}"})
    entries: list[dict[str, Any]] = []
    try:
        for item in sorted(p.iterdir()):
            entries.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
    except PermissionError:
        return json.dumps({"error": "Permission denied"})
    return json.dumps({"path": str(p), "entries": entries})


def tree(path: str = ".", max_depth: int = 3) -> str:
    """Display project tree structure."""
    root = Path(path).resolve()
    if not root.is_dir():
        return json.dumps({"error": f"Not a directory: {path}"})

    SKIP_DIRS = {
        ".git", "node_modules", "__pycache__", ".venv", "venv",
        ".tox", ".mypy_cache", ".pytest_cache", "dist", "build",
        ".next", ".nuxt", "target", ".idea", ".vscode",
    }
    lines: list[str] = [root.name + "/"]
    file_count = 0

    def _walk(directory: Path, prefix: str, depth: int) -> None:
        nonlocal file_count
        if depth > max_depth:
            return
        try:
            items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return
        dirs = [i for i in items if i.is_dir() and i.name not in SKIP_DIRS]
        files = [i for i in items if i.is_file() and not i.name.startswith(".")]
        entries = dirs + files
        for idx, entry in enumerate(entries):
            is_last = idx == len(entries) - 1
            connector = "--- " if is_last else "|-- "
            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                extension = "    " if is_last else "|   "
                _walk(entry, prefix + extension, depth + 1)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")
                file_count += 1

    _walk(root, "", 1)
    return "\n".join(lines) + f"\n\n({file_count} files)"
