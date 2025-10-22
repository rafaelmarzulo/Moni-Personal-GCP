#!/bin/bash
# Script de Validação da Reorganização do Projeto
# Valida imports, estrutura e compatibilidade

set -e

echo "🔍 Iniciando validação da reorganização do projeto..."
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para validação
validate() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
        exit 1
    fi
}

# 1. Verificar se estamos no branch correto
echo "📌 Verificando branch..."
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" = "refactor/organize-project-structure" ]; then
    validate "Branch correto: $CURRENT_BRANCH"
else
    echo -e "${YELLOW}⚠️  Branch atual: $CURRENT_BRANCH (esperado: refactor/organize-project-structure)${NC}"
fi
echo ""

# 2. Verificar estrutura de diretórios
echo "📁 Verificando estrutura de diretórios..."
REQUIRED_DIRS=(
    "app/core"
    "app/models"
    "app/schemas"
    "app/middleware"
    "app/routes"
    "app/services"
    "app/utils"
    "infrastructure/local"
    "infrastructure/nginx"
    "templates"
    "static"
    "scripts/gcp"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}  ✅ $dir${NC}"
    else
        echo -e "${RED}  ❌ $dir (não encontrado)${NC}"
        exit 1
    fi
done
echo ""

# 3. Verificar arquivos movidos
echo "📦 Verificando arquivos movidos..."
MOVED_FILES=(
    "app/core/database.py"
    "app/core/migrate.py"
    "app/models/__init__.py"
    "app/schemas/__init__.py"
    "infrastructure/local/docker-compose.yml"
    "infrastructure/nginx/nginx.conf"
)

for file in "${MOVED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✅ $file${NC}"
    else
        echo -e "${RED}  ❌ $file (não encontrado)${NC}"
        exit 1
    fi
done
echo ""

# 4. Verificar arquivos que devem ter sido removidos
echo "🗑️  Verificando arquivos removidos..."
REMOVED_FILES=(
    "database.py"
    "models.py"
    "schemas.py"
    "migrate_db.py"
    "main_modular.py"
    "compose.yml"
    "nginx.conf"
    "__init__.py"
)

for file in "${REMOVED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${GREEN}  ✅ $file (removido corretamente)${NC}"
    else
        echo -e "${RED}  ❌ $file (ainda existe, deveria ter sido removido)${NC}"
        exit 1
    fi
done
echo ""

# 5. Verificar main.py
echo "🚀 Verificando main.py..."
if [ -f "main.py" ]; then
    # Verificar se imports foram atualizados
    if grep -q "from app.core.database import" main.py; then
        echo -e "${GREEN}  ✅ Import de database atualizado${NC}"
    else
        echo -e "${RED}  ❌ Import de database não atualizado${NC}"
        exit 1
    fi

    if grep -q "from app.models import" main.py; then
        echo -e "${GREEN}  ✅ Import de models atualizado${NC}"
    else
        echo -e "${RED}  ❌ Import de models não atualizado${NC}"
        exit 1
    fi

    if grep -q '"main:app"' main.py; then
        echo -e "${GREEN}  ✅ Uvicorn run command correto${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Uvicorn run command pode estar incorreto${NC}"
    fi
else
    echo -e "${RED}  ❌ main.py não encontrado${NC}"
    exit 1
fi
echo ""

# 6. Verificar imports nas rotas
echo "🔗 Verificando imports nas rotas..."
ROUTE_FILES=(
    "app/routes/admin.py"
    "app/routes/auth.py"
    "app/routes/public.py"
    "app/routes/student.py"
)

for file in "${ROUTE_FILES[@]}"; do
    if grep -q "from app.core.database import\|from app.models import" "$file"; then
        echo -e "${GREEN}  ✅ $file (imports atualizados)${NC}"
    else
        echo -e "${RED}  ❌ $file (imports não atualizados)${NC}"
        exit 1
    fi
done
echo ""

# 7. Verificar requirements.txt
echo "📋 Verificando requirements.txt..."
if [ -f "requirements.txt" ]; then
    validate "requirements.txt existe"
else
    echo -e "${RED}  ❌ requirements.txt não encontrado${NC}"
    exit 1
fi
echo ""

# 8. Verificar Docker
echo "🐳 Verificando Dockerfile..."
if [ -f "Dockerfile" ]; then
    validate "Dockerfile existe"
else
    echo -e "${RED}  ❌ Dockerfile não encontrado${NC}"
    exit 1
fi
echo ""

# 9. Verificar app.yaml (GCP)
echo "☁️  Verificando app.yaml (GCP)..."
if [ -f "app.yaml" ]; then
    validate "app.yaml existe"
else
    echo -e "${RED}  ❌ app.yaml não encontrado${NC}"
    exit 1
fi
echo ""

# 10. Verificar Git status
echo "🔄 Verificando Git status..."
GIT_STATUS=$(git status --porcelain)
if [ -z "$GIT_STATUS" ]; then
    echo -e "${GREEN}  ✅ Working tree limpo${NC}"
else
    echo -e "${YELLOW}  ⚠️  Existem mudanças não commitadas:${NC}"
    git status --short
fi
echo ""

# Resumo final
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}🎉 VALIDAÇÃO COMPLETA COM SUCESSO!${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "✅ Estrutura de diretórios: OK"
echo "✅ Arquivos movidos: OK"
echo "✅ Arquivos removidos: OK"
echo "✅ Imports atualizados: OK"
echo "✅ Configurações GCP: OK"
echo ""
echo "🚀 O projeto está pronto para merge!"
echo ""
