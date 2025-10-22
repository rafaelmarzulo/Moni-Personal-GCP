#!/bin/bash
# ====================================
# Configurar Secrets no Secret Manager
# Moni Personal GCP Edition
# ====================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Verificar gcloud
if ! command -v gcloud &> /dev/null; then
    log_error "Google Cloud SDK não encontrado"
    exit 1
fi

# Verificar python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 não encontrado"
    exit 1
fi

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    log_error "Projeto GCP não configurado"
    exit 1
fi

log_info "Projeto: $PROJECT_ID"
echo ""

# Função para criar secret
create_secret() {
    local SECRET_NAME=$1
    local SECRET_VALUE=$2

    # Verificar se secret já existe
    if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
        log_warning "Secret $SECRET_NAME já existe. Criando nova versão..."
        echo -n "$SECRET_VALUE" | gcloud secrets versions add "$SECRET_NAME" \
            --data-file=- \
            --project="$PROJECT_ID"
    else
        log_info "Criando secret $SECRET_NAME..."
        echo -n "$SECRET_VALUE" | gcloud secrets create "$SECRET_NAME" \
            --data-file=- \
            --replication-policy="automatic" \
            --project="$PROJECT_ID"
    fi

    log_success "Secret $SECRET_NAME configurado"
}

# Função para gerar token seguro
generate_token() {
    python3 -c "import secrets; print(secrets.token_urlsafe(64))"
}

# 1. SECRET_KEY
log_info "Gerando SECRET_KEY..."
SECRET_KEY=$(generate_token)
create_secret "SECRET_KEY" "$SECRET_KEY"

# 2. JWT_SECRET_KEY
log_info "Gerando JWT_SECRET_KEY..."
JWT_SECRET_KEY=$(generate_token)
create_secret "JWT_SECRET_KEY" "$JWT_SECRET_KEY"

# 3. SESSION_SECRET
log_info "Gerando SESSION_SECRET..."
SESSION_SECRET=$(generate_token)
create_secret "SESSION_SECRET" "$SESSION_SECRET"

# 4. DATABASE_URL (precisa ser configurado manualmente)
echo ""
log_warning "DATABASE_URL precisa ser configurado manualmente"
log_info "Formato: postgresql://user:password@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE"
echo ""
read -p "Deseja configurar DATABASE_URL agora? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Digite a DATABASE_URL (ex: postgresql://user:pass@/db?host=/cloudsql/...):"
    read -r DATABASE_URL
    create_secret "DATABASE_URL" "$DATABASE_URL"
fi

# 5. Configurar permissões para Cloud Run
echo ""
log_info "Configurando permissões IAM..."

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

log_info "Service Account: $SERVICE_ACCOUNT"

# Lista de secrets para dar permissão
SECRETS=("SECRET_KEY" "JWT_SECRET_KEY" "SESSION_SECRET")

# Adicionar DATABASE_URL se foi configurado
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SECRETS+=("DATABASE_URL")
fi

for SECRET_NAME in "${SECRETS[@]}"; do
    if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
        log_info "Dando permissão ao Cloud Run para acessar $SECRET_NAME..."
        gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/secretmanager.secretAccessor" \
            --project="$PROJECT_ID" \
            --quiet
        log_success "Permissão configurada para $SECRET_NAME"
    fi
done

echo ""
log_success "🎉 Secrets configurados com sucesso!"
log_info "Liste os secrets com: gcloud secrets list --project=$PROJECT_ID"
