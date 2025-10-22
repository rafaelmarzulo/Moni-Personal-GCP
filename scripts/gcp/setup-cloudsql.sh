#!/bin/bash
# ====================================
# Configurar Cloud SQL Instance
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

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    log_error "Projeto GCP não configurado"
    exit 1
fi

# Configurações padrão
INSTANCE_NAME="${INSTANCE_NAME:-moni-personal-db}"
REGION="${GCP_REGION:-southamerica-east1}"
DB_VERSION="POSTGRES_15"
TIER="${DB_TIER:-db-f1-micro}"
STORAGE_SIZE="${STORAGE_SIZE:-10GB}"
DATABASE_NAME="monipersonal"
DB_USER="moniuser"

log_info "Projeto: $PROJECT_ID"
log_info "Instância: $INSTANCE_NAME"
log_info "Região: $REGION"
log_info "Tier: $TIER"
echo ""

# Confirmar criação
read -p "Deseja criar a instância Cloud SQL? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warning "Operação cancelada"
    exit 0
fi

# Gerar senha forte
log_info "Gerando senha segura..."
DB_PASSWORD=$(python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%&*') for _ in range(32)))")

# 1. Criar instância Cloud SQL
log_info "Criando instância Cloud SQL (isso pode levar alguns minutos)..."
gcloud sql instances create "$INSTANCE_NAME" \
    --database-version="$DB_VERSION" \
    --tier="$TIER" \
    --region="$REGION" \
    --storage-size="$STORAGE_SIZE" \
    --storage-type=SSD \
    --storage-auto-increase \
    --backup-start-time=03:00 \
    --enable-bin-log \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=04 \
    --maintenance-release-channel=production \
    --project="$PROJECT_ID" \
    --quiet

log_success "Instância Cloud SQL criada!"

# 2. Criar database
log_info "Criando database $DATABASE_NAME..."
gcloud sql databases create "$DATABASE_NAME" \
    --instance="$INSTANCE_NAME" \
    --project="$PROJECT_ID"

log_success "Database criado!"

# 3. Criar usuário
log_info "Criando usuário $DB_USER..."
gcloud sql users create "$DB_USER" \
    --instance="$INSTANCE_NAME" \
    --password="$DB_PASSWORD" \
    --project="$PROJECT_ID"

log_success "Usuário criado!"

# 4. Obter connection name
CONNECTION_NAME=$(gcloud sql instances describe "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --format='value(connectionName)')

log_success "Connection Name: $CONNECTION_NAME"

# 5. Construir DATABASE_URL
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/${DATABASE_NAME}?host=/cloudsql/${CONNECTION_NAME}"

echo ""
log_success "🎉 Cloud SQL configurado com sucesso!"
echo ""
log_info "Informações importantes (SALVE EM LOCAL SEGURO!):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Instance Name:      $INSTANCE_NAME"
echo "Connection Name:    $CONNECTION_NAME"
echo "Database:           $DATABASE_NAME"
echo "User:               $DB_USER"
echo "Password:           $DB_PASSWORD"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "DATABASE_URL:"
echo "$DATABASE_URL"
echo ""

# 6. Salvar em secret manager
echo ""
read -p "Deseja salvar DATABASE_URL no Secret Manager? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Salvando DATABASE_URL no Secret Manager..."

    if gcloud secrets describe "DATABASE_URL" --project="$PROJECT_ID" &>/dev/null; then
        log_warning "Secret DATABASE_URL já existe. Criando nova versão..."
        echo -n "$DATABASE_URL" | gcloud secrets versions add "DATABASE_URL" \
            --data-file=- \
            --project="$PROJECT_ID"
    else
        echo -n "$DATABASE_URL" | gcloud secrets create "DATABASE_URL" \
            --data-file=- \
            --replication-policy="automatic" \
            --project="$PROJECT_ID"
    fi

    # Dar permissão ao Cloud Run
    PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
    SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

    gcloud secrets add-iam-policy-binding "DATABASE_URL" \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" \
        --project="$PROJECT_ID" \
        --quiet

    log_success "DATABASE_URL salvo no Secret Manager!"
fi

# 7. Instruções para rodar migrations
echo ""
log_info "Para rodar migrations, execute:"
echo "  1. Instale o Cloud SQL Proxy:"
echo "     wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy"
echo "     chmod +x cloud_sql_proxy"
echo ""
echo "  2. Conecte ao Cloud SQL:"
echo "     ./cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5432"
echo ""
echo "  3. Em outro terminal, rode as migrations:"
echo "     export DATABASE_URL=\"postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DATABASE_NAME\""
echo "     alembic upgrade head"
echo ""

# Salvar credenciais em arquivo local (temporário)
CRED_FILE="cloud-sql-credentials.txt"
cat > "$CRED_FILE" <<EOF
# Cloud SQL Credentials - DELETE AFTER SETUP
# Generated: $(date)

Instance Name:      $INSTANCE_NAME
Connection Name:    $CONNECTION_NAME
Database:           $DATABASE_NAME
User:               $DB_USER
Password:           $DB_PASSWORD

DATABASE_URL:
$DATABASE_URL

# IMPORTANT: Delete this file after saving credentials in a secure location!
EOF

log_warning "Credenciais salvas em: $CRED_FILE"
log_warning "DELETE este arquivo após configurar!"
