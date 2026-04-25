"""
🧰 TOOL LAYER
=============
Les "mains" de l'IA - Accès au système

Outils essentiels:
- Terminal (bash/powershell)
- Python runner
- Node runner
- Git
- Browser automation
- File system
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from local_agent.config import (
    WORKSPACE_ROOT,
    ALLOW_POWERSHELL,
    ALLOW_GIT,
    ALLOW_DOCKER,
    ALLOW_OPEN_BROWSER,
    MAX_SHELL_OUTPUT,
    SHELL_TIMEOUT_SEC,
)


class ToolLayer:
    """
    Couche d'outils - Donne "des mains" à l'IA
    
    Tous les outils nécessaires pour exécuter des tâches réelles.
    """
    
    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or WORKSPACE_ROOT
        self.allow_powershell = ALLOW_POWERSHELL
        self.allow_git = ALLOW_GIT
        self.allow_docker = ALLOW_DOCKER
        self.allow_browser = ALLOW_OPEN_BROWSER
        
    # ========== TERMINAL ==========
    
    def run_command(self, command: str, timeout: int = SHELL_TIMEOUT_SEC) -> str:
        """Exécute une commande shell."""
        if not command.strip():
            return json.dumps({"error": "Commande vide"})
        
        # Sécurité - forbid dangerous commands
        dangerous = ["rm -rf /", "dd if=", ":(){:|:&};:", "mkfs", "dd if=/dev/zero"]
        for d in dangerous:
            if d in command:
                return json.dumps({"error": f"Commande dangereuse bloquée: {d}"})
        
        try:
            # Try bash first (Linux/Mac/WSL)
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.workspace),
            )
            return self._format_output(result)
        except subprocess.TimeoutExpired:
            return json.dumps({"error": f"Timeout après {timeout}s"})
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def run_python(self, code_or_file: str, file_mode: bool = False) -> str:
        """Exécute du code Python."""
        if file_mode:
            return self.run_command(f"python {code_or_file}")
        
        # Inline code
        return self.run_command(f'python -c "{code_or_file.replace("\"", "\\\"")}"')
    
    def run_node(self, code_or_file: str, file_mode: bool = False) -> str:
        """Exécute du code Node.js."""
        if file_mode:
            return self.run_command(f"node {code_or_file}")
        return self.run_command(f'node -e "{code_or_file.replace("\"", "\\\"")}"')
    
    # ========== FILE SYSTEM ==========
    
    def create_file(self, path: str, content: str) -> str:
        """Crée un fichier."""
        try:
            full_path = self.workspace / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding="utf-8")
            return json.dumps({"ok": True, "path": str(path)})
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def read_file(self, path: str) -> str:
        """Lit un fichier."""
        try:
            full_path = self.workspace / path
            content = full_path.read_text(encoding="utf-8")
            return json.dumps({"path": path, "content": content[:50000]})
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def list_files(self, directory: str = ".") -> str:
        """Liste les fichiers."""
        try:
            full_path = self.workspace / directory
            files = [p.name for p in full_path.iterdir()]
            return json.dumps({"directory": directory, "files": files})
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    # ========== GIT ==========
    
    def run_git(self, command: str) -> str:
        """Exécute une commande git."""
        if not self.allow_git:
            return json.dumps({"error": "Git désactivé"})
        
        return self.run_command(f"git {command}")
    
    def git_clone(self, repo_url: str, path: str = ".") -> str:
        """Clone un dépôt."""
        return self.run_git(f"clone {repo_url} {path}")
    
    def git_commit(self, message: str) -> str:
        """Commit les changements."""
        return self.run_git(f'commit -m "{message}"')
    
    def git_push(self) -> str:
        """Push vers remote."""
        return self.run_git("push")
    
    # ========== DOCKER ==========
    
    def docker_run(self, image: str, command: str = "", detach: bool = False) -> str:
        """Lance un container Docker."""
        if not self.allow_docker:
            return json.dumps({"error": "Docker désactivé"})
        
        cmd = f"docker run {'-d' if detach else ''} {image} {command}"
        return self.run_command(cmd)
    
    def docker_build(self, tag: str, path: str = ".") -> str:
        """Build une image Docker."""
        if not self.allow_docker:
            return json.dumps({"error": "Docker désactivé"})
        
        return self.run_command(f"docker build -t {tag} {path}")
    
    def docker_ps(self, all_containers: bool = False) -> str:
        """Liste les containers."""
        if not self.allow_docker:
            return json.dumps({"error": "Docker désactivé"})
        
        return self.run_command(f"docker ps {'-a' if all_containers else ''}")
    
    def docker_exec(self, container: str, command: str) -> str:
        """Exécute dans un container."""
        if not self.allow_docker:
            return json.dumps({"error": "Docker désactivé"})
        
        return self.run_command(f"docker exec {container} {command}")
    
    # ========== BROWSER (Playwright) ==========
    
    def open_browser(self, url: str) -> str:
        """Ouvre le navigateur."""
        if not self.allow_browser:
            return json.dumps({"error": "Navigateur désactivé"})
        
        try:
            import webbrowser
            webbrowser.open(url)
            return json.dumps({"ok": True, "url": url})
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def playwright_open(self, url: str) -> str:
        """Ouvre une page avec Playwright."""
        # Note: Playwright needs to be installed
        code = f"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('{url}')
        # Take screenshot
        await page.screenshot(path='screenshot.png')
        await browser.close()
        print('Page chargée: {url}')

asyncio.run(main())
"""
        return self.run_command(f'python -c """{code}"""')
    
    # ========== PLAYWRIGHT SPECIALIST ==========
    
    def browser_click(self, selector: str) -> str:
        """Clique sur un élément."""
        return self.playwright_run(f'await page.click("{selector}")')
    
    def browser_fill(self, selector: str, value: str) -> str:
        """Remplit un champ."""
        return self.playwright_run(f'await page.fill("{selector}", "{value}")')
    
    def browser_screenshot(self, path: str = "screenshot.png") -> str:
        """Prend une capture d'écran."""
        return self.playwright_run(f'await page.screenshot(path="{path}")')
    
    def browser_wait_for(self, selector: str, timeout: int = 30000) -> str:
        """Attend un élément."""
        return self.playwright_run(f'await page.wait_for_selector("{selector}", timeout={timeout})')
    
    def playwright_run(self, action_code: str) -> str:
        """Exécute du code Playwright personnalisé."""
        template = f"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        # User action here
        {action_code}
        await browser.close()

asyncio.run(main())
"""
        return self.run_command(f'python -c """{template}"""')
    
    # ========== HELPER ==========
    
    def _format_output(self, result: subprocess.CompletedProcess) -> str:
        """Formate la sortie d'une commande."""
        output = (result.stdout or "") + (result.stderr or "")
        if len(output) > MAX_SHELL_OUTPUT:
            output = output[:MAX_SHELL_OUTPUT] + "\n... [tronqué]"
        
        return json.dumps({
            "exit_code": result.returncode,
            "output": output,
        })


# Import needed for JSON
import json