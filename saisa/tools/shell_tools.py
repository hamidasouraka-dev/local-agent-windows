"""Shell execution tools — cross-platform command runner."""

from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path

from ..config import ALLOW_SHELL, WORKSPACE_ROOT

MAX_OUTPUT = 50_000
DEFAULT_TIMEOUT = 60

DANGEROUS_PATTERNS = [
    "rm -rf /",
    "dd if=/dev/zero",
    "mkfs.",
    ":(){:|:&};:",
    "format c:",
    "del /f /s /q c:\\",
]


def run_command(command: str, cwd: str = "", timeout: int = DEFAULT_TIMEOUT) -> str:
    """Execute a shell command and return output."""
    if not ALLOW_SHELL:
        return json.dumps({"error": "Shell execution disabled. Set SAISA_ALLOW_SHELL=1"})

    if not command.strip():
        return json.dumps({"error": "Empty command"})

    cmd_lower = command.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern in cmd_lower:
            return json.dumps({"error": f"Dangerous command blocked: {pattern}"})

    work_dir = Path(cwd).resolve() if cwd else WORKSPACE_ROOT

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(work_dir),
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        stdout = result.stdout[:MAX_OUTPUT] if result.stdout else ""
        stderr = result.stderr[:MAX_OUTPUT] if result.stderr else ""
        return json.dumps({
            "exit_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "cwd": str(work_dir),
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Command timed out after {timeout}s", "command": command})
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_system_info() -> str:
    """Return basic system information."""
    return json.dumps({
        "os": platform.system(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cwd": str(Path.cwd()),
        "home": str(Path.home()),
    })
