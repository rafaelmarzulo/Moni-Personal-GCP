#!/bin/bash
# ============================================================================
# Script de Sincronização - Moni-Personal → Moni-Personal-GCP
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Sincronizando Moni-Personal → Moni-Personal-GCP${NC}"
echo -e "${GREEN}============================================${NC}"
echo

# Verificar se estamos no diretório correto
if [[ ! -d "infrastructure" ]]; then
    echo -e "${RED}Erro: Execute este script do diretório Moni-Personal-GCP${NC}"
    exit 1
fi

# Verificar se projeto original existe
if [[ ! -d "../Moni-Personal" ]]; then
    echo -e "${RED}Erro: Projeto original não encontrado em ../Moni-Personal${NC}"
    exit 1
fi

echo -e "${YELLOW}Arquivos que serão sincronizados:${NC}"
echo "  - app/"
echo "  - templates/"
echo "  - static/"
echo "  - main.py, models.py, schemas.py, database.py"
echo "  - requirements.txt, Dockerfile, compose.yml, nginx.conf"
echo

read -p "Continuar com a sincronização? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${RED}Sincronização cancelada.${NC}"
    exit 1
fi

# Fazer backup do estado atual
echo -e "${YELLOW}Criando backup do estado atual...${NC}"
BACKUP_DIR="backups/sync-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp -r app templates static main.py models.py schemas.py database.py \
      requirements.txt Dockerfile compose.yml nginx.conf \
      "$BACKUP_DIR/" 2>/dev/null || true

echo -e "${GREEN}✓ Backup criado em: $BACKUP_DIR${NC}"

# Sincronizar arquivos
echo -e "${YELLOW}Sincronizando arquivos da aplicação...${NC}"

# Sincronizar diretórios
rsync -av --delete ../Moni-Personal/app/ ./app/
rsync -av --delete ../Moni-Personal/templates/ ./templates/
rsync -av --delete ../Moni-Personal/static/ ./static/
rsync -av --delete ../Moni-Personal/scripts/ ./scripts/ 2>/dev/null || true

# Sincronizar arquivos individuais
cp ../Moni-Personal/main.py ./main.py
cp ../Moni-Personal/models.py ./models.py
cp ../Moni-Personal/schemas.py ./schemas.py
cp ../Moni-Personal/database.py ./database.py
cp ../Moni-Personal/requirements.txt ./requirements.txt
cp ../Moni-Personal/Dockerfile ./Dockerfile
cp ../Moni-Personal/compose.yml ./compose.yml
cp ../Moni-Personal/nginx.conf ./nginx.conf
cp ../Moni-Personal/.dockerignore ./.dockerignore 2>/dev/null || true
cp ../Moni-Personal/Makefile ./Makefile 2>/dev/null || true

# Copiar outros arquivos Python se existirem
cp ../Moni-Personal/main_modular.py ./main_modular.py 2>/dev/null || true
cp ../Moni-Personal/migrate_db.py ./migrate_db.py 2>/dev/null || true

echo -e "${GREEN}✓ Sincronização completa!${NC}"
echo

# Mostrar diferenças
echo -e "${YELLOW}Verificando mudanças no Git...${NC}"
git status

echo
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Sincronização concluída!${NC}"
echo -e "${GREEN}============================================${NC}"
echo
echo -e "${YELLOW}Próximos passos:${NC}"
echo "1. Revise as mudanças: git diff"
echo "2. Teste localmente: docker-compose up -d"
echo "3. Commit: git add . && git commit -m 'Sync: atualização da aplicação'"
echo "4. Push: git push"
echo
echo -e "${YELLOW}Backup disponível em:${NC} $BACKUP_DIR"
