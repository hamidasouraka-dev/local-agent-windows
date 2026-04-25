"""
Système de chargement dynamique des skills.
Les skills sont des modules Python dans le dossier skills/ qui extend les capacités de l'agent.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from local_agent.config import WORKSPACE_ROOT


class SkillsLoader:
    """Charge et exécute les skills dynamiques."""
    
    def __init__(self, skills_dir: Path | None = None):
        self.skills_dir = skills_dir or (Path(WORKSPACE_ROOT) / "skills")
        self._skills: dict[str, Any] = {}
        self._load_skills()
    
    def _load_skills(self) -> None:
        """Charge tous les skills disponibles."""
        if not self.skills_dir.exists():
            return
        
        for file in self.skills_dir.glob("*.py"):
            if file.name.startswith("_") or file.stem in ("base", "loader"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(file.stem, file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Enregistrer les functions marked comme skills
                    for name in dir(module):
                        obj = getattr(module, name, None)
                        if callable(obj) and hasattr(obj, "_is_skill"):
                            self._skills[name] = obj
            except Exception as e:
                print(f"Erreur chargement skill {file.name}: {e}")
    
    def list_skills(self) -> list[str]:
        """Liste tous les skills disponibles."""
        return list(self._skills.keys())
    
    def get_skill(self, name: str) -> Any:
        """Récupère un skill par son nom."""
        return self._skills.get(name)
    
    def execute_skill(self, name: str, **kwargs) -> str:
        """Exécute un skill et retourne le résultat."""
        skill = self.get_skill(name)
        if not skill:
            return f"Skill '{name}' non trouvé. Skills disponibles: {self.list_skills()}"
        
        try:
            result = skill(**kwargs)
            return str(result) if result is not None else "Skill exécuté avec succès"
        except Exception as e:
            return f"Erreur execution skill '{name}': {e}"


def skill(enabled: bool = True):
    """Décorateur pour marquer une fonction comme skill."""
    def decorator(func):
        func._is_skill = enabled
        return func
    return decorator


# Instance globale
_skills_loader: SkillsLoader | None = None


def get_skills_loader() -> SkillsLoader:
    """Récupère l'instance globale du loader."""
    global _skills_loader
    if _skills_loader is None:
        _skills_loader = SkillsLoader()
    return _skills_loader


# ============== SKILLS PRÉDÉFINIS ==============

@skill()
def code_review(file_path: str, focus: str = "general") -> str:
    """
    Effectue une revue de code simple sur un fichier.
    
    Args:
        file_path: Chemin vers le fichier à reviewer
        focus: Type de review (general, security, performance, style)
    
    Returns:
        Review du code
    """
    path = Path(file_path)
    if not path.exists():
        return f"Fichier non trouvé: {file_path}"
    
    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")
    
    issues = []
    suggestions = []
    
    # Analyse basique selon le focus
    if focus in ("general", "security"):
        # Vérifications de sécurité basiques
        for i, line in enumerate(lines, 1):
            if "password" in line.lower() and "=" in line and '"' not in line and "'" not in line:
                issues.append(f"Ligne {i}: Mot de passe en texte brut potentiellement exposé")
            if "eval(" in line:
                issues.append(f"Ligne {i}: Utilisation de eval() potentiellement dangereuse")
            if "exec(" in line:
                issues.append(f"Ligne {i}: Utilisation de exec() potentiellement dangereuses")
            if "os.system(" in line:
                issues.append(f"Ligne {i}: Utilisation de os.system() - valider les entrées")
    
    if focus in ("general", "performance"):
        for i, line in enumerate(lines, 1):
            if ".append(" in line and "for" in lines[max(0, i-2):i+1]:
                suggestions.append(f"Ligne {i}: Envisager list comprehension pour de meilleures perfs")
    
    if focus in ("general", "style"):
        if len(lines) > 500:
            suggestions.append(f"Fichier très long ({len(lines)} lignes). Envisager le splitter.")
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                suggestions.append(f"Ligne {i}: Ligne très longue ({len(line)} chars)")
    
    result = [f"# Code Review: {path.name}", f"## Focus: {focus}\n"]
    
    if issues:
        result.append("## 🔴 Problèmes détectés")
        for issue in issues:
            result.append(f"- {issue}")
    
    if suggestions:
        result.append("\n## 💡 Suggestions d'amélioration")
        for sug in suggestions:
            result.append(f"- {sug}")
    
    if not issues and not suggestions:
        result.append("✅ Aucune anomalie détectée!")
    
    return "\n".join(result)


@skill()
def analyze_file(file_path: str) -> str:
    """Analyse un fichier et retourne des statistiques."""
    path = Path(file_path)
    if not path.exists():
        return f"Fichier non trouvé: {file_path}"
    
    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")
    
    stats = {
        "fichier": path.name,
        "lignes": len(lines),
        "caracteres": len(content),
        "mots": len(content.split()),
        "extensions": path.suffix,
    }
    
    return json.dumps(stats, indent=2, ensure_ascii=False)


@skill()
def generate_documentation(file_path: str) -> str:
    """Génère une documentation basique pour un fichier Python."""
    path = Path(file_path)
    if not path.exists():
        return f"Fichier non trouvé: {file_path}"
    
    if path.suffix != ".py":
        return "Seuls les fichiers Python sont supportés pour l'instant"
    
    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")
    
    doc = [f"# Documentation: {path.name}\n"]
    
    # Trouver les functions et classes
    in_class = ""
    in_function = ""
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Classes
        if stripped.startswith("class "):
            parts = stripped[6:].split("(")
            in_class = parts[0]
            doc.append(f"\n## Classe: {in_class}")
        
        # Fonctions
        if stripped.startswith("def "):
            parts = stripped[4:].split("(")
            func_name = parts[0]
            params = parts[1].rstrip("):") if len(parts) > 1 else ""
            
            # Chercher le docstring
            docstring = ""
            if i < len(lines) and '"""' in lines[i]:
                for j in range(i, min(i+5, len(lines))):
                    if '"""' in lines[j]:
                        docstring = lines[j].strip().strip('"""')
                        break
            
            doc.append(f"\n### `{func_name}({params})`")
            if docstring:
                doc.append(f"_{docstring}_")
    
    return "\n".join(doc)


@skill()
def explain_error(error_message: str) -> str:
    """Explique une erreur Python et propose une solution."""
    error = error_message.strip()
    
    explanations = {
        "IndentationError": "Erreur d'indentation. Vérifiez la cohérence des espaces/tabulations.",
        "SyntaxError": "Erreur de syntaxe. Vérifiez les parenthèses, virgules, etc.",
        "NameError": "Variable non définie. Vérifiez l'orthographe et l'import.",
        "TypeError": "Erreur de type. Opération sur un type incompatible.",
        "ImportError": "Module non trouvé. Vérifiez l'installation et l'import.",
        "FileNotFoundError": "Fichier non trouvé. Vérifiez le chemin.",
        "KeyError": "Clé non trouvée dans le dictionnaire.",
        "AttributeError": "Attribut non trouvé sur l'objet.",
        "ValueError": "Valeur invalide pour l'opération.",
    }
    
    for err_type, explanation in explanations.items():
        if err_type in error:
            return f"## 🔍 Analyse de l'erreur\n\n**Type**: {err_type}\n\n**Explication**: {explanation}\n\n**Message original**:\n```\n{error}\n```"
    
    return f"## 🔍 Erreur inconnue\n\nJe ne reconnais pas ce type d'erreur.\n\n**Message**:\n```\n{error}\n```"