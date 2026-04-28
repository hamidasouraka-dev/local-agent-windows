# SAISA v2 - Coding Agent

> A powerful terminal-based AI coding agent inspired by Claude Code. Your AI pair-programmer that lives in the terminal.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Ollama-Local-orange?logo=llama" alt="Ollama">
  <img src="https://img.shields.io/badge/Groq-Cloud-purple" alt="Groq">
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o-black?logo=openai" alt="OpenAI">
  <img src="https://img.shields.io/badge/Anthropic-Claude-blue" alt="Anthropic">
</p>

## What is SAISA?

SAISA (Super AI Self-Autonomous) is a **terminal-based coding agent** that reads, writes, edits, searches, and runs code directly on your machine. Think Claude Code or Cursor — but open-source and multi-provider.

### Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Provider** | Ollama (local), Groq, OpenAI, Anthropic — switch with one flag |
| **Surgical Edits** | `edit_file` with search-and-replace — no full rewrites |
| **Code Search** | Regex search across files (ripgrep-powered) |
| **Shell Execution** | Run any command, see stdout/stderr/exit code |
| **Git Integration** | status, diff, log, add, commit, branch, checkout |
| **Rich Terminal UI** | Syntax highlighting, Markdown rendering, streaming |
| **Session Management** | Save/load conversations across sessions |
| **Project Awareness** | Tree view, file discovery, project structure analysis |
| **Streaming** | Real-time token streaming from all providers |
| **Cross-Platform** | Works on Windows, macOS, and Linux |

## Architecture v2

```
saisa/
|-- __init__.py          # Package root
|-- config.py            # Centralised configuration
|-- agent.py             # Core agent with agentic tool loop
|-- prompts.py           # Coding-optimised system prompts
|-- session.py           # Session save/load
|-- cli.py               # Rich CLI entry point (Click)
|-- providers/
|   |-- base.py          # Abstract LLM interface
|   |-- registry.py      # Provider factory
|   |-- ollama.py        # Ollama (local)
|   |-- groq_provider.py # Groq (cloud)
|   |-- openai_provider.py # OpenAI
|   |-- anthropic_provider.py # Anthropic
|-- tools/
|   |-- registry.py      # Tool catalog & dispatch
|   |-- file_tools.py    # read, write, edit, tree, list
|   |-- code_tools.py    # search_code, find_files
|   |-- shell_tools.py   # run_command, system_info
|   |-- git_tools.py     # Full git operations
|-- ui/
|   |-- console.py       # Rich output (panels, markdown, syntax)
|   |-- input.py         # prompt_toolkit input with history
```

## Quick Start

### 1. Install

```bash
git clone https://github.com/Souraka229/local-agent-windows.git
cd local-agent-windows

# Install with pip (recommended)
pip install -e ".[all]"

# Or just core dependencies
pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your preferred provider and API keys
```

### 3. Run

```bash
# With Ollama (local, default)
ollama pull llama3.2
saisa

# With Groq (fast cloud)
saisa --provider groq

# With OpenAI
saisa --provider openai

# With Anthropic
saisa --provider anthropic

# Single command mode
saisa --run "explain the code in main.py"

# Specify model
saisa --provider ollama --model codellama
```

## Usage Examples

```
You > Read the file src/app.py and add error handling to the main function

  > read_file(src/app.py)
  Read src/app.py (45 lines)
  > edit_file(src/app.py)
  edit_file: src/app.py

I've added try/except blocks around the main function...
```

```
You > Find all TODO comments in the project

  > search_code(TODO)
  12 matches

Found 12 TODOs across 8 files:
- src/utils.py:23 — TODO: add input validation
- ...
```

```
You > Run the tests and fix any failures

  > run_command(python -m pytest tests/ -v)
  exit 1
  > read_file(tests/test_auth.py)
  ...
  > edit_file(src/auth.py)
  ...
  > run_command(python -m pytest tests/ -v)
  exit 0

All 24 tests pass now. Fixed the auth token validation.
```

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/new` | Clear conversation history |
| `/model <name>` | Switch model |
| `/save [name]` | Save session |
| `/sessions` | List saved sessions |
| `/load <id>` | Load a session |
| `/status` | Show configuration |
| `/tree [path]` | Show project tree |
| `/diff` | Show git diff |
| `/context [path]` | Auto-detect project stack and frameworks |
| `/swarm <task>` | Run multi-agent swarm (architect+developer+security) |
| `/memory` | Show persistent memory stats |
| `/quit` | Exit |

## Advanced Features

### Multi-Agent Swarm
Run multiple specialized agents on a task. Each agent builds on the previous output:

```bash
/swarm "Design a user authentication system with JWT"
```

Agents: **Architect** (system design) -> **Developer** (implementation) -> **Security** (review)

Available agents: `developer`, `devops`, `security`, `architect`, `reviewer`

### Project Scaffolding
Generate full projects from templates:

```
You > Create a new FastAPI project called my-api
  > scaffold_project(my-api, python-fastapi)

Templates: python-fastapi, python-cli, react-vite, node-express
```

### Persistent Memory
SAISA remembers across sessions — learnings, preferences, project context:

```
You > Remember that this project uses PostgreSQL 16
  > memory_store(context, "Project uses PostgreSQL 16", ["database", "postgres"])

You > What database do we use?
  > memory_recall("database")
```

### Project Context Detection
Auto-detect stack, frameworks, and configuration:

```
/context .
→ stack: [python], frameworks: [FastAPI], has_docker: true, has_ci: true
```

### Autonomous Mode (Autopilot)
Let SAISA handle complex tasks end-to-end: **plan -> execute -> verify**

```bash
/autopilot Create a full REST API with user authentication using FastAPI and JWT
```

SAISA will:
1. Break the task into concrete steps
2. Execute each step autonomously (create files, install deps, write tests)
3. Verify the results

Works with any LLM provider. The better the model, the better the autonomy.

### SaaS Generator
Generate full production-ready SaaS projects with one command:

```bash
/saas my-startup fastapi
```

Generates 19+ files with:
- JWT authentication (register, login)
- User management with roles
- Admin dashboard API
- Stripe payment integration
- Database models (SQLite/PostgreSQL)
- Docker + docker-compose
- Tests

Also available as Express+TypeScript.

### User Management & API Key Vault
Multi-user support with secure API key storage:

```bash
/register admin mypassword admin     # Create admin account
/login admin mypassword               # Login
/addkey groq gsk_xxxx                 # Store API key securely
/keys                                 # List stored keys
```

API keys auto-load on login — switch providers seamlessly.

### Provider Tiers
```bash
/tiers
```

| Tier | Provider | Cost | Speed | Quality |
|------|----------|------|-------|---------|
| Free (Local) | Ollama | Free forever | Hardware-dependent | Good (7B-70B) |
| Turbo | Groq | Free tier / Pay | ~500 tok/s | Excellent |
| Premium | OpenAI | Pay per token | Fast | Top tier |
| Elite | Anthropic | Pay per token | Fast | Top tier |

### Turbo Mode
Built-in response caching and connection pooling for blazing fast inference.
No extra config needed — always on.

## Configuration (.env)

```env
# Provider: ollama (default), groq, openai, anthropic
SAISA_PROVIDER=ollama

# Ollama (local)
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2

# Groq (cloud - fast)
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o

# Anthropic
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Agent settings
SAISA_TEMPERATURE=0.3
SAISA_MAX_TOOL_ROUNDS=30
SAISA_STREAMING=1
SAISA_ALLOW_SHELL=1
SAISA_ALLOW_GIT=1
SAISA_NAME=SAISA
SAISA_OWNER=YourName
```

## Legacy v1

The original SAISA v1 agent is still available in the `local_agent/`, `brain/`, `agents/`, `tools/`, `memory/`, and `sandbox/` directories. It supports Ollama and Groq with features like autopilot mode, browser automation, and SQLite memory. Run it with `python main.py`.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Made with passion by [@Souraka229](https://github.com/Souraka229)
