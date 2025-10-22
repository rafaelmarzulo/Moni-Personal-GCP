#!/bin/bash

# 📝 Script para fazer commits seguindo padrões do MoniPersonal
# Uso: ./scripts/commit.sh <tipo> <mensagem>
# Exemplo: ./scripts/commit.sh feat "adicionar dashboard do usuário"

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para mostrar uso
show_usage() {
    echo -e "${BLUE}📝 MoniPersonal Commit Helper${NC}"
    echo ""
    echo -e "${YELLOW}Uso:${NC}"
    echo '  ./scripts/commit.sh <tipo> "mensagem do commit"'
    echo ""
    echo -e "${YELLOW}Tipos disponíveis:${NC}"
    echo "  feat      - Nova funcionalidade"
    echo "  fix       - Correção de bug"
    echo "  docs      - Documentação"
    echo "  style     - Formatação/estilo"
    echo "  refactor  - Refatoração"
    echo "  test      - Testes"
    echo "  chore     - Manutenção"
    echo "  perf      - Performance"
    echo "  security  - Segurança"
    echo ""
    echo -e "${YELLOW}Exemplos:${NC}"
    echo '  ./scripts/commit.sh feat "implementar rate limiting"'
    echo '  ./scripts/commit.sh fix "corrigir erro de login"'
    echo '  ./scripts/commit.sh docs "atualizar README"'
    echo ""
}

# Verificar argumentos
if [ $# -ne 2 ]; then
    echo -e "${RED}❌ Erro: Número incorreto de argumentos${NC}"
    show_usage
    exit 1
fi

COMMIT_TYPE=$1
COMMIT_MESSAGE=$2

# Tipos válidos
VALID_TYPES=("feat" "fix" "docs" "style" "refactor" "test" "chore" "perf" "security" "hotfix")

# Verificar se tipo é válido
if [[ ! " ${VALID_TYPES[@]} " =~ " ${COMMIT_TYPE} " ]]; then
    echo -e "${RED}❌ Erro: Tipo de commit inválido: ${COMMIT_TYPE}${NC}"
    echo -e "${YELLOW}Tipos válidos: ${VALID_TYPES[*]}${NC}"
    exit 1
fi

# Verificar se mensagem não está vazia
if [ -z "$COMMIT_MESSAGE" ]; then
    echo -e "${RED}❌ Erro: Mensagem do commit não pode estar vazia${NC}"
    exit 1
fi

# Verificar se mensagem começa com minúscula
FIRST_CHAR=${COMMIT_MESSAGE:0:1}
if [[ $FIRST_CHAR =~ [A-Z] ]]; then
    echo -e "${YELLOW}⚠️ Aviso: Mensagem deve começar com letra minúscula${NC}"
    echo -e "${YELLOW}Convertendo automaticamente...${NC}"
    COMMIT_MESSAGE=$(echo "$COMMIT_MESSAGE" | sed 's/./\L&/')
fi

# Verificar se estamos no diretório correto
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Erro: Execute este script na raiz do projeto MoniPersonal${NC}"
    exit 1
fi

# Verificar se git está instalado
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Erro: Git não está instalizado${NC}"
    exit 1
fi

# Verificar se é um repositório git
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Erro: Não é um repositório git${NC}"
    exit 1
fi

# Verificar se há mudanças para commit
if ! git diff --cached --exit-code >/dev/null; then
    HAS_STAGED=true
else
    HAS_STAGED=false
fi

if ! git diff --exit-code >/dev/null; then
    HAS_UNSTAGED=true
else
    HAS_UNSTAGED=false
fi

if [ "$HAS_STAGED" = false ] && [ "$HAS_UNSTAGED" = false ]; then
    echo -e "${YELLOW}⚠️ Nenhuma mudança encontrada para commit${NC}"
    exit 0
fi

# Se há mudanças não staged, perguntar se quer adicionar
if [ "$HAS_UNSTAGED" = true ] && [ "$HAS_STAGED" = false ]; then
    echo -e "${YELLOW}📋 Mudanças encontradas (não adicionadas ao stage):${NC}"
    git status --porcelain
    echo ""
    read -p "Deseja adicionar todas as mudanças ao commit? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        echo -e "${GREEN}✅ Arquivos adicionados ao stage${NC}"
    else
        echo -e "${YELLOW}Use 'git add <arquivo>' para selecionar arquivos específicos${NC}"
        exit 0
    fi
fi

# Mostrar arquivos que serão commitados
echo -e "${BLUE}📋 Arquivos no commit:${NC}"
git diff --cached --name-status

# Formar mensagem do commit
FULL_COMMIT_MESSAGE="${COMMIT_TYPE}: ${COMMIT_MESSAGE}"

# Adicionar assinatura do Claude Code
COMMIT_BODY="

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo ""
echo -e "${BLUE}📝 Mensagem do commit:${NC}"
echo -e "${GREEN}${FULL_COMMIT_MESSAGE}${NC}"

# Confirmar commit
echo ""
read -p "Confirma o commit? (Y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo -e "${YELLOW}❌ Commit cancelado${NC}"
    exit 0
fi

# Executar commit
echo -e "${YELLOW}📝 Executando commit...${NC}"

# Usar heredoc para commit com corpo
git commit -m "$(cat <<EOF
${FULL_COMMIT_MESSAGE}${COMMIT_BODY}
EOF
)"

echo -e "${GREEN}✅ Commit realizado com sucesso!${NC}"

# Mostrar informações da branch
CURRENT_BRANCH=$(git branch --show-current)
echo ""
echo -e "${BLUE}📍 Branch atual: ${GREEN}${CURRENT_BRANCH}${NC}"

# Verificar se é uma branch de feature/fix
if [[ $CURRENT_BRANCH =~ ^(feature|fix|hotfix|docs|refactor)/ ]]; then
    echo -e "${BLUE}💡 Próximos passos:${NC}"
    echo -e "1. Continue desenvolvendo ou"
    echo -e "2. Faça push: ${YELLOW}git push -u origin ${CURRENT_BRANCH}${NC}"
    echo -e "3. Crie Pull Request quando pronto"
else
    echo -e "${YELLOW}⚠️ Você está na branch: ${CURRENT_BRANCH}${NC}"
    echo -e "${YELLOW}Considere usar uma branch específica para features/fixes${NC}"
fi

echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"