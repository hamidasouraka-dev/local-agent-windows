# Ce que cet agent est (et n’est pas)

- **Ce n’est pas une AGI** au sens recherche : pas de conscience garantie, pas de « 99 % d’efficacité » mesurable sur toutes les tâches.
- **C’est un agent outillé** : LLM + fichiers + mémoire + web + options (mail, navigateur, shell avec confirmations).
- **Rapide** : Groq est déjà très rapide ; le mode performance réduit les tokens de prompt, met en cache les recherches web identiques, et réutilise une connexion HTTP.
- **Sans limite pratique** : impossible (RAM, quotas API, taille des modèles). Les plafonds dans `.env` sont des garde-fous techniques ; tu peux les augmenter tant que ta machine et les API suivent.

Pour le **maximum de contrôle local** des données sensibles : `AGENT_BACKEND=ollama`.
