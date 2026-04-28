"""Git integration tools."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ..config import ALLOW_GIT, WORKSPACE_ROOT

MAX_OUTPUT = 50_000


def _git(args: list[str], cwd: str = "") -> dict:
    if not ALLOW_GIT:
        return {"error": "Git disabled. Set SAISA_ALLOW_GIT=1"}
    work_dir = Path(cwd).resolve() if cwd else WORKSPACE_ROOT
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(work_dir),
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout[:MAX_OUTPUT],
            "stderr": result.stderr[:MAX_OUTPUT] if result.returncode != 0 else "",
        }
    except FileNotFoundError:
        return {"error": "git not found. Install git first."}
    except subprocess.TimeoutExpired:
        return {"error": "git command timed out"}
    except Exception as e:
        return {"error": str(e)}


def git_status(cwd: str = "") -> str:
    """Show git status."""
    return json.dumps(_git(["status", "--short"], cwd))


def git_diff(file: str = "", staged: bool = False, cwd: str = "") -> str:
    """Show git diff."""
    args = ["diff"]
    if staged:
        args.append("--staged")
    if file:
        args += ["--", file]
    return json.dumps(_git(args, cwd))


def git_log(max_count: int = 20, oneline: bool = True, cwd: str = "") -> str:
    """Show git log."""
    args = ["log", f"-{max_count}"]
    if oneline:
        args.append("--oneline")
    return json.dumps(_git(args, cwd))


def git_add(files: str = ".", cwd: str = "") -> str:
    """Stage files for commit."""
    return json.dumps(_git(["add", files], cwd))


def git_commit(message: str, cwd: str = "") -> str:
    """Create a commit."""
    return json.dumps(_git(["commit", "-m", message], cwd))


def git_branch(cwd: str = "") -> str:
    """List branches."""
    return json.dumps(_git(["branch", "-a"], cwd))


def git_checkout(branch: str, create: bool = False, cwd: str = "") -> str:
    """Switch or create a branch."""
    args = ["checkout"]
    if create:
        args.append("-b")
    args.append(branch)
    return json.dumps(_git(args, cwd))


def git_blame(file: str, cwd: str = "") -> str:
    """Show git blame for a file."""
    return json.dumps(_git(["blame", "--line-porcelain", file], cwd))
