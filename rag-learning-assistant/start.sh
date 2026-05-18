#!/usr/bin/env bash
# =============================================================
#  RAG Learning Assistant — Script de démarrage
# =============================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; GOLD='\033[0;33m'; NC='\033[0m'

echo -e "${GOLD}"
echo "  ██████╗  █████╗  ██████╗     ███████╗ ██████╗██╗  ██╗ ██████╗ ██╗      █████╗ ██████╗"
echo "  ██╔══██╗██╔══██╗██╔════╝     ██╔════╝██╔════╝██║  ██║██╔═══██╗██║     ██╔══██╗██╔══██╗"
echo "  ██████╔╝███████║██║  ███╗    ███████╗██║     ███████║██║   ██║██║     ███████║██████╔╝"
echo "  ██╔══██╗██╔══██║██║   ██║    ╚════██║██║     ██╔══██║██║   ██║██║     ██╔══██║██╔══██╗"
echo "  ██║  ██║██║  ██║╚██████╔╝    ███████║╚██████╗██║  ██║╚██████╔╝███████╗██║  ██║██║  ██║"
echo "  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝"
echo -e "${NC}"
echo -e "${BLUE}  Assistant d'apprentissage IA · IA Distribuée & Multi-Agents${NC}"
echo ""

# --- Vérification Python ---
echo -e "${YELLOW}[1/4] Vérification de l'environnement Python...${NC}"
if [ ! -d ".venv" ]; then
    echo "  Création de l'environnement virtuel..."
    python3 -m venv .venv
fi
source .venv/bin/activate
echo -e "${GREEN}  ✓ Python $(python --version)${NC}"

# --- Dépendances ---
echo -e "${YELLOW}[2/4] Installation des dépendances...${NC}"
pip install -q -r requirements.txt
echo -e "${GREEN}  ✓ Dépendances installées${NC}"

# --- Ollama ---
echo -e "${YELLOW}[3/4] Vérification d'Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}  ✗ Ollama non trouvé. Installez-le : curl -fsSL https://ollama.com/install.sh | sh${NC}"
    exit 1
fi

if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "  Démarrage d'Ollama en arrière-plan..."
    ollama serve &> /tmp/ollama.log &
    sleep 3
fi

# Vérifier les modèles
MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; d=json.load(sys.stdin); print([m['name'] for m in d.get('models',[])])" 2>/dev/null || echo "[]")
echo -e "${GREEN}  ✓ Ollama disponible — Modèles : ${MODELS}${NC}"

if [[ "$MODELS" != *"nomic-embed-text"* ]]; then
    echo -e "${YELLOW}  ⚠ Téléchargement de nomic-embed-text (274 Mo)...${NC}"
    ollama pull nomic-embed-text
fi

# --- Lancement API ---
echo -e "${YELLOW}[4/4] Démarrage de l'API FastAPI...${NC}"
echo ""
echo -e "${GREEN}  ┌─────────────────────────────────────────┐${NC}"
echo -e "${GREEN}  │  🌐 Interface : http://localhost:8000    │${NC}"
echo -e "${GREEN}  │  📚 API Docs  : http://localhost:8000/docs│${NC}"
echo -e "${GREEN}  └─────────────────────────────────────────┘${NC}"
echo ""

python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
