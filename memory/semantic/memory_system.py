"""
🧠 MEMORY SYSTEM
================
Cerveau qui apprend - Stockage persistant

SQLite + Vector DB concept pour:
- Garder historique des conversations
- Apprendre des erreurs
- Améliorer les décisions
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from local_agent.config import WORKSPACE_ROOT


class MemorySystem:
    """
    Système de mémoire avec apprentissage
    
    Combine:
    - SQLite pour le stockage structuré
    - Concepts de Vector DB pour la recherche semantique
    """
    
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or (WORKSPACE_ROOT / "memory" / "agent_memory.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """Initialise la base de données."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Table des conversations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_input TEXT NOT NULL,
                agent_response TEXT NOT NULL,
                tools_used TEXT,
                success BOOLEAN
            )
        """)
        
        # Table des erreurs apprises
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_pattern TEXT NOT NULL,
                solution TEXT NOT NULL,
                times_encountered INTEGER DEFAULT 1,
                times_solved INTEGER DEFAULT 0,
                last_seen TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # Table des préférences utilisateur
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Table des compétences acquises
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills_acquired (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                code TEXT,
                created_at TEXT NOT NULL,
                times_used INTEGER DEFAULT 0
            )
        """)
        
        # Table des tâches accomplies
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks_completed (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                steps INTEGER,
                duration_seconds INTEGER,
                success BOOLEAN,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ========== CONVERSATIONS ==========
    
    def save_conversation(self, user_input: str, agent_response: str, 
                         tools_used: list[str] | None = None, success: bool = True):
        """Sauvegarde une conversation."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (timestamp, user_input, agent_response, tools_used, success)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            user_input,
            agent_response,
            json.dumps(tools_used or []),
            success
        ))
        
        conn.commit()
        conn.close()
    
    def get_recent_conversations(self, limit: int = 10) -> list[dict[str, Any]]:
        """Récupère les conversations récentes."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, user_input, agent_response, success
            FROM conversations
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "timestamp": row[0],
                "user_input": row[1],
                "agent_response": row[2],
                "success": bool(row[3])
            })
        
        conn.close()
        return results
    
    # ========== ERREURS APPRISES ==========
    
    def learn_from_error(self, error_pattern: str, solution: str):
        """Apprend d'une erreur."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Vérifier si cette erreur est déjà connue
        cursor.execute("SELECT id, times_encountered FROM learned_errors WHERE error_pattern = ?", 
                      (error_pattern,))
        row = cursor.fetchone()
        
        if row:
            # Mettre à jour
            cursor.execute("""
                UPDATE learned_errors 
                SET times_encountered = times_encountered + 1,
                    last_seen = ?,
                    solution = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), solution, row[0]))
        else:
            # Créer nouvelle entrée
            cursor.execute("""
                INSERT INTO learned_errors (error_pattern, solution, last_seen, created_at)
                VALUES (?, ?, ?, ?)
            """, (error_pattern, solution, datetime.now().isoformat(), 
                  datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def mark_error_solved(self, error_pattern: str):
        """Marque une erreur comme résolue."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE learned_errors
            SET times_solved = times_solved + 1
            WHERE error_pattern = ?
        """, (error_pattern,))
        
        conn.commit()
        conn.close()
    
    def get_solutions_for_error(self, error_pattern: str) -> list[str]:
        """Trouve des solutions pour une erreur."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT solution, times_solved, times_encountered
            FROM learned_errors
            WHERE error_pattern LIKE ?
            ORDER BY times_solved DESC
            LIMIT 5
        """, (f"%{error_pattern}%",))
        
        solutions = [row[0] for row in cursor.fetchall()]
        conn.close()
        return solutions
    
    # ========== PRÉFÉRENCES ==========
    
    def set_preference(self, key: str, value: str):
        """Sauvegarde une préférence."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, value, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_preference(self, key: str, default: str = "") -> str:
        """Récupère une préférence."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM user_preferences WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        conn.close()
        return row[0] if row else default
    
    # ========== COMPÉTENCES ACQUISES ==========
    
    def acquire_skill(self, name: str, description: str, code: str):
        """Acquiert une nouvelle compétence."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO skills_acquired (name, description, code, created_at)
            VALUES (?, ?, ?, ?)
        """, (name, description, code, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def use_skill(self, name: str):
        """Marque une compétence comme utilisée."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE skills_acquired
            SET times_used = times_used + 1
            WHERE name = ?
        """, (name,))
        
        conn.commit()
        conn.close()
    
    def get_skills(self) -> list[dict[str, Any]]:
        """Liste toutes les compétences acquises."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, description, times_used, created_at
            FROM skills_acquired
            ORDER BY times_used DESC
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "name": row[0],
                "description": row[1],
                "times_used": row[2],
                "created_at": row[3]
            })
        
        conn.close()
        return results
    
    # ========== TÂCHES ==========
    
    def log_task(self, description: str, steps: int, duration: int, success: bool):
        """Enregistre une tâche accomplie."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tasks_completed (description, steps, duration_seconds, success, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (description, steps, duration, success, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> dict[str, Any]:
        """Retourne les statistiques d'apprentissage."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Nombre de conversations
        cursor.execute("SELECT COUNT(*) FROM conversations")
        conversations = cursor.fetchone()[0]
        
        # Erreurs apprises
        cursor.execute("SELECT COUNT(*) FROM learned_errors")
        errors_learned = cursor.fetchone()[0]
        
        # Erreurs résolues
        cursor.execute("SELECT SUM(times_solved) FROM learned_errors")
        errors_solved = cursor.fetchone()[0] or 0
        
        # Compétences acquises
        cursor.execute("SELECT COUNT(*) FROM skills_acquired")
        skills = cursor.fetchone()[0]
        
        # Tâches accomplies
        cursor.execute("SELECT COUNT(*) FROM tasks_completed WHERE success = 1")
        tasks_done = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "conversations": conversations,
            "errors_learned": errors_learned,
            "errors_solved": errors_solved,
            "skills_acquired": skills,
            "tasks_completed": tasks_done,
            "learning_score": self._calculate_learning_score(
                conversations, errors_learned, errors_solved, skills, tasks_done
            )
        }
    
    def _calculate_learning_score(self, conv: int, err: int, solved: int, 
                                   skills: int, tasks: int) -> float:
        """Calcule un score d'apprentissage."""
        if conv == 0:
            return 0.0
        
        score = (
            min(conv / 100, 1.0) * 20 +  # Conversations
            min(err / 50, 1.0) * 20 +     # Erreurs apprises
            min(solved / 20, 1.0) * 25 +   # Erreurs résolues
            min(skills / 10, 1.0) * 15 +   # Compétences
            min(tasks / 50, 1.0) * 20      # Tâches accomplies
        )
        return round(score, 1)
    
    # ========== FEEDBACK LOOP ==========
    
    def analyze_and_learn(self, user_input: str, agent_response: str, 
                          tools_used: list[str], success: bool):
        """Analyse et apprend du résultat."""
        # Sauvegarder la conversation
        self.save_conversation(user_input, agent_response, tools_used, success)
        
        # Si échec, apprendre de l'erreur
        if not success:
            # Extraire le pattern d'erreur (simplifié)
            error_pattern = self._extract_error_pattern(agent_response)
            if error_pattern:
                # Proposer une solution générique
                solution = self._generate_solution(error_pattern)
                self.learn_from_error(error_pattern, solution)
        
        # Si succès avec des outils, c'est une compétence acquise potentielle
        if success and tools_used:
            skill_name = self._extract_skill_name(user_input, tools_used)
            if skill_name:
                self.acquire_skill(skill_name, f"Appris: {user_input[:100]}", "")
    
    def _extract_error_pattern(self, response: str) -> str | None:
        """Extrait le pattern d'erreur."""
        error_keywords = ["error", "failed", "exception", "erreur", "échec"]
        for keyword in error_keywords:
            if keyword in response.lower():
                return response[:200]
        return None
    
    def _generate_solution(self, error: str) -> str:
        """Génère une solution pour l'erreur."""
        return f"Solution pour: {error[:100]}"
    
    def _extract_skill_name(self, user_input: str, tools: list[str]) -> str | None:
        """Extrait le nom d'une compétence acquise."""
        if len(tools) >= 3:  # Complexe = potentiellement une compétence
            return f"task_{len(tools)}_tools"
        return None