"""
🧠 CEREBRUM - Le cerveau IA
===========================
Gemma 4 (Ollama) integration pour la compréhension et planification.

Rôle:
- Comprendre les tâches utilisateur
- Découper les objectifs en étapes
- Générer du code
- Planifier les actions
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from local_agent.config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TEMPERATURE,
    OLLAMA_NUM_CTX,
)


class Cerebrum:
    """
    Cerveau IA principal - Gemma 4
    
    Transforme les tâches complexes en plans d'action exécutables.
    """
    
    def __init__(self, model: str | None = None):
        self.base_url = OLLAMA_BASE_URL.rstrip("/")
        self.model = model or OLLAMA_MODEL
        self.http = httpx.Client(timeout=600.0)
        self._system_prompt = self._load_brain_prompt()
        
    def _load_brain_prompt(self) -> str:
        return """Tu es **Cerebrum**, le cerveau IA ultra-puissant d'un agent autonome.

🎯 Ta mission:
- Comprendre TOUTE tâche formulée par l'utilisateur
- La décomposer en étapes logiques et exécutables
- Planifier l'ordre d'exécution optimal
- Anticiper les problèmes et proposer des solutions

💡 Exemple de transformation:
"Créer un SaaS login + tester" → [
  {"action": "create_backend", "detail": "FastAPI avec auth JWT"},
  {"action": "create_frontend", "detail": "Page login HTML/JS"},
  {"action": "start_server", "detail": "Lancer serveur sur port 3000"},
  {"action": "open_browser", "detail": "Ouvrir Chrome à localhost:3000"},
  {"action": "test_login", "detail": "Remplir formulaire et soumettre"},
  {"action": "verify", "detail": "Vérifier réponse OK"}
]

🔧 Tu as accès à ces outils:
- Terminal (bash/powershell)
- Python runner
- Node.js runner
- Git
- Browser automation (Playwright)
- File system
- Docker

📝 Format de réponse (JSON):
{
  "task": "description courte",
  "steps": [
    {"order": 1, "action": "nom_action", "detail": "détail", "tool": "outil_à_utiliser"}
  ],
  "estimated_time": "X minutes",
  "risks": ["risk1", "risk2"]
}

Sois précis, structuré, et anticipe les problèmes."""
    
    def _chat(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": OLLAMA_TEMPERATURE,
                "num_ctx": OLLAMA_NUM_CTX or 8192,
            }
        }
        r = self.http.post(f"{self.base_url}/api/chat", json=payload)
        r.raise_for_status()
        return r.json()
    
    def analyze_task(self, user_request: str) -> dict[str, Any]:
        """Analyse une tâche et retourne un plan d'exécution."""
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": f"Analyse cette tâche et crée un plan:\n\n{user_request}"}
        ]
        
        data = self._chat(messages)
        content = data.get("message", {}).get("content", "")
        
        # Parser la réponse JSON
        try:
            # Essayer d'extraire le JSON de la réponse
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
            else:
                return {"task": user_request, "error": "Impossible de parser le plan", "raw": content}
            
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {"task": user_request, "error": "Format JSON invalide", "raw": content}
    
    def execute_plan(self, plan: dict[str, Any], orchestrator) -> str:
        """Exécute un plan via l'orchestrateur."""
        steps = plan.get("steps", [])
        results = []
        
        for step in steps:
            order = step.get("order", 0)
            action = step.get("action", "unknown")
            detail = step.get("detail", "")
            tool = step.get("tool", "terminal")
            
            print(f"\n🔄 Étape {order}: {action}")
            print(f"   Détail: {detail}")
            print(f"   Outil: {tool}")
            
            # Exécuter via l'orchestrateur
            result = orchestrator.execute_step(step)
            results.append({"step": order, "action": action, "result": result})
            
            # Feedback loop - vérifier si succès
            if not self._is_success(result):
                print(f"   ⚠️ Échec détecté, adaptation...")
                # Ici on pourrait appeler self._adapt_plan() pour corriger
                
        return self._format_results(results)
    
    def _is_success(self, result: str) -> bool:
        """Vérifie si le résultat est un succès."""
        # Logique simple - à améliorer avec des patterns plus élaborés
        error_indicators = ["error", "failed", "échec", "erreur"]
        result_lower = result.lower()
        return not any(indicator in result_lower for indicator in error_indicators)
    
    def _format_results(self, results: list[dict]) -> str:
        """Formate les résultats de l'exécution."""
        output = ["# 📊 Résultats d'exécution\n"]
        for r in results:
            status = "✅" if self._is_success(str(r.get("result", ""))) else "❌"
            output.append(f"{status} Étape {r['step']}: {r['action']}")
        return "\n".join(output)
    
    def close(self):
        self.http.close()