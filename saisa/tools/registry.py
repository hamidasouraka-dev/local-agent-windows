"""Tool registry — maps tool names to implementations and definitions."""

from __future__ import annotations

import json
from typing import Any, Callable

from ..providers.base import ToolDefinition

# ── Tool Definition Catalog ──────────────────────────────────────────────

_TOOL_CATALOG: list[tuple[ToolDefinition, Callable[..., str]]] = []


def _register(definition: ToolDefinition, fn: Callable[..., str]) -> None:
    _TOOL_CATALOG.append((definition, fn))


def _build_catalog() -> None:
    """Lazily populate the catalog on first use."""
    if _TOOL_CATALOG:
        return

    from . import code_tools, file_tools, git_tools, project_tools, shell_tools

    # ── File tools ──
    _register(
        ToolDefinition(
            name="read_file",
            description="Read a file. Returns content with line numbers.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative file path."},
                    "offset": {"type": "integer", "description": "Start reading from this line (0-based). Default 0."},
                    "limit": {"type": "integer", "description": "Max lines to read. 0 = all."},
                },
                "required": ["path"],
            },
        ),
        file_tools.read_file,
    )

    _register(
        ToolDefinition(
            name="write_file",
            description="Create or overwrite a file with the given content.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write."},
                    "content": {"type": "string", "description": "File content."},
                },
                "required": ["path", "content"],
            },
        ),
        file_tools.write_file,
    )

    _register(
        ToolDefinition(
            name="edit_file",
            description=(
                "Surgical search-and-replace in a file. "
                "old_string must appear exactly once. Provide enough context to make it unique."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File to edit."},
                    "old_string": {"type": "string", "description": "Exact text to find (must be unique)."},
                    "new_string": {"type": "string", "description": "Replacement text."},
                },
                "required": ["path", "old_string", "new_string"],
            },
        ),
        file_tools.edit_file,
    )

    _register(
        ToolDefinition(
            name="list_directory",
            description="List files and directories at a path.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path. Default: current dir."},
                },
            },
        ),
        file_tools.list_directory,
    )

    _register(
        ToolDefinition(
            name="tree",
            description="Show project directory tree structure.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Root directory. Default: current dir."},
                    "max_depth": {"type": "integer", "description": "Max depth to traverse. Default 3."},
                },
            },
        ),
        file_tools.tree,
    )

    _register(
        ToolDefinition(
            name="create_directory",
            description="Create a directory and all parent directories.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to create."},
                },
                "required": ["path"],
            },
        ),
        file_tools.create_directory,
    )

    # ── Code search tools ──
    _register(
        ToolDefinition(
            name="search_code",
            description="Search for a regex pattern in code files (like ripgrep).",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regex pattern to search."},
                    "path": {"type": "string", "description": "Directory to search in. Default: current dir."},
                    "file_glob": {"type": "string", "description": "File glob filter, e.g. '*.py'."},
                    "max_results": {"type": "integer", "description": "Max results. Default 50."},
                },
                "required": ["pattern"],
            },
        ),
        code_tools.search_code,
    )

    _register(
        ToolDefinition(
            name="find_files",
            description="Find files by name pattern (glob).",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern, e.g. '*.py' or 'test_*.js'."},
                    "path": {"type": "string", "description": "Directory to search in."},
                },
                "required": ["pattern"],
            },
        ),
        code_tools.find_files,
    )

    # ── Shell tools ──
    _register(
        ToolDefinition(
            name="run_command",
            description=(
                "Execute a shell command. Returns stdout, stderr, and exit code. "
                "Use for: running tests, installing packages, building projects, etc."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute."},
                    "cwd": {"type": "string", "description": "Working directory. Default: project root."},
                    "timeout": {"type": "integer", "description": "Timeout in seconds. Default 60."},
                },
                "required": ["command"],
            },
        ),
        shell_tools.run_command,
    )

    _register(
        ToolDefinition(
            name="get_system_info",
            description="Get OS, Python version, and system information.",
            parameters={"type": "object", "properties": {}},
        ),
        shell_tools.get_system_info,
    )

    # ── Git tools ──
    _register(
        ToolDefinition(
            name="git_status",
            description="Show git status (modified/staged files).",
            parameters={
                "type": "object",
                "properties": {
                    "cwd": {"type": "string", "description": "Repository path."},
                },
            },
        ),
        git_tools.git_status,
    )

    _register(
        ToolDefinition(
            name="git_diff",
            description="Show git diff (unstaged or staged changes).",
            parameters={
                "type": "object",
                "properties": {
                    "file": {"type": "string", "description": "Specific file to diff."},
                    "staged": {"type": "boolean", "description": "Show staged changes."},
                    "cwd": {"type": "string", "description": "Repository path."},
                },
            },
        ),
        git_tools.git_diff,
    )

    _register(
        ToolDefinition(
            name="git_log",
            description="Show recent git commits.",
            parameters={
                "type": "object",
                "properties": {
                    "max_count": {"type": "integer", "description": "Number of commits. Default 20."},
                    "oneline": {"type": "boolean", "description": "One-line format. Default true."},
                    "cwd": {"type": "string", "description": "Repository path."},
                },
            },
        ),
        git_tools.git_log,
    )

    _register(
        ToolDefinition(
            name="git_add",
            description="Stage files for git commit.",
            parameters={
                "type": "object",
                "properties": {
                    "files": {"type": "string", "description": "Files to stage. Default: all."},
                    "cwd": {"type": "string", "description": "Repository path."},
                },
            },
        ),
        git_tools.git_add,
    )

    _register(
        ToolDefinition(
            name="git_commit",
            description="Create a git commit with a message.",
            parameters={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Commit message."},
                    "cwd": {"type": "string", "description": "Repository path."},
                },
                "required": ["message"],
            },
        ),
        git_tools.git_commit,
    )

    _register(
        ToolDefinition(
            name="git_branch",
            description="List all git branches.",
            parameters={
                "type": "object",
                "properties": {
                    "cwd": {"type": "string", "description": "Repository path."},
                },
            },
        ),
        git_tools.git_branch,
    )

    _register(
        ToolDefinition(
            name="git_checkout",
            description="Switch to or create a git branch.",
            parameters={
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "description": "Branch name."},
                    "create": {"type": "boolean", "description": "Create new branch."},
                    "cwd": {"type": "string", "description": "Repository path."},
                },
                "required": ["branch"],
            },
        ),
        git_tools.git_checkout,
    )

    # ── Project tools ──
    _register(
        ToolDefinition(
            name="scaffold_project",
            description=(
                "Generate a full project from a template. "
                "Available templates: python-fastapi, python-cli, react-vite, node-express."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Project name."},
                    "template": {"type": "string", "description": "Template name (python-fastapi, python-cli, react-vite, node-express)."},
                    "path": {"type": "string", "description": "Parent directory. Default: current dir."},
                },
                "required": ["name", "template"],
            },
        ),
        project_tools.scaffold_project,
    )

    _register(
        ToolDefinition(
            name="list_templates",
            description="List available project scaffolding templates.",
            parameters={"type": "object", "properties": {}},
        ),
        project_tools.list_templates,
    )

    _register(
        ToolDefinition(
            name="detect_project",
            description="Auto-detect project stack, frameworks, package manager, and configuration.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Project directory to analyze."},
                },
            },
        ),
        project_tools.detect_project_context,
    )

    # ── Memory tools ──
    from ..memory import Memory as _Mem

    _mem = _Mem()

    def _memory_store(category: str, content: str, tags: str = "") -> str:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        entry_id = _mem.store(category, content, tag_list)
        return json.dumps({"ok": True, "id": entry_id, "total": _mem.count})

    def _memory_recall(query: str, top_k: int = 5, category: str = "") -> str:
        results = _mem.recall(query, top_k, category or None)
        return json.dumps({
            "results": [
                {"id": r.id, "category": r.category, "content": r.content[:500], "tags": r.tags, "score": round(r.relevance_score, 3)}
                for r in results
            ],
            "total": len(results),
        })

    def _memory_stats() -> str:
        return json.dumps(_mem.stats())

    _register(
        ToolDefinition(
            name="memory_store",
            description="Store a learning, context, or preference in persistent memory.",
            parameters={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Category: learning, context, preference, error, success."},
                    "content": {"type": "string", "description": "Content to remember."},
                    "tags": {"type": "string", "description": "Comma-separated tags for retrieval."},
                },
                "required": ["category", "content"],
            },
        ),
        _memory_store,
    )

    _register(
        ToolDefinition(
            name="memory_recall",
            description="Retrieve relevant memories by query. Uses similarity search.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."},
                    "top_k": {"type": "integer", "description": "Max results. Default 5."},
                    "category": {"type": "string", "description": "Filter by category."},
                },
                "required": ["query"],
            },
        ),
        _memory_recall,
    )

    _register(
        ToolDefinition(
            name="memory_stats",
            description="Show memory statistics (entries, categories).",
            parameters={"type": "object", "properties": {}},
        ),
        _memory_stats,
    )

    # ── SaaS Generator ──
    from . import saas_templates

    _register(
        ToolDefinition(
            name="generate_saas",
            description=(
                "Generate a full SaaS project with auth, user management, payments, "
                "dashboard API, and database. Stacks: fastapi, express."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Project name."},
                    "stack": {"type": "string", "description": "Stack: fastapi or express."},
                    "path": {"type": "string", "description": "Parent directory."},
                },
                "required": ["name", "stack"],
            },
        ),
        saas_templates.generate_saas,
    )

    _register(
        ToolDefinition(
            name="list_saas_templates",
            description="List available SaaS project templates with features.",
            parameters={"type": "object", "properties": {}},
        ),
        saas_templates.list_saas_templates,
    )

    # ── Tier info ──
    from ..tiers import list_tiers_json, recommend_tier

    def _list_tiers() -> str:
        return list_tiers_json()

    def _recommend_tier(budget: str = "free", priority: str = "balanced") -> str:
        tier = recommend_tier(budget, priority)
        return json.dumps({
            "recommended": tier.name,
            "provider": tier.provider,
            "cost": tier.cost,
            "description": tier.description,
        })

    _register(
        ToolDefinition(
            name="list_tiers",
            description="List all available LLM provider tiers (free local to premium cloud).",
            parameters={"type": "object", "properties": {}},
        ),
        _list_tiers,
    )

    _register(
        ToolDefinition(
            name="recommend_tier",
            description="Recommend the best LLM provider tier based on budget and priority.",
            parameters={
                "type": "object",
                "properties": {
                    "budget": {"type": "string", "description": "Budget: free, low, unlimited."},
                    "priority": {"type": "string", "description": "Priority: speed, quality, balanced, privacy."},
                },
            },
        ),
        _recommend_tier,
    )


# ── Public API ───────────────────────────────────────────────────────────


class ToolRegistry:
    """Lookup tool definitions and dispatch calls."""

    def __init__(self) -> None:
        _build_catalog()
        self._definitions = {td.name: td for td, _ in _TOOL_CATALOG}
        self._handlers: dict[str, Callable[..., str]] = {td.name: fn for td, fn in _TOOL_CATALOG}

    @property
    def definitions(self) -> list[ToolDefinition]:
        return list(self._definitions.values())

    def dispatch(self, name: str, arguments: dict[str, Any]) -> str:
        handler = self._handlers.get(name)
        if handler is None:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            return handler(**arguments)
        except TypeError as e:
            return json.dumps({"error": f"Invalid arguments for {name}: {e}"})
        except Exception as e:
            return json.dumps({"error": f"Tool {name} failed: {e}"})


def get_all_tool_definitions() -> list[ToolDefinition]:
    _build_catalog()
    return [td for td, _ in _TOOL_CATALOG]


def dispatch_tool(name: str, arguments: dict[str, Any]) -> str:
    _build_catalog()
    for td, fn in _TOOL_CATALOG:
        if td.name == name:
            try:
                return fn(**arguments)
            except Exception as e:
                return json.dumps({"error": f"Tool {name} failed: {e}"})
    return json.dumps({"error": f"Unknown tool: {name}"})
