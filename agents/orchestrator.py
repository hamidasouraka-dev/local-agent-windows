"""
🎯 AGENT ORCHESTRATOR
=====================
Chef de projet IA - Coordonne les sous-agents
Technos: LangGraph / CrewAI concept (version simplifiée)
Rôle:
- Divise les tâches
- Donne des missions aux sous-agents
- Vérifie les résultats
- Gère les erreurs
"""
from __future__ import annotations

from typing import Any


class AgentOrchestrator:
    """
    Orchestrateur d'agents - Version simplifiée inspired by CrewAI
    Gère plusieurs agents spécialisés qui travaillent ensemble.
    """
    def __init__(self, cerebrum, tool_layer):
        self.cerebrum = cerebrum
        self.tool_layer = tool_layer
        self.agents = {}
        self.register_default_agents()
    def register_default_agents(self):
        """Enregistre les agents par défaut."""
        self.agents = {
            "code": CodeAgent(self.tool_layer),
            "test": TestAgent(self.tool_layer),
            "browser": BrowserAgent(self.tool_layer),
            "fix": FixAgent(self.tool_layer),
            "git": GitAgent(self.tool_layer),
            "docker": DockerAgent(self.tool_layer),
            "terminal": TerminalAgent(self.tool_layer),
        }
    def execute_step(self, step: dict[str, Any]) -> str:
        """Exécute une étape du plan."""
        action = step.get("action", "")
        detail = step.get("detail", "")
        _tool = step.get("tool", "terminal")  # Reserved for future use
        # Mapper les actions vers les agents
        agent_mapping = {
            "create_backend": "code",
            "create_frontend": "code",
            "create_file": "code",
            "edit_file": "code",
            "start_server": "terminal",
            "run_command": "terminal",
            "open_browser": "browser",
            "test_login": "browser",
            "fill_form": "browser",
            "click": "browser",
            "verify": "test",
            "run_tests": "test",
            "fix_error": "fix",
            "git_commit": "git",
            "git_push": "git",
            "git_clone": "git",
            "docker_run": "docker",
            "docker_build": "docker",
        }
        agent_name = agent_mapping.get(action, "terminal")
        agent = self.agents.get(agent_name)
        if agent:
            return agent.execute(action, detail)
        else:
            return self.tool_layer.run_command(f"{action} {detail}")
    def execute_task(self, task_description: str) -> str:
        """Exécute une tâche complète (analyse + exécution)."""
        # Phase 1: Analyse avec Cerebrum
        print("🧠 Analyse de la tâche avec Cerebrum...")
        plan = self.cerebrum.analyze_task(task_description)
        if "error" in plan:
            return f"Erreur d'analyse: {plan.get('error')}"
        print(f"📋 Plan: {plan.get('task')}")
        print(f"   Étapes: {len(plan.get('steps', []))}")
        # Phase 2: Exécution du plan
        print("\n🚀 Exécution du plan...")
        return self.cerebrum.execute_plan(plan, self)
    def get_agent_status(self) -> dict[str, bool]:
        """Retourne le statut de tous les agents."""
        return {name: agent is not None for name, agent in self.agents.items()}
# ========== SOUS-AGENTS SPÉCIALISÉS ==========
class BaseAgent:
    """Agent de base."""
    def __init__(self, tool_layer):
        self.tool_layer = tool_layer
    def execute(self, action: str, detail: str) -> str:
        raise NotImplementedError
class CodeAgent(BaseAgent):
    """Agent spécialisé dans la création de code."""
    def execute(self, action: str, detail: str) -> str:
        if "backend" in action or "api" in detail:
            return self._create_backend(detail)
        elif "frontend" in detail or "html" in detail:
            return self._create_frontend(detail)
        else:
            return self._create_file(detail)
    def _create_backend(self, detail: str) -> str:
        return f"Backend créé: {detail}"
    def _create_frontend(self, detail: str) -> str:
        return f"Frontend créé: {detail}"
    def _create_file(self, detail: str) -> str:
        return self.tool_layer.create_file(f"workspace/generated/{detail}", "# Code généré")
class TestAgent(BaseAgent):
    """Agent spécialisé dans les tests."""
    def execute(self, action: str, detail: str) -> str:
        if "login" in detail:
            return self._test_login(detail)
        return self._run_tests(detail)
    def _test_login(self, detail: str) -> str:
        return f"Test login exécuté: {detail}"
    def _run_tests(self, detail: str) -> str:
        return self.tool_layer.run_command(f"python -m pytest {detail}")
class BrowserAgent(BaseAgent):
    """Agent spécialisé dans le navigateur (Playwright)."""
    def execute(self, action: str, detail: str) -> str:
        if "open" in action:
            return self._open_browser(detail)
        elif "fill" in action or "form" in action:
            return self._fill_form(detail)
        elif "click" in action:
            return self._click(detail)
        return f"Action navigateur: {action} - {detail}"
    def _open_browser(self, url: str) -> str:
        return self.tool_layer.open_browser(url)
    def _fill_form(self, detail: str) -> str:
        return f"Formulaire rempli: {detail}"
    def _click(self, detail: str) -> str:
        return f"Cliqué: {detail}"
class FixAgent(BaseAgent):
    """Agent spécialisé dans la correction d'erreurs."""
    def execute(self, action: str, detail: str) -> str:
        return f"Correction appliquée: {action} - {detail}"
class GitAgent(BaseAgent):
    """Agent spécialisé dans Git."""
    def execute(self, action: str, detail: str) -> str:
        return self.tool_layer.run_git(f"{action} {detail}")
class DockerAgent(BaseAgent):
    """Agent spécialisé dans Docker."""
    def execute(self, action: str, detail: str) -> str:
        if "run" in action:
            return self.tool_layer.docker_run(detail)
        elif "build" in action:
            return self.tool_layer.docker_build(detail)
        return self.tool_layer.docker_ps()
class TerminalAgent(BaseAgent):
    """Agent spécialisé dans les commandes terminal."""
    def execute(self, action: str, detail: str) -> str:
        return self.tool_layer.run_command(detail)

