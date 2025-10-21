#!/bin/bash

# 🌿 Script para criar branches seguindo o padrão do MoniPersonal
# Uso: ./scripts/create-branch.sh <tipo> <nome>
# Exemplo: ./scripts/create-branch.sh feature user-dashboard

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para mostrar uso
show_usage() {
    echo -e "${BLUE}🌿 MoniPersonal Branch Creator${NC}"
    echo ""
    echo -e "${YELLOW}Uso:${NC}"
    echo "  ./scripts/create-branch.sh <tipo> <nome-da-branch>"
    echo ""
    echo -e "${YELLOW}Tipos disponíveis:${NC}"
    echo "  feature    - Nova funcionalidade"
    echo "  fix        - Correção de bug"
    echo "  hotfix     - Correção urgente"
    echo "  docs       - Documentação"
    echo "  refactor   - Refatoração"
    echo "  test       - Testes"
    echo ""
    echo -e "${YELLOW}Exemplos:${NC}"
    echo "  ./scripts/create-branch.sh feature user-dashboard"
    echo "  ./scripts/create-branch.sh fix login-error"
    echo "  ./scripts/create-branch.sh hotfix security-patch"
    echo ""
}

# Verificar argumentos
if [ $# -ne 2 ]; then
    echo -e "${RED}❌ Erro: Número incorreto de argumentos${NC}"
    show_usage
    exit 1
fi

BRANCH_TYPE=$1
BRANCH_NAME=$2

# Tipos válidos
VALID_TYPES=("feature" "fix" "hotfix" "docs" "refactor" "test" "release")

# Verificar se tipo é válido
if [[ ! " ${VALID_TYPES[@]} " =~ " ${BRANCH_TYPE} " ]]; then
    echo -e "${RED}❌ Erro: Tipo de branch inválido: ${BRANCH_TYPE}${NC}"
    echo -e "${YELLOW}Tipos válidos: ${VALID_TYPES[*]}${NC}"
    exit 1
fi

# Validar nome da branch (apenas letras, números e hífen)
if [[ ! $BRANCH_NAME =~ ^[a-z0-9-]+$ ]]; then
    echo -e "${RED}❌ Erro: Nome da branch inválido${NC}"
    echo -e "${YELLOW}Use apenas letras minúsculas, números e hífen (-)${NC}"
    echo -e "${YELLOW}Exemplo: user-dashboard, auth-system, api-v2${NC}"
    exit 1
fi

# Nome completo da branch
FULL_BRANCH_NAME="${BRANCH_TYPE}/${BRANCH_NAME}"

echo -e "${BLUE}🚀 Criando branch: ${FULL_BRANCH_NAME}${NC}"

# Verificar se estamos no diretório correto
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Erro: Execute este script na raiz do projeto MoniPersonal${NC}"
    exit 1
fi

# Verificar se git está instalado
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Erro: Git não está instalado${NC}"
    exit 1
fi

# Verificar se é um repositório git
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Erro: Não é um repositório git${NC}"
    exit 1
fi

# Atualizar main
echo -e "${YELLOW}📥 Atualizando branch main...${NC}"
git checkout main
git pull origin main

# Verificar se branch já existe
if git show-ref --verify --quiet "refs/heads/${FULL_BRANCH_NAME}"; then
    echo -e "${RED}❌ Erro: Branch ${FULL_BRANCH_NAME} já existe${NC}"
    exit 1
fi

# Criar e mudar para nova branch
echo -e "${YELLOW}🌿 Criando branch ${FULL_BRANCH_NAME}...${NC}"
git checkout -b "$FULL_BRANCH_NAME"

# Confirmar criação
echo -e "${GREEN}✅ Branch ${FULL_BRANCH_NAME} criada com sucesso!${NC}"
echo ""
echo -e "${BLUE}📋 Próximos passos:${NC}"
echo -e "1. Fazer suas alterações"
echo -e "2. Fazer commit: ${YELLOW}git commit -m \"${BRANCH_TYPE}: sua mensagem\"${NC}"
echo -e "3. Push da branch: ${YELLOW}git push -u origin ${FULL_BRANCH_NAME}${NC}"
echo -e "4. Criar Pull Request no GitHub"
echo ""
echo -e "${BLUE}💡 Dicas:${NC}"
echo -e "- Use commits pequenos e focados"
echo -e "- Teste sua funcionalidade antes do PR"
echo -e "- Preencha o template do Pull Request"
echo -e "- Siga as boas práticas do BRANCH_WORKFLOW.md"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"