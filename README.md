# Local Agent — Windows

**Nom de dépôt GitHub suggéré : `local-agent-windows`** — court, clair, SEO-friendly.  
*Alternatives : `win-local-agent`, `workspace-cli-agent`.*

Assistant CLI **open source** pour **un seul opérateur** : fichiers, mémoire persistante et **skills** sur ton disque (`workspace/`), aide aux **dissertations**, outils optionnels (web, e-mail, WhatsApp via wa.me, navigateur, PowerShell avec confirmations).

---

## Français

### Données vs inférence (« tout local » ?)

| Élément | Où ça vit |
|--------|-----------|
| Mémoire, skills, dissertations | **Toujours sur ton PC** (`workspace/memory`, `skills`, `dissertations`) |
| Réponses du modèle | **Ollama** = **100 % local**. **Groq** = **cloud** (le chat transite par leurs serveurs). |

Pour un maximum de local : `AGENT_BACKEND=ollama` dans `.env`.

### Prérequis

- Windows, **Python 3.11+** (testé avec 3.13)
- **Groq (défaut)** : compte [Groq Console](https://console.groq.com/keys), API type OpenAI
- **Ollama** : [ollama.com](https://ollama.com) + modèle supportant les **appels d’outils** (ex. `qwen2.5`, `llama3.1`)

### Installation

```powershell
cd $HOME\local-agent-windows
python -m pip install -r requirements.txt
copy .env.example .env
```

Édite `.env` : `GROQ_API_KEY=...`. Pour l’inférence locale : `AGENT_BACKEND=ollama` et `OLLAMA_MODEL=...`.

### Lancer

```powershell
python main.py
```

**Commandes** : `/quit` quitter · `/new` vider l’historique · `/paste` (ou `/long`) saisie **multiligne** jusqu’à une ligne contenant seulement `/fin`.

Chemins des outils : **relatifs au dossier `workspace`**.  
**Suppression de fichier** : **cinq** confirmations `OUI` dans le terminal.

### Mode performance & qualité

- `AGENT_PERFORMANCE_MODE=0` (**défaut**) : prompts système **complets** (meilleure qualité, plus de tokens).
- `AGENT_PERFORMANCE_MODE=1` : prompt court + **cache** `web_search` — utile si tu as souvent des **429 TPM** sur Groq.

`GROQ_TEMPERATURE` / `OLLAMA_TEMPERATURE` (défaut **0.65**) : réponses plus stables ; monte vers ~1.0 pour un style plus libre.

Ce n’est **ni de l’AGI** ni un score d’efficacité garanti — voir `workspace/LIRE-realite-agent.md`.

### Groq : limites & erreurs

- **429 (TPM)** : nouveaux essais automatiques avec attente ; réduis `GROQ_MAX_HISTORY_MESSAGES`, utilise `/new`, ou `AGENT_PERFORMANCE_MODE=1`.
- **400 `tool_use_failed`** (pseudo-appels type `<function=...>`) : **nouvelle tentative** automatique puis repli **sans outils** si besoin.

Variables utiles : `GROQ_MAX_HISTORY_MESSAGES`, `GROQ_RATE_LIMIT_MAX_RETRIES`, `GROQ_MAX_COMPLETION_TOKENS`, `GROQ_MODEL` — voir `.env.example`.

### Mémoire, skills, dissertations

- **`append_memory_note` / `read_memory_notes`** → `workspace/memory/journal.md`
- **`skills/*.md`** : tes règles ; l’agent peut les lire avec `read_file`
- **`dissertations/`** : plans et textes (honnêteté académique : sources, pas de plagiat)

### Ollama (local + auto-évaluation optionnelle)

```env
AGENT_BACKEND=ollama
OLLAMA_MODEL=qwen2.5:7b
SELF_EVAL=1
SELF_EVAL_MIN_SCORE=7
```

### Web, e-mail, WhatsApp, PowerShell

- **`AGENT_OWNER_NAME`** / **`AGENT_OWNER_ONLINE_HINT`** : identité et indices pour recherches publiques
- **`ALLOW_FETCH_URL=1`** : `fetch_url` (page en texte, pas un navigateur graphique)
- **`ALLOW_OPEN_BROWSER=1`** : URLs + liens wa.me (confirmation à chaque fois)
- **WhatsApp** : `open_whatsapp_compose` → [wa.me](https://wa.me) ; **l’envoi se fait dans l’app** ; pas d’API WhatsApp Business intégrée
- **`ALLOW_SMTP_SEND=1`** + variables `SMTP_*` : `send_smtp_email` (confirmation terminal)
- **`ALLOW_POWERSHELL=1`** : commandes système (très prudent ; confirmations)

### Comment l’agent « apprend »

Pas d’entraînement des poids du modèle en direct. En pratique : **mémoire fichier**, **skills**, **fichiers dans `dissertations/`**, **historique de session** (fenêtre limitée). Pour un vrai fine-tuning, il faut un autre pipeline (hors de ce dépôt).

### Pistes / contributions

- Auto-évaluation côté Groq (comme Ollama)
- Module séparé WhatsApp Business (Twilio / Meta) si usage pro
- Issues & PR bienvenues — précise la version Python, le backend (Groq/Ollama) et le modèle.

---

## English

### Data vs inference (“fully local”?)

| Piece | Where it lives |
|--------|----------------|
| Memory, skills, dissertations | **Always on your PC** (`workspace/memory`, `skills`, `dissertations`) |
| Model replies | **Ollama** = **fully local**. **Groq** = **cloud** (chat goes through their API). |

For maximum privacy on inference: `AGENT_BACKEND=ollama` in `.env`.

### Requirements

- Windows, **Python 3.11+** (tested on 3.13)
- **Groq (default)** : [Groq Console](https://console.groq.com/keys) API key, OpenAI-compatible API
- **Ollama** : [ollama.com](https://ollama.com) + a model with **tool calling** (e.g. `qwen2.5`, `llama3.1`)

### Setup

```powershell
cd $HOME\local-agent-windows
python -m pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`: set `GROQ_API_KEY=...`. For local inference: `AGENT_BACKEND=ollama` and `OLLAMA_MODEL=...`.

### Run

```powershell
python main.py
```

**Commands**: `/quit` exit · `/new` clear history · `/paste` (or `/long`) **multiline** input until a line that contains only `/fin`.

Tool paths are **relative to `workspace`**.  
**File delete** requires **five** `OUI` confirmations in the terminal.

### Performance vs quality

- `AGENT_PERFORMANCE_MODE=0` (**default**): **full** system prompts (better answers, more tokens).
- `AGENT_PERFORMANCE_MODE=1`: shorter prompt + **`web_search` cache** — helps if you often hit **Groq 429 TPM** limits.

`GROQ_TEMPERATURE` / `OLLAMA_TEMPERATURE` (default **0.65**): steadier answers; raise toward ~1.0 for more creative tone.

This is **not AGI** and does not guarantee a fixed “quality percentage” — see `workspace/LIRE-realite-agent.md`.

### Groq: limits & errors

- **429 (TPM)**: automatic retries with backoff; lower `GROQ_MAX_HISTORY_MESSAGES`, use `/new`, or enable `AGENT_PERFORMANCE_MODE=1`.
- **400 `tool_use_failed`** (fake `<function=...>`-style calls): **automatic retry**, then a **no-tools** fallback if the API still rejects the turn.

See `.env.example` for `GROQ_MAX_HISTORY_MESSAGES`, `GROQ_RATE_LIMIT_MAX_RETRIES`, `GROQ_MAX_COMPLETION_TOKENS`, `GROQ_MODEL`.

### Memory, skills, dissertations

- **`append_memory_note` / `read_memory_notes`** → `workspace/memory/journal.md`
- **`skills/*.md`**: your rules; the agent can read them with `read_file`
- **`dissertations/`**: outlines and drafts (cite sources, no plagiarism)

### Ollama (local + optional self-eval)

```env
AGENT_BACKEND=ollama
OLLAMA_MODEL=qwen2.5:7b
SELF_EVAL=1
SELF_EVAL_MIN_SCORE=7
```

### Web, email, WhatsApp, PowerShell

- **`AGENT_OWNER_NAME`** / **`AGENT_OWNER_ONLINE_HINT`**: identity and hints for public web search
- **`ALLOW_FETCH_URL=1`**: `fetch_url` (plain text fetch, not a full browser)
- **`ALLOW_OPEN_BROWSER=1`**: open URLs + wa.me links (confirmation each time)
- **WhatsApp**: `open_whatsapp_compose` builds [wa.me](https://wa.me) links; **sending happens in the app**; no embedded WhatsApp Business API
- **`ALLOW_SMTP_SEND=1`** + `SMTP_*`: `send_smtp_email` (terminal confirmation)
- **`ALLOW_POWERSHELL=1`**: system commands (use with care; confirmations)

### How the agent “learns”

The model weights are **not** trained during chat. What changes behaviour: **file memory**, **skills**, **files under `dissertations/`**, and **session history** (bounded window). Real fine-tuning needs another pipeline outside this repo.

### Roadmap / contributing

- Self-evaluation on Groq (parity with Ollama)
- Optional separate module for WhatsApp Business (Twilio / Meta) for pro use
- Issues & PRs welcome — include Python version, backend (Groq/Ollama), and model name.

---

## Licence / License

Projet fourni en **open source** : ajoute un fichier `LICENSE` (souvent **MIT** ou **Apache-2.0**) pour clarifier les droits.  
This repo is **open source**: add a `LICENSE` file (commonly **MIT** or **Apache-2.0**) to state terms clearly.
