"""Code search and analysis tools."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


def search_code(pattern: str, path: str = ".", file_glob: str = "", max_results: int = 50) -> str:
    """Search for a regex pattern in files (like ripgrep / grep -rn)."""
    root = Path(path).resolve()
    if not root.exists():
        return json.dumps({"error": f"Path not found: {path}"})

    # try ripgrep first, fallback to grep
    for cmd_name in ("rg", "grep"):
        cmd = _build_search_cmd(cmd_name, pattern, str(root), file_glob, max_results)
        if cmd is None:
            continue
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, cwd=str(root)
            )
            if result.returncode <= 1:  # 0=found, 1=not found
                matches = _parse_search_output(result.stdout, max_results)
                return json.dumps({
                    "pattern": pattern,
                    "path": str(root),
                    "matches": matches,
                    "total": len(matches),
                })
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    # Python fallback
    return _python_search(pattern, root, file_glob, max_results)


def _build_search_cmd(
    tool: str, pattern: str, path: str, file_glob: str, max_results: int
) -> list[str] | None:
    if tool == "rg":
        cmd = ["rg", "--no-heading", "--line-number", "--color=never", "-m", str(max_results)]
        if file_glob:
            cmd += ["--glob", file_glob]
        cmd += [pattern, path]
        return cmd
    if tool == "grep":
        cmd = ["grep", "-rn", "--color=never"]
        if file_glob:
            cmd += ["--include", file_glob]
        cmd += [pattern, path]
        return cmd
    return None


def _parse_search_output(output: str, limit: int) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for line in output.strip().split("\n"):
        if not line:
            continue
        parts = line.split(":", 2)
        if len(parts) >= 3:
            matches.append({
                "file": parts[0],
                "line": int(parts[1]) if parts[1].isdigit() else 0,
                "text": parts[2].strip(),
            })
        if len(matches) >= limit:
            break
    return matches


def _python_search(pattern: str, root: Path, file_glob: str, max_results: int) -> str:
    SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
    regex = re.compile(pattern)
    matches: list[dict[str, Any]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for fname in filenames:
            if file_glob and not _glob_match(fname, file_glob):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if regex.search(line):
                            matches.append({
                                "file": fpath,
                                "line": i,
                                "text": line.strip()[:200],
                            })
                            if len(matches) >= max_results:
                                return json.dumps({
                                    "pattern": pattern,
                                    "path": str(root),
                                    "matches": matches,
                                    "total": len(matches),
                                    "truncated": True,
                                })
            except (PermissionError, OSError):
                continue
    return json.dumps({
        "pattern": pattern,
        "path": str(root),
        "matches": matches,
        "total": len(matches),
    })


def _glob_match(filename: str, pattern: str) -> bool:
    import fnmatch
    return fnmatch.fnmatch(filename, pattern)


def find_files(pattern: str, path: str = ".") -> str:
    """Find files by name glob pattern."""
    root = Path(path).resolve()
    if not root.is_dir():
        return json.dumps({"error": f"Not a directory: {path}"})

    SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
    results: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        import fnmatch
        for fname in fnmatch.filter(filenames, pattern):
            results.append(os.path.join(dirpath, fname))
            if len(results) >= 200:
                break

    return json.dumps({"pattern": pattern, "files": results, "total": len(results)})
