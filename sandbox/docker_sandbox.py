"""
🐳 EXECUTION SANDBOX
====================
Environnement d'exécution sécurisé avec Docker

Rôle:
- Exécuter du code sans casser le PC
- Isoler l'IA
- Prévenir les accidents
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from local_agent.config import WORKSPACE_ROOT


class ExecutionSandbox:
    """
    Sandbox d'exécution avec Docker
    
    Isolation complète pour:
    - Exécution de code non fiable
    - Tests dangereux
    - Prévention de dommages système
    """
    
    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or WORKSPACE_ROOT
        self.image_name = "saisa-sandbox"
        self.container_name = "saisa-runner"
        
    def build_image(self, dockerfile_content: str | None = None) -> dict[str, Any]:
        """Construit l'image Docker du sandbox."""
        if dockerfile_content is None:
            dockerfile_content = self._default_dockerfile()
        
        # Écrire le Dockerfile
        dockerfile_path = self.workspace / "sandbox" / "Dockerfile"
        dockerfile_path.parent.mkdir(parents=True, exist_ok=True)
        dockerfile_path.write_text(dockerfile_content, encoding="utf-8")
        
        # Builder l'image
        result = subprocess.run(
            ["docker", "build", "-t", self.image_name, str(dockerfile_path.parent)],
            capture_output=True,
            text=True
        )
        
        return {
            "ok": result.returncode == 0,
            "output": result.stdout + result.stderr
        }
    
    def _default_dockerfile(self) -> str:
        """Dockerfile par défaut."""
        return """FROM python:3.11-slim

# Installation des outils essentiels
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    wget \\
    vim \\
    && rm -rf /var/lib/apt/lists/*

# Workspace
WORKDIR /workspace

# Python tools
RUN pip install --no-cache-dir \\
    pytest \\
    black \\
    ruff \\
    mypy

CMD ["/bin/bash"]
"""
    
    def run_in_sandbox(self, command: str, timeout: int = 300) -> dict[str, Any]:
        """
        Exécute une commande dans le sandbox
        
        Args:
            command: Commande à exécuter
            timeout: Timeout en secondes
            
        Returns:
            Résultat de l'exécution
        """
        # Créer un conteneur temporaire
        container_id = None
        try:
            # Démarrer un container avec le workspace mounté
            result = subprocess.run([
                "docker", "run", "-d",
                "--name", f"{self.container_name}_{id(command)}",
                "-v", f"{self.workspace}:/workspace",
                "-w", "/workspace",
                self.image_name,
                "sleep", "infinity"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"error": f"Échec démarrage container: {result.stderr}"}
            
            container_id = result.stdout.strip()
            
            # Exécuter la commande
            exec_result = subprocess.run([
                "docker", "exec", container_id,
                "sh", "-c", command
            ], capture_output=True, text=True, timeout=timeout)
            
            return {
                "ok": exec_result.returncode == 0,
                "exit_code": exec_result.returncode,
                "stdout": exec_result.stdout,
                "stderr": exec_result.stderr,
                "output": exec_result.stdout + exec_result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {"error": f"Timeout après {timeout}s", "timeout": True}
            
        finally:
            # Nettoyer le container
            if container_id:
                subprocess.run(["docker", "kill", container_id], capture_output=True)
                subprocess.run(["docker", "rm", container_id], capture_output=True)
    
    def run_python_sandbox(self, code: str) -> dict[str, Any]:
        """Exécute du Python en sécurité."""
        return self.run_in_sandbox(f'python -c "{code.replace("\"", "\\\"")}"')
    
    def run_tests_sandbox(self, test_path: str = "tests/") -> dict[str, Any]:
        """Exécute les tests dans le sandbox."""
        return self.run_in_sandbox(f"cd /workspace && pytest {test_path} -v")
    
    def list_sandboxes(self) -> list[dict[str, Any]]:
        """Liste les sandboxes actifs."""
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={self.container_name}", 
             "--format", "{{.ID}}|{{.Names}}|{{.Status}}|{{.Image}}"],
            capture_output=True,
            text=True
        )
        
        sandboxes = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("|")
                if len(parts) >= 4:
                    sandboxes.append({
                        "id": parts[0],
                        "name": parts[1],
                        "status": parts[2],
                        "image": parts[3]
                    })
        
        return sandboxes
    
    def stop_all_sandboxes(self) -> dict[str, Any]:
        """Arrête tous les sandboxes."""
        result = subprocess.run(
            ["docker", "kill", f"$(docker ps -q --filter name={self.container_name})"],
            shell=True,
            capture_output=True,
            text=True
        )
        
        subprocess.run(
            ["docker", "rm", f"$(docker ps -aq --filter name={self.container_name})"],
            shell=True,
            capture_output=True
        )
        
        return {"ok": True, "message": "Sandboxes arrêtés"}


# ========== SIMPLE USAGE ==========

if __name__ == "__main__":
    sandbox = ExecutionSandbox()
    
    # Exemple d'utilisation
    print("🧪 Test du sandbox...")
    
    # Exécuter un test simple
    result = sandbox.run_in_sandbox("echo 'Hello from sandbox!' && python --version")
    print(json.dumps(result, indent=2))
    
    # Exécuter Python safely
    result = sandbox.run_python_sandbox("print('Secure Python execution!')")
    print(json.dumps(result, indent=2))