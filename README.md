<div align="center">

# SAISA v2

### Super AI Self-Autonomous Coding Agent

> Open-source, local-first, multi-provider terminal coding agent.
> Like Claude Code and Cursor — but yours.

<p>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Open_Source-100%25-orange?style=for-the-badge&logo=opensourceinitiative" alt="Open Source">
  <img src="https://img.shields.io/badge/Local_First-Ollama-ff6b35?style=for-the-badge" alt="Local First">
</p>

<p>
  <img src="https://img.shields.io/badge/Ollama-Local-E34F26?style=flat-square&logo=llama" alt="Ollama">
  <img src="https://img.shields.io/badge/Groq-Turbo-7C3AED?style=flat-square" alt="Groq">
  <img src="https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=flat-square&logo=openai" alt="OpenAI">
  <img src="https://img.shields.io/badge/Anthropic-Claude-D4A574?style=flat-square" alt="Anthropic">
</p>

**Created by [Souraka HAMIDA](https://souraka.restafy.shop) — [@Souraka229](https://github.com/Souraka229)**

---

[Installation](#-installation) · [Quick Start](#-quick-start) · [Features](#-features) · [Architecture](#-architecture) · [Guide](#-complete-guide) · [Vision 2030](#-vision-saisa-2030)

</div>

---

## What is SAISA?

SAISA is a **terminal-based autonomous coding agent** that reads, writes, edits, searches, and runs code directly on your machine. It can handle **entire projects** — from scaffolding to deployment.

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   You  ───────►  SAISA  ───────►  Your Code            │
│                    │                                    │
│              ┌─────┼─────┐                              │
│              │     │     │                              │
│              ▼     ▼     ▼                              │
│           Read   Edit   Run     Search   Git   Build   │
│           Files  Code   Shell   Code     Ops   Deploy  │
│                                                         │
│   Powered by: Ollama | Groq | OpenAI | Anthropic       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Why SAISA?

| vs | SAISA Advantage |
|----|-----------------|
| **ChatGPT** | SAISA runs code directly on your machine, not in a sandbox |
| **Cursor** | SAISA is open-source, free, and works in the terminal |
| **Claude Code** | SAISA supports 4 providers, works 100% locally with Ollama |
| **GitHub Copilot** | SAISA doesn't just suggest — it executes, tests, and commits |

---

## Features

```
┌────────────────────────────────────────────────────────────────┐
│                    SAISA v2 Feature Map                        │
├────────────────┬───────────────────────────────────────────────┤
│  27 Tools      │  read, write, edit, search, shell, git...    │
│  4 Providers   │  Ollama, Groq, OpenAI, Anthropic             │
│  5 Agents      │  Developer, DevOps, Security, Architect...   │
│  Autopilot     │  Plan → Execute → Verify (autonomous)        │
│  SaaS Gen      │  Full projects: auth, payments, dashboard    │
│  Memory        │  Persistent learning across sessions         │
│  Users         │  Register, login, roles, API key vault       │
│  4 Tiers       │  Free (local) → Turbo → Premium → Elite     │
│  Turbo Mode    │  Response cache + connection pooling         │
│  Rich UI       │  Syntax highlighting, markdown, streaming    │
└────────────────┴───────────────────────────────────────────────┘
```

### Provider Tiers

```
  FREE ──────── TURBO ──────── PREMIUM ──────── ELITE
   │              │               │                │
   ▼              ▼               ▼                ▼
 Ollama         Groq           OpenAI          Anthropic
 (Local)       (Cloud)         (Cloud)          (Cloud)
   │              │               │                │
   │  Free        │  ~500tok/s    │  GPT-4o        │  Claude
   │  Private     │  Free tier    │  Top tier      │  Top tier
   │  7B-70B      │  70B models   │  Pay/token     │  Pay/token
   │              │               │                │
   ▼              ▼               ▼                ▼
 No key        GROQ_API_KEY   OPENAI_API_KEY   ANTHROPIC_API_KEY
 needed        (free signup)
```

### All 27 Tools

```
┌─────────── FILE OPS ───────────┐  ┌─────── CODE INTEL ────────┐
│  read_file      write_file     │  │  search_code  find_files  │
│  edit_file      list_directory │  │  detect_project            │
│  tree           create_directory│  └────────────────────────────┘
└────────────────────────────────┘
┌─────────── EXECUTION ──────────┐  ┌──────── GIT OPS ──────────┐
│  run_command    get_system_info│  │  git_status   git_diff    │
└────────────────────────────────┘  │  git_log      git_add     │
                                    │  git_commit   git_branch  │
┌─────────── PROJECT GEN ────────┐  │  git_checkout              │
│  scaffold_project              │  └────────────────────────────┘
│  list_templates                │
│  generate_saas                 │  ┌──────── MEMORY ────────────┐
│  list_saas_templates           │  │  memory_store              │
└────────────────────────────────┘  │  memory_recall             │
                                    │  memory_stats              │
┌─────────── TIER INFO ──────────┐  └────────────────────────────┘
│  list_tiers    recommend_tier  │
└────────────────────────────────┘
```

---

## Installation

### Prerequisites

- **Python 3.10+**
- **Ollama** (optional, for local/free usage): https://ollama.com

### Step 1: Clone

```bash
git clone https://github.com/hamidasouraka-dev/local-agent-windows.git
cd local-agent-windows
```

### Step 2: Install

```bash
# Recommended: install with all optional providers
pip install -e ".[all]"

# Or minimal install (Ollama + Groq only, no openai/anthropic SDK)
pip install -e .
```

### Step 3: Configure

```bash
cp .env.example .env
# Edit .env with your settings (optional — works out of the box with Ollama)
```

### Step 4: Pull a model (if using Ollama)

```bash
ollama pull llama3.2
# Or for coding: ollama pull qwen2.5-coder
# Or for power: ollama pull deepseek-coder-v2
```

### Step 5: Run

```bash
saisa
```

### Verify Installation

```bash
saisa --version
# → saisa, version 2.0.0

python -c "from saisa.tools.registry import ToolRegistry; print(f'{len(ToolRegistry().definitions)} tools')"
# → 27 tools
```

---

## Quick Start

### Basic Usage

```bash
# Interactive mode (default)
saisa

# With a specific provider
saisa --provider groq
saisa --provider openai
saisa --provider anthropic

# With a specific model
saisa --provider ollama --model codellama
saisa --provider groq --model llama-3.1-8b-instant

# Single command mode (no REPL)
saisa --run "explain the code in main.py"
saisa --run "find all TODO comments and fix them"

# Disable streaming
saisa --no-stream
```

### Example Sessions

**Reading and editing code:**
```
You > Read src/app.py and add error handling to the main function

  > read_file(src/app.py)
  Read src/app.py (45 lines)
  > edit_file(src/app.py, old_string="def main():", new_string="def main():\n    try:")
  Edited src/app.py

I've added try/except blocks around the main function with proper error logging.
```

**Finding and fixing bugs:**
```
You > Run the tests and fix any failures

  > run_command(python -m pytest tests/ -v)
  2 failed, 22 passed
  > read_file(tests/test_auth.py)
  > edit_file(src/auth.py, ...)
  > run_command(python -m pytest tests/ -v)
  24 passed

All 24 tests pass now. Fixed the auth token validation.
```

**Generating a full project:**
```
You > /saas my-startup fastapi

SaaS project created! /home/user/my-startup
  Stack: fastapi
  Files: 19
  - JWT Authentication
  - User registration & login
  - Role-based access control
  - Stripe payment stubs
  - Docker + docker-compose
  - Tests
```

---

## Complete Guide

### All Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show all commands | `/help` |
| `/new` | Clear conversation | `/new` |
| `/model <name>` | Switch model | `/model codellama` |
| `/save [name]` | Save session | `/save my-project` |
| `/sessions` | List saved sessions | `/sessions` |
| `/load <id>` | Load a session | `/load abc123` |
| `/status` | Show configuration | `/status` |
| `/tree [path]` | Show project tree | `/tree src/` |
| `/diff` | Show git changes | `/diff` |
| `/context [path]` | Detect project stack | `/context .` |
| `/swarm <task>` | Multi-agent swarm | `/swarm "design auth system"` |
| `/memory` | Memory stats | `/memory` |
| `/autopilot <task>` | Autonomous execution | `/autopilot "build a REST API"` |
| `/saas <name> [stack]` | Generate SaaS project | `/saas my-app fastapi` |
| `/tiers` | Show provider tiers | `/tiers` |
| `/register <user> <pass> [role]` | Create account | `/register admin pass123 admin` |
| `/login <user> <pass>` | Login | `/login admin pass123` |
| `/addkey <provider> <key>` | Store API key | `/addkey groq gsk_xxx` |
| `/keys` | List stored keys | `/keys` |
| `/quit` | Exit SAISA | `/quit` |

### Multi-Agent Swarm

Run multiple specialized agents on a single task. Each agent builds on the previous output:

```
/swarm "Design a user authentication system with JWT"
```

```
┌──────────┐    ┌───────────┐    ┌──────────┐
│ Architect │───►│ Developer │───►│ Security │
│           │    │           │    │          │
│ System    │    │ Code      │    │ Vuln     │
│ design    │    │ implement │    │ review   │
└──────────┘    └───────────┘    └──────────┘
```

**Available agents:**

| Agent | Specialty |
|-------|-----------|
| `developer` | Code generation, debugging, testing |
| `devops` | Docker, CI/CD, infrastructure |
| `security` | Vulnerability scanning, security review |
| `architect` | System design, technology selection |
| `reviewer` | Code review, quality assurance |

### Autopilot Mode

Let SAISA handle complex tasks end-to-end with a 3-phase approach:

```
┌─────────┐    ┌─────────┐    ┌─────────┐
│  PLAN   │───►│ EXECUTE │───►│ VERIFY  │
│         │    │         │    │         │
│ Break   │    │ Run     │    │ Check   │
│ task    │    │ each    │    │ results │
│ into    │    │ step    │    │ and     │
│ steps   │    │ with    │    │ report  │
│         │    │ tools   │    │         │
└─────────┘    └─────────┘    └─────────┘
```

```bash
/autopilot Create a full REST API with user authentication using FastAPI and JWT
```

SAISA will:
1. Plan concrete steps (e.g., "create models", "add auth routes", "write tests")
2. Execute each step autonomously using all 27 tools
3. Verify results and report issues

### SaaS Generator

Generate full production-ready SaaS projects:

```bash
/saas my-startup fastapi     # Python FastAPI SaaS
/saas my-startup express     # Node.js Express SaaS
```

**What you get (FastAPI):**

```
my-startup/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app with CORS
│   ├── config.py            # Environment configuration
│   ├── database.py          # SQLAlchemy setup
│   ├── models.py            # User + APIKey models
│   ├── auth.py              # JWT + bcrypt utilities
│   └── routes/
│       ├── auth.py          # Register + Login
│       ├── users.py         # Profile + Preferences
│       ├── admin.py         # User management + Stats
│       └── payments.py      # Stripe checkout stubs
├── tests/
│   └── test_auth.py         # Auth integration tests
├── Dockerfile               # Production Docker image
├── docker-compose.yml       # Dev environment
├── requirements.txt         # Python dependencies
├── .env.example             # Config template
├── .gitignore
└── README.md                # Project documentation
```

**Features included:**
- JWT authentication (register, login, token refresh)
- User management with roles (user, admin, premium)
- Admin dashboard API (stats, user list)
- Stripe payment integration (checkout stubs)
- Database models (SQLite/PostgreSQL via SQLAlchemy)
- Docker + docker-compose
- Tests with pytest

### Project Scaffolding

For simpler projects, use the scaffolding tool:

| Template | Description | Command |
|----------|-------------|---------|
| `python-fastapi` | FastAPI REST API | `scaffold_project(name, python-fastapi)` |
| `python-cli` | Click CLI app | `scaffold_project(name, python-cli)` |
| `react-vite` | React + TypeScript + Vite | `scaffold_project(name, react-vite)` |
| `node-express` | Express + TypeScript | `scaffold_project(name, node-express)` |

### Persistent Memory

SAISA remembers across sessions:

```
You > Remember that this project uses PostgreSQL 16 with pgvector
  → memory_store(context, "Project uses PostgreSQL 16 with pgvector")

You > What database setup do we use?
  → memory_recall("database") → "Project uses PostgreSQL 16 with pgvector"
```

**Memory categories:** `learning`, `context`, `preference`, `error`, `success`

### User Management

Multi-user support with roles and API key vault:

```bash
/register souraka mypassword admin     # Create admin account
/login souraka mypassword               # Login
/addkey groq gsk_xxxx                   # Store API key securely
/addkey openai sk-xxxx                  # Add another provider
/keys                                   # List stored keys (masked)
```

**Roles:**

| Role | Permissions |
|------|-------------|
| `admin` | Everything + manage users + manage keys |
| `developer` | Read, write, execute, git, shell, autopilot, swarm, scaffold |
| `viewer` | Read only |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLI Layer                              │
│                        (cli.py + Click)                         │
│  Commands: /help /new /swarm /autopilot /saas /login /quit     │
├─────────────────────────────────────────────────────────────────┤
│                          Agent Core                             │
│                        (agent.py)                               │
│  Agentic loop: User → LLM → [Tool calls] → LLM → Response    │
├───────────────┬─────────────────┬───────────────────────────────┤
│  Providers    │     Tools       │      Advanced                 │
│               │                 │                               │
│  ollama.py    │  file_tools.py  │  autopilot.py (autonomous)   │
│  groq.py      │  code_tools.py  │  swarm.py (multi-agent)      │
│  openai.py    │  shell_tools.py │  memory.py (persistent)      │
│  anthropic.py │  git_tools.py   │  users.py (auth + vault)     │
│               │  project_tools  │  tiers.py (provider tiers)   │
│  registry.py  │  saas_templates │  turbo.py (cache + pool)     │
│  base.py      │  registry.py    │  errors.py (error handling)  │
├───────────────┴─────────────────┴───────────────────────────────┤
│                         UI Layer                                │
│  console.py (Rich panels, markdown, syntax highlighting)       │
│  input.py (prompt_toolkit with history)                        │
├─────────────────────────────────────────────────────────────────┤
│                      Configuration                              │
│  config.py (.env) │ session.py (JSON) │ memory (JSON)          │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Input
    │
    ▼
┌──────────┐     ┌───────────┐     ┌──────────────┐
│   CLI    │────►│   Agent   │────►│  LLM Provider│
│          │     │  (loop)   │◄────│  (streaming) │
└──────────┘     │           │     └──────────────┘
                 │     │     │
                 │     ▼     │
                 │ ┌───────┐ │
                 │ │ Tools │ │     Tool calls are executed
                 │ │ (27)  │ │     between LLM rounds until
                 │ └───────┘ │     the agent produces a final
                 │           │     text response
                 └───────────┘
                       │
                       ▼
               ┌──────────────┐
               │  Rich Output │
               │  (streaming) │
               └──────────────┘
```

### File Structure

```
saisa/
├── __init__.py            # Package root, version
├── config.py              # Environment configuration (.env)
├── errors.py              # Custom exceptions + recovery suggestions
├── agent.py               # Core agentic loop (chat → tools → response)
├── prompts.py             # SAISA 2030 system prompt
├── session.py             # Conversation save/load (JSON)
├── cli.py                 # CLI entry point (Click) + all commands
├── autopilot.py           # Autonomous: plan → execute → verify
├── swarm.py               # Multi-agent orchestration (5 agents)
├── memory.py              # Persistent memory with TF-IDF retrieval
├── users.py               # User management + API key vault
├── tiers.py               # Provider tiers (free → elite)
├── turbo.py               # Response cache + connection pool
├── providers/
│   ├── __init__.py
│   ├── base.py            # Abstract LLM interface (Message, ToolCall)
│   ├── registry.py        # Provider factory
│   ├── ollama.py          # Ollama provider (local)
│   ├── groq_provider.py   # Groq provider (turbo cloud)
│   ├── openai_provider.py # OpenAI provider
│   └── anthropic_provider.py # Anthropic provider
├── tools/
│   ├── __init__.py
│   ├── registry.py        # 27 tool definitions + dispatch
│   ├── file_tools.py      # File CRUD + tree
│   ├── code_tools.py      # Regex search + find files
│   ├── shell_tools.py     # Command execution + system info
│   ├── git_tools.py       # Git operations
│   ├── project_tools.py   # Scaffolding + context detection
│   └── saas_templates.py  # SaaS project generator
└── ui/
    ├── __init__.py
    ├── console.py         # Rich output (panels, markdown, syntax)
    └── input.py           # prompt_toolkit input with history
```

---

## Configuration

### Environment Variables (.env)

```env
# ─── Provider Selection ───────────────────────────────────────
# Options: ollama (default, free), groq, openai, anthropic
SAISA_PROVIDER=ollama

# ─── Ollama (Local — FREE, no key needed) ─────────────────────
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
# Other good models: qwen2.5-coder, deepseek-coder-v2, codellama

# ─── Groq (Cloud — Fast, free tier available) ─────────────────
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
# Get key: https://console.groq.com/keys

# ─── OpenAI (Cloud — Premium) ─────────────────────────────────
OPENAI_API_KEY=sk-your_key_here
OPENAI_MODEL=gpt-4o
# Get key: https://platform.openai.com/api-keys

# ─── Anthropic (Cloud — Elite) ────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-your_key_here
ANTHROPIC_MODEL=claude-sonnet-4-20250514
# Get key: https://console.anthropic.com/settings/keys

# ─── Agent Behavior ───────────────────────────────────────────
SAISA_TEMPERATURE=0.3           # Creativity (0.0 = precise, 1.0 = creative)
SAISA_MAX_TOOL_ROUNDS=30        # Max tool calls per turn
SAISA_MAX_CONTEXT=60            # Max messages in context window
SAISA_TIMEOUT=300               # Request timeout (seconds)

# ─── Feature Flags ────────────────────────────────────────────
SAISA_STREAMING=1               # Real-time token streaming (1=on, 0=off)
SAISA_ALLOW_SHELL=1             # Allow shell command execution
SAISA_ALLOW_GIT=1               # Allow git operations

# ─── Identity ─────────────────────────────────────────────────
SAISA_NAME=SAISA                # Agent name
SAISA_OWNER=Souraka HAMIDA      # Your name (shown in prompts)

# ─── Workspace ─────────────────────────────────────────────────
# SAISA_WORKSPACE=/path/to/project  # Override working directory
# SAISA_SESSIONS_DIR=~/.saisa/sessions  # Session storage
```

### Recommended Models

| Use Case | Provider | Model | Why |
|----------|----------|-------|-----|
| **Free & Private** | Ollama | `qwen2.5-coder` | Best free coding model |
| **Fast Iteration** | Groq | `llama-3.3-70b-versatile` | ~500 tok/s, free tier |
| **Complex Projects** | OpenAI | `gpt-4o` | Best reasoning |
| **Long Context** | Anthropic | `claude-sonnet-4-20250514` | 200K context window |
| **Quick Tasks** | Ollama | `llama3.2` | Small, fast, capable |

---

## Error Handling

SAISA includes robust error handling with **user-friendly messages and recovery suggestions** for every error type:

### Provider Errors

| Error | Cause | Recovery |
|-------|-------|----------|
| `ProviderConnectionError` | Can't reach LLM | Start Ollama / check internet |
| `APIKeyMissingError` | No API key configured | Set key in .env or use Ollama |
| `RateLimitError` | Too many requests | Wait and retry, or use local model |
| `ModelNotFoundError` | Model doesn't exist | Pull model or check name |

### Tool Errors

| Error | Cause | Recovery |
|-------|-------|----------|
| `FileNotFoundError_` | File doesn't exist | Use /tree or find_files |
| `EditConflictError` | Search string not unique | Read file first, add context |
| `ShellCommandError` | Command failed/blocked | Check syntax, some cmds blocked |
| `PermissionDeniedError` | Insufficient role | Login with appropriate permissions |

### Session Errors

| Error | Cause | Recovery |
|-------|-------|----------|
| `SessionNotFoundError` | Session ID invalid | Use /sessions to list |
| `SessionCorruptedError` | File damaged | Start new session with /new |

All errors provide:
- Clear error message
- Specific recovery suggestion
- Link to documentation when relevant

---

## Troubleshooting

### "Ollama unreachable"
```bash
# Install Ollama: https://ollama.com
ollama serve          # Start the server
ollama pull llama3.2  # Pull a model
saisa                 # Try again
```

### "API key missing"
```bash
# Edit your .env file:
cp .env.example .env
nano .env  # Add your API key
```

### "Model not found"
```bash
# Ollama:
ollama list           # See available models
ollama pull <model>   # Pull a model

# Cloud providers: check the model name in the provider's docs
```

### "Rate limit"
```bash
# Switch to a local model:
saisa --provider ollama

# Or wait and retry — Groq auto-retries with backoff
```

### Shell commands blocked
SAISA blocks dangerous commands for safety:
- `rm -rf /`, `dd if=/dev/zero`, `mkfs`, etc.
- This is intentional. To run these commands, use your terminal directly.

---

## Vision: SAISA 2030

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    SAISA 2030 ROADMAP                           │
│                "Your Private Digital Soul"                      │
│                                                                 │
│  Phase 0 (NOW) ─── Phase 1 ─── Phase 2 ─── Phase 3           │
│  Terminal Agent     Desktop      OS Layer     Neural           │
│                     Agent        Integration  Kernel           │
│                                                                 │
│  ✓ 27 tools         □ GUI app     □ System     □ Continuous   │
│  ✓ 4 providers      □ Browser     □ File       □ learning     │
│  ✓ Multi-agent      □ Visual      □ manager    □ Cognitive    │
│  ✓ Autopilot        □ context     □ Process    □ swarm        │
│  ✓ Memory           □ Plugin      □ control    □ Digital      │
│  ✓ SaaS gen         □ system      □ Network    □ sovereignty  │
│  ✓ User mgmt        □ IDE         □ Security   □ Marketplace  │
│                       plugin        sandbox                    │
│                                                                 │
│  Foundation ──────────────────────────────► Full Vision        │
│  (Open Source, Local-First, Privacy-Respecting)                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **100% Open Source** — MIT License, transparent code, community-driven
2. **Local First** — Works offline with Ollama, your data never leaves your machine
3. **Privacy by Design** — No telemetry, no tracking, no cloud dependency
4. **Modular Architecture** — Swap providers, add tools, extend agents
5. **Performance** — Turbo mode with caching, connection pooling, streaming
6. **Accessibility** — Free tier (Ollama) with optional cloud upgrades

### Contributing

We welcome contributions! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run lint: `ruff check saisa/`
5. Commit: `git commit -m "feat: description"`
6. Push: `git push origin feature/my-feature`
7. Open a Pull Request

**Areas we need help with:**
- New tool implementations
- New project templates
- New LLM provider integrations
- Documentation and translations
- Bug reports and fixes

---

## Legacy v1

The original SAISA v1 agent is still available in `local_agent/`, `brain/`, `agents/`, `tools/`, `memory/`, and `sandbox/` directories. It supports Ollama and Groq with autopilot mode, browser automation, and SQLite memory. Run with `python main.py`.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

### Created by [Souraka HAMIDA](https://souraka.restafy.shop)

**GitHub:** [@Souraka229](https://github.com/Souraka229) · **Website:** [souraka.restafy.shop](https://souraka.restafy.shop)

*SAISA — Making AI development accessible, private, and powerful.*

<sub>Made with passion in the pursuit of digital sovereignty.</sub>

</div>