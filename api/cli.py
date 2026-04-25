"""
🚀 SAISA - Super AI Self-Autonomous
===================================
Interface principale pour le terminal

Usage:
    python -m api.cli "crée un SaaS login"
"""

from __future__ import annotations

import sys
import asyncio
from pathlib import Path

# Ajout du path pour imports locaux
sys.path.insert(0, str(Path(__file__).parent.parent))

from brain.cerebrum import Cerebrum
from agents.orchestrator import AgentOrchestrator
from tools.tool_layer import ToolLayer
from memory.semantic.memory_system import MemorySystem
from local_agent.config import WORKSPACE_ROOT, OLLAMA_MODEL


class SAISA:
    """
    Super AI Self-Autonomous - L'IA ultime locale
    
    Combine:
    - Cerebrum (cerveau)
    - Orchestrator (chef de projet)
    - Tool Layer (mains)
    - Memory (apprentissage)
    """
    
    def __init__(self):
        print("🚀 Initialisation de SAISA...")
        
        # Initialiser les composants
        self.tool_layer = ToolLayer(WORKSPACE_ROOT)
        self.cerebrum = Cerebrum()
        self.orchestrator = AgentOrchestrator(self.cerebrum, self.tool_layer)
        self.memory = MemorySystem()
        
        print(f"   🧠 Cerebrum: {OLLAMA_MODEL}")
        print(f"   📁 Workspace: {WORKSPACE_ROOT}")
        print(f"   🧠 Mémoire: {self.memory.db_path}")
        print("   ✅ Prêt!\n")
    
    def run(self, task: str) -> str:
        """Exécute une tâche."""
        print(f"📝 Tâche: {task}\n")
        
        try:
            # Exécution avec le feedback loop
            result = self.orchestrator.execute_task(task)
            
            # Apprendre du résultat
            self.memory.analyze_and_learn(
                user_input=task,
                agent_response=result,
                tools_used=[],  # À améliorer
                success="error" not in result.lower()
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Erreur: {str(e)}"
            self.memory.learn_from_error(str(e), "Contactez le développeur")
            return error_msg
    
    def stats(self) -> dict:
        """Affiche les statistiques."""
        return self.memory.get_stats()
    
    def close(self):
        """Ferme proprement."""
        self.cerebrum.close()


def main():
    """Point d'entrée CLI."""
    if len(sys.argv) < 2:
        print("""
🧠 SAISA - Super AI Self-Autonomous
===================================

Usage:
    python -m api.cli "ta tâche"
    python -m api.cli --stats
    python -m api.cli --interactive

Exemples:
    python -m api.cli "crée un fichier hello.py"
    python -m api.cli "ouvre google.com"
    python -m api.cli "teste le site localhost:3000"
""")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg == "--stats":
        # Afficher les stats
        from memory.semantic.memory_system import MemorySystem
        mem = MemorySystem()
        stats = mem.get_stats()
        print("\n📊 Statistiques d'apprentissage:")
        print(f"   Conversations: {stats['conversations']}")
        print(f"   Erreurs apprises: {stats['errors_learned']}")
        print(f"   Erreurs résolues: {stats['errors_solved']}")
        print(f"   Compétences: {stats['skills_acquired']}")
        print(f"   Tâches accomplies: {stats['tasks_completed']}")
        print(f"   Score d'apprentissage: {stats['learning_score']}/100")
        return
    
    if arg == "--interactive":
        # Mode interactif
        saisa = SAISA()
        print("Mode interactif. Tapez 'quit' pour quitter.\n")
        
        while True:
            try:
                task = input("Vous> ").strip()
                if task.lower() in ("quit", "exit", "q"):
                    break
                if not task:
                    continue
                    
                result = saisa.run(task)
                print(f"\n{saisa.run(task)}\n")
                
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
        saisa.close()
        print("\n👋 Au revoir!")
        return
    
    # Exécution simple
    task = " ".join(sys.argv[1:])
    saisa = SAISA()
    result = saisa.run(task)
    print(result)
    saisa.close()


if __name__ == "__main__":
    main()