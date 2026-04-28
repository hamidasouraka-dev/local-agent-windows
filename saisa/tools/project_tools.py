"""Project scaffolding and context detection tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ── Project templates ─────────────────────────────────────────────────────

TEMPLATES: dict[str, dict[str, Any]] = {
    "python-fastapi": {
        "description": "FastAPI REST API with async, tests, Docker",
        "files": {
            "main.py": '''"""FastAPI application."""
from fastapi import FastAPI

app = FastAPI(title="{{name}}", version="0.1.0")


@app.get("/")
async def root():
    return {"message": "Hello from {{name}}"}


@app.get("/health")
async def health():
    return {"status": "ok"}
''',
            "requirements.txt": "fastapi>=0.110.0\nuvicorn[standard]>=0.29.0\nhttpx>=0.27.0\npytest>=8.0.0\npytest-asyncio>=0.23.0\n",
            "Dockerfile": '''FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
            "tests/__init__.py": "",
            "tests/test_main.py": '''"""Tests for main API."""
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
''',
            ".gitignore": "__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\n",
            "README.md": "# {{name}}\n\n## Quick Start\n\n```bash\npip install -r requirements.txt\nuvicorn main:app --reload\n```\n\n## Tests\n\n```bash\npytest -v\n```\n",
        },
    },
    "python-cli": {
        "description": "Python CLI app with Click, tests, packaging",
        "files": {
            "src/__init__.py": "",
            "src/cli.py": '''"""CLI entry point."""
import click


@click.command()
@click.option("--name", "-n", default="World", help="Name to greet")
def main(name: str) -> None:
    """{{name}} CLI application."""
    click.echo(f"Hello, {name}!")


if __name__ == "__main__":
    main()
''',
            "pyproject.toml": '''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{{name}}"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["click>=8.0.0"]

[project.scripts]
{{name}} = "src.cli:main"
''',
            "tests/__init__.py": "",
            "tests/test_cli.py": '''"""Tests for CLI."""
from click.testing import CliRunner
from src.cli import main


def test_default():
    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code == 0
    assert "Hello" in result.output
''',
            ".gitignore": "__pycache__/\n*.pyc\n.venv/\nvenv/\n*.egg-info/\ndist/\nbuild/\n",
            "README.md": "# {{name}}\n\n## Install\n\n```bash\npip install -e .\n```\n\n## Usage\n\n```bash\n{{name}} --help\n```\n",
        },
    },
    "react-vite": {
        "description": "React + Vite + TypeScript starter",
        "files": {
            "package.json": '''{
  "name": "{{name}}",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.0",
    "vite": "^6.0.0"
  }
}
''',
            "tsconfig.json": '''{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
''',
            "vite.config.ts": '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
''',
            "index.html": '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{name}}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
''',
            "src/main.tsx": '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
''',
            "src/App.tsx": '''function App() {
  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui' }}>
      <h1>{{name}}</h1>
      <p>Edit <code>src/App.tsx</code> and save to test HMR.</p>
    </div>
  )
}

export default App
''',
            ".gitignore": "node_modules/\ndist/\n.env\n",
            "README.md": "# {{name}}\n\n## Dev\n\n```bash\nnpm install\nnpm run dev\n```\n\n## Build\n\n```bash\nnpm run build\n```\n",
        },
    },
    "node-express": {
        "description": "Express.js API with TypeScript",
        "files": {
            "package.json": '''{
  "name": "{{name}}",
  "version": "0.1.0",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "express": "^5.0.0"
  },
  "devDependencies": {
    "@types/express": "^5.0.0",
    "@types/node": "^22.0.0",
    "tsx": "^4.19.0",
    "typescript": "^5.5.0"
  }
}
''',
            "tsconfig.json": '''{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["src"]
}
''',
            "src/index.ts": '''import express from "express";

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.get("/", (_req, res) => {
  res.json({ message: "Hello from {{name}}" });
});

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
''',
            ".gitignore": "node_modules/\ndist/\n.env\n",
            "README.md": "# {{name}}\n\n## Dev\n\n```bash\nnpm install\nnpm run dev\n```\n",
        },
    },
}


def scaffold_project(name: str, template: str, path: str = ".") -> str:
    """Generate a full project from a template."""
    if template not in TEMPLATES:
        available = ", ".join(TEMPLATES.keys())
        return json.dumps({"error": f"Unknown template: {template}. Available: {available}"})

    root = Path(path).resolve() / name
    if root.exists():
        return json.dumps({"error": f"Directory already exists: {root}"})

    tmpl = TEMPLATES[template]
    created_files: list[str] = []
    try:
        for rel_path, content in tmpl["files"].items():
            file_path = root / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            rendered = content.replace("{{name}}", name)
            file_path.write_text(rendered, encoding="utf-8")
            created_files.append(str(rel_path))
    except Exception as e:
        return json.dumps({"error": str(e)})

    return json.dumps({
        "ok": True,
        "project": name,
        "template": template,
        "path": str(root),
        "files_created": created_files,
        "description": tmpl["description"],
    })


def list_templates() -> str:
    """List available project templates."""
    templates = [
        {"name": name, "description": tmpl["description"]}
        for name, tmpl in TEMPLATES.items()
    ]
    return json.dumps({"templates": templates})


def detect_project_context(path: str = ".") -> str:
    """Auto-detect project stack, frameworks, and configuration."""
    root = Path(path).resolve()
    context: dict[str, Any] = {
        "path": str(root),
        "name": root.name,
        "stack": [],
        "package_manager": None,
        "frameworks": [],
        "has_tests": False,
        "has_docker": False,
        "has_ci": False,
        "has_git": False,
        "entry_points": [],
        "config_files": [],
    }

    # Python detection
    if (root / "pyproject.toml").exists():
        context["stack"].append("python")
        context["config_files"].append("pyproject.toml")
        content = (root / "pyproject.toml").read_text(errors="ignore")
        if "fastapi" in content.lower():
            context["frameworks"].append("FastAPI")
        if "django" in content.lower():
            context["frameworks"].append("Django")
        if "flask" in content.lower():
            context["frameworks"].append("Flask")
    if (root / "requirements.txt").exists():
        context["stack"].append("python")
        context["package_manager"] = "pip"
        context["config_files"].append("requirements.txt")
    if (root / "Pipfile").exists():
        context["package_manager"] = "pipenv"

    # Node.js detection
    if (root / "package.json").exists():
        context["stack"].append("node")
        context["config_files"].append("package.json")
        try:
            pkg = json.loads((root / "package.json").read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "react" in deps:
                context["frameworks"].append("React")
            if "vue" in deps:
                context["frameworks"].append("Vue")
            if "next" in deps:
                context["frameworks"].append("Next.js")
            if "express" in deps:
                context["frameworks"].append("Express")
            if "vite" in deps:
                context["frameworks"].append("Vite")
            scripts = pkg.get("scripts", {})
            if "dev" in scripts:
                context["entry_points"].append("npm run dev")
            if "start" in scripts:
                context["entry_points"].append("npm start")
        except Exception:
            pass
        if (root / "pnpm-lock.yaml").exists():
            context["package_manager"] = "pnpm"
        elif (root / "yarn.lock").exists():
            context["package_manager"] = "yarn"
        elif (root / "bun.lockb").exists():
            context["package_manager"] = "bun"
        else:
            context["package_manager"] = "npm"

    # Rust
    if (root / "Cargo.toml").exists():
        context["stack"].append("rust")
        context["config_files"].append("Cargo.toml")

    # Go
    if (root / "go.mod").exists():
        context["stack"].append("go")
        context["config_files"].append("go.mod")

    # Java/Kotlin
    if (root / "pom.xml").exists():
        context["stack"].append("java")
        context["config_files"].append("pom.xml")
    if (root / "build.gradle").exists() or (root / "build.gradle.kts").exists():
        context["stack"].append("java/kotlin")

    # Docker
    if (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists() or (root / "docker-compose.yaml").exists():
        context["has_docker"] = True

    # CI/CD
    ci_paths = [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile", ".circleci"]
    for ci in ci_paths:
        if (root / ci).exists():
            context["has_ci"] = True
            break

    # Tests
    test_dirs = ["tests", "test", "__tests__", "spec"]
    for td in test_dirs:
        if (root / td).is_dir():
            context["has_tests"] = True
            break

    # Git
    context["has_git"] = (root / ".git").is_dir()

    # Entry points
    for ep in ["main.py", "app.py", "index.js", "index.ts", "src/index.ts", "src/main.py"]:
        if (root / ep).exists():
            context["entry_points"].append(ep)

    # Deduplicate
    context["stack"] = list(dict.fromkeys(context["stack"]))

    return json.dumps(context, indent=2)
