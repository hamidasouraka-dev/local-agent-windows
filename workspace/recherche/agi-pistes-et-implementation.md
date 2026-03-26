# AGI : bonnes sources et pistes d’implémentation

> Document de synthèse (pas une vérité finale). Les liens étaient valides au moment de la rédaction.  
> *Note : dans cet environnement, pas d’accès au mode @Browser ; la veille a été faite via pages web publiques consultables.*

---

## 1. Définir l’AGI (vue d’ensemble)

- **Wikipedia — Artificial general intelligence**  
  https://en.wikipedia.org/wiki/Artificial_general_intelligence  
  Synthèse : AGI = capacités cognitives **générales** (raisonnement sous incertitude, planification, apprentissage, langage, intégration de compétences), par opposition à l’IA **étroite**. Mention des tests (Turing, « coffee test », etc.), des risques discutés, et du lien **ANI → AGI → ASI**.

---

## 2. Document académique clé : niveaux d’AGI (Google DeepMind)

- **Levels of AGI for Operationalizing Progress on the Path to AGI**  
  https://arxiv.org/abs/2311.02462  
  (Morris et al., ICML 2024 — version PDF : https://arxiv.org/pdf/2311.02462 )

**Intérêt pour toi :** cadre pour **mesurer** où en sont les systèmes (profondeur + largeur des capacités) et comment penser **autonomie** et **risques** selon le niveau. Utile pour ne pas confondre « chatbot très fort » et AGI au sens recherche.

---

## 3. Sécurité, alignement, impacts (recherche appliquée)

- **Anthropic — Research**  
  https://www.anthropic.com/research  

Axes : **alignement** (modèles utiles, honnêtes, sans danger inutile), **interprétabilité**, **impacts sociétaux**, red teaming. C’est le type de littérature nécessaire si tu veux **déployer** des systèmes plus autonomes sans ignorer les dérives.

*(Autres pôles reconnus : interprétabilité, gouvernance, normes — à croiser avec des revues et des rapports d’organismes publics selon ton pays.)*

---

## 4. Comment on peut « implémenter » quelque chose qui *ressemble* à de l’AGI aujourd’hui

Il n’existe **pas** de recette unique ; l’AGI au sens strict reste un **objectif de recherche**. En pratique, l’industrie combine :

| Piste | Idée | Implémentation typique |
|--------|------|-------------------------|
| **Fondation + outils** | LLM + API + mémoire + perception | Agents (comme ton projet), MCP, RAG, bases vectorielles |
| **Multimodalité** | Langage + vision + audio | Modèles VLM, pipelines capteurs |
| **Planification / boucle** | Découper des objectifs longs | Boucles tool-calling, planificateurs, state machines |
| **Monde / simulation** | Modèles du monde pour anticiper | World models (recherche), simulateurs, digital twins |
| **Robotique** | AGI « incarnée » | Embodied AI, apprentissage par démonstration, contrôle |
| **Neuro-symbolique** | Règles + réseaux | Graphes de connaissances + LLM, vérification formelle sur parties critiques |
| **Évaluation** | Savoir si ça progresse | Benchmarks généralistes, tâches multi-étapes, audits humains |

**Fine-tuning / LoRA / RLHF** : servent à **spécialiser** ou **aligner** un modèle existant ; ce n’est pas « inventer l’AGI d’un coup », mais c’est une **implémentation** concrète d’amélioration continue sur **tes** données et **tes** contraintes.

---

## 5. Lien avec ton agent local (windows-local-agent)

Ce que tu as déjà : **outils**, **mémoire fichier**, **skills**, **workspace** = architecture **outil + contexte persistant**, proche des **building blocks** des agents modernes, **sans** prétendre reproduire une AGI.

Pour aller plus loin côté « généraliste » (toujours pas de garantie AGI) :

1. **RAG** : indexer `skills/`, `dissertations/`, PDFs avec embeddings + recherche sémantique.  
2. **Modèle local costaud** (Ollama) + **contexte long** pour tenir plus de documents.  
3. **Tâches multi-étapes** : file d’objectifs, journal de plan, relecture critique (tu as déjà l’idée d’auto-évaluation côté Ollama).  
4. **Garde-fous** : confirmations humaines (déjà là pour shell / e-mail / navigateur).

---

## 6. À retenir

- Les **meilleurs documents** pour commencer : **Wikipedia AGI** (vue large) + **arXiv 2311.02462** (cadre DeepMind) + **recherches alignment** (ex. Anthropic).  
- **Implémenter** au sens ingénieur = surtout **agents**, **données**, **évaluation**, **sécurité** — pas une formule magique.  
- L’**auto-entraînement** des poids du modèle est un **projet à part** (données, GPU, licence, éthique).

---

*Tu peux déplacer ce fichier, le couper en skills, ou le faire enrichir par ton agent avec `read_file` / `write_file` dans `dissertations/`.*
