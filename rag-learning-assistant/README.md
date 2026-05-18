# 📚 RAG Learning Assistant
### Assistant d'apprentissage intelligent — IA Distribuée & Systèmes Multi-Agents

> Architecture RAG locale avec Ollama · FastAPI · ChromaDB · Multi-Agents

---

## 🏗 Architecture Système

```
┌─────────────────────────────────────────────────────────┐
│                    ÉTUDIANT (UI Web)                    │
│              http://localhost:8000                       │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP/REST
                        ▼
┌─────────────────────────────────────────────────────────┐
│              ROUTER AGENT (Cerveau)                     │
│    Analyse l'intention → classe en 4 catégories         │
│    ┌──────────┬──────────┬──────────┬──────────┐       │
│    │  règles  │  regex   │ LLM class│ fallback │       │
│    └──────────┴──────────┴──────────┴──────────┘       │
└───────┬─────────────────────┬───────────────────────────┘
        │                     │
        ▼                     ▼
┌──────────────┐    ┌──────────────────────┐
│GENERAL AGENT │    │    RAG AGENT         │
│ Chat basique │    │  ┌────────────────┐  │
│ Historique   │    │  │ Mode: answer   │  │
│ inclus       │    │  │ Mode: summary  │  │
└──────┬───────┘    │  │ Mode: quiz     │  │
       │            │  └────────┬───────┘  │
       │            └──────────┼───────────┘
       │                       │
       │            ┌──────────▼───────────┐
       │            │   VECTOR STORE       │
       │            │   ChromaDB           │
       │            │   embeddings Ollama  │
       │            └──────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│             MEMORY AGENT (Historique)                   │
│         Fenêtre glissante de N tours                    │
│         Injecté dans chaque requête LLM                 │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│              OLLAMA (LLM Local)                         │
│   mistral / llama3 / phi3 / gemma2 ...                  │
│   nomic-embed-text (embeddings)                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📂 Structure du projet

```
rag-learning-assistant/
├── 📄 README.md
├── 📄 requirements.txt
├── 📄 .env.example
│
├── 🐍 backend/
│   ├── main.py              # FastAPI — point d'entrée API
│   ├── config.py            # Configuration pydantic-settings
│   │
│   ├── agents/
│   │   ├── router.py        # 🧠 Cerveau : route vers le bon agent
│   │   ├── rag_agent.py     # 📚 Agent RAG (answer | summary | quiz)
│   │   ├── memory_agent.py  # 💾 Agent Mémoire (historique glissant)
│   │   └── general_agent.py # 💬 Agent Général (chat basique)
│   │
│   └── core/
│       ├── ollama_client.py # 🤖 Client Ollama (chat + embeddings)
│       ├── vector_store.py  # 🗃 ChromaDB (indexation + recherche)
│       └── pdf_processor.py # 📄 Extraction + chunking des PDFs
│
├── 🌐 frontend/
│   └── index.html           # UI web (dark academic design)
│
└── 📁 data/
    ├── uploads/             # PDFs téléversés
    └── vectorstore/         # Base ChromaDB (persistée)
```

---

## ⚙️ Installation

### 1. Prérequis

```bash
# Python 3.11+
python --version

# Ollama
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Télécharger les modèles Ollama

```bash
# Modèle de chat (choisir selon votre RAM)
ollama pull mistral          # 4.1 Go — recommandé
# ollama pull llama3          # 4.7 Go — très bon
# ollama pull phi3            # 2.3 Go — léger
# ollama pull gemma2          # 5.4 Go — excellent

# Modèle d'embeddings (obligatoire)
ollama pull nomic-embed-text # 274 Mo
```

### 3. Installer les dépendances Python

```bash
# Cloner / extraire le projet
cd rag-learning-assistant

# Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
# .venv\Scripts\activate       # Windows

# Installer
pip install -r requirements.txt
```

### 4. Configuration (optionnel)

```bash
cp .env.example .env
# Éditer .env pour changer le modèle, les ports, etc.
```

---

## 🚀 Lancement

```bash
# Terminal 1 — Ollama
ollama serve

# Terminal 2 — API FastAPI
python -m uvicorn backend.main:app --reload --port 8000

# Ouvrir le navigateur
# http://localhost:8000
```

---

## 🎮 Utilisation

### Interface web
1. **Charger un PDF** → clic sur "Ajouter un PDF" dans la sidebar
2. **Attendre l'indexation** (~30s selon la taille du document)
3. **Choisir un mode** (ou laisser "Auto" pour le routage automatique)
4. **Poser une question** dans le chat

### Modes disponibles
| Mode | Description | Exemple |
|------|-------------|---------|
| 🧠 Auto | Le Router analyse l'intention | Toute question |
| 🔍 Réponse précise | RAG + citation sources | "Qu'est-ce que le gradient ?" |
| 📝 Résumé | Synthèse structurée du cours | "Résume ce chapitre" |
| 🎯 Quiz | 5 QCM interactifs | "Génère un quiz sur TCP/IP" |

### API REST

```bash
# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explique le théorème de Bayes", "mode": "auto"}'

# Upload PDF
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@mon_cours.pdf"

# Lister les documents
curl http://localhost:8000/documents

# Santé du système
curl http://localhost:8000/health

# Effacer l'historique
curl -X DELETE http://localhost:8000/memory
```

### Documentation interactive
- Swagger UI : http://localhost:8000/docs
- ReDoc : http://localhost:8000/redoc

---

## 🧠 Détail des Agents

### Router Agent (Cerveau)
Analyse l'intention utilisateur en 2 étapes :
1. **Classification par règles** (regex, rapide) → quiz / summary / answer / general
2. **Classification LLM** (si cas ambigu) → appel Ollama avec temperature=0

### RAG Agent
- **Embed** la question avec `nomic-embed-text`
- **Recherche** les K chunks les plus proches (cosine similarity dans ChromaDB)
- **Génère** la réponse avec le contexte injecté dans le prompt
- Modes : `answer` (précis) · `summary` (structuré) · `quiz` (JSON QCM)

### Memory Agent
- Fenêtre glissante de **10 tours** (configurable)
- Injecté dans chaque appel LLM pour la cohérence conversationnelle
- Stats : nombre de tours, heure de début de session

### General Agent
- Chat standard sans RAG
- Utilise l'historique conversationnel complet
- Redirige vers le mode RAG si besoin

---

## 🔧 Configuration avancée

```env
OLLAMA_MODEL=mistral           # Modèle LLM
OLLAMA_EMBED_MODEL=nomic-embed-text
CHUNK_SIZE=512                 # Mots par chunk
CHUNK_OVERLAP=64               # Chevauchement entre chunks
TOP_K=5                        # Chunks récupérés par requête
MAX_HISTORY_TURNS=10           # Historique conversationnel
```

---

## 📊 Concepts IA Distribuée illustrés

| Concept | Implémentation |
|---------|----------------|
| **Agent autonome** | Chaque agent (RAG, Memory, General) est indépendant |
| **Orchestrateur** | Router centralise la décision de routage |
| **RAG** | ChromaDB + nomic-embed-text + Ollama |
| **Mémoire partagée** | MemoryAgent accessible par tous les agents |
| **Traitement asynchrone** | FastAPI async + BackgroundTasks pour l'indexation |
| **Séparation des responsabilités** | Un agent = une responsabilité |
| **Tolérance aux pannes** | Retry (tenacity) sur les appels Ollama |

---

## 📝 Licence
Projet académique — Module IA Distribuée & Systèmes Multi-Agents
