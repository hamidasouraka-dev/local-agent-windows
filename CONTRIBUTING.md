# Contributing to SAISA

Thank you for your interest in contributing to SAISA! This guide will help you get started.

## Getting Started

### 1. Fork & Clone

```bash
gh repo fork hamidasouraka-dev/local-agent-windows --clone
cd local-agent-windows
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install with all dependencies
pip install -e ".[all]"

# Install dev tools
pip install ruff
```

### 3. Verify Setup

```bash
saisa --version
# → saisa, version 2.0.0

python -c "from saisa.tools.registry import ToolRegistry; print(f'{len(ToolRegistry().definitions)} tools')"
# → 27 tools
```

## Development Workflow

### Branch Naming

```
feature/description     # New features
fix/description         # Bug fixes
docs/description        # Documentation
refactor/description    # Code refactoring
```

### Code Quality

Before submitting, ensure:

```bash
# Lint
ruff check saisa/

# Auto-fix lint issues
ruff check saisa/ --fix

# Test imports
python -c "from saisa.agent import CodingAgent; print('OK')"
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new tool for Docker management
fix: handle connection timeout in Ollama provider
docs: update README with troubleshooting guide
refactor: simplify tool dispatch logic
```

## Project Structure

| Directory | Purpose |
|-----------|---------|
| `saisa/` | Main package |
| `saisa/providers/` | LLM provider implementations |
| `saisa/tools/` | Tool implementations |
| `saisa/ui/` | Terminal UI (Rich + prompt_toolkit) |
| `local_agent/` | Legacy v1 code |

## Adding a New Tool

1. Add the tool function in the appropriate file under `saisa/tools/`:

```python
# In saisa/tools/file_tools.py (example)
def my_new_tool(param1: str, param2: int = 10) -> str:
    """Brief description of what the tool does."""
    # Implementation
    return json.dumps({"ok": True, "result": "..."})
```

2. Register it in `saisa/tools/registry.py` inside `_build_catalog()`:

```python
_register(
    ToolDefinition(
        name="my_new_tool",
        description="Brief description for the LLM.",
        parameters={
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "..."},
                "param2": {"type": "integer", "description": "..."},
            },
            "required": ["param1"],
        },
    ),
    my_new_tool,
)
```

3. Run lint and test: `ruff check saisa/ && python -c "from saisa.tools.registry import ToolRegistry; print(len(ToolRegistry().definitions))"`

## Adding a New Provider

1. Create a new file in `saisa/providers/`:

```python
# saisa/providers/my_provider.py
from .base import LLMProvider, Message, ToolCall, ToolDefinition

class MyProvider(LLMProvider):
    def __init__(self, ...):
        ...

    @property
    def model_name(self) -> str:
        return f"myprovider/{self._model}"

    def close(self) -> None:
        ...

    def chat(self, messages, tools=None, *, stream=False) -> Message:
        ...

    def stream_chat(self, messages, tools=None):
        ...
```

2. Register in `saisa/providers/registry.py`
3. Add config vars in `saisa/config.py`
4. Add tier info in `saisa/tiers.py`

## Reporting Issues

When reporting bugs, include:
- Python version (`python --version`)
- OS (Windows/macOS/Linux)
- Provider being used
- Full error message
- Steps to reproduce

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers get started
- Credit others' work

---

**Thank you for contributing to SAISA!**

*Created by [Souraka HAMIDA](https://souraka.restafy.shop)*
