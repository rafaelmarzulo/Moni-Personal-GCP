#!/bin/bash
# ====================================
# Rollback para revisão anterior
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
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Configurações
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
REGION="${GCP_REGION:-southamerica-east1}"
SERVICE_NAME="${SERVICE_NAME:-moni-personal}"

if [ -z "$PROJECT_ID" ]; then
    log_error "Projeto GCP não configurado"
    exit 1
fi

# Listar últimas revisões
log_info "Últimas 5 revisões do serviço $SERVICE_NAME:"
gcloud run revisions list \
    --service="$SERVICE_NAME" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --limit=5 \
    --format='table(
        metadata.name,
        status.conditions[0].type:label=STATUS,
        metadata.creationTimestamp:sort=1:reverse,
        spec.containers[0].image
    )'

# Obter revisão atual e anterior
CURRENT_REVISION=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format='value(status.latestReadyRevisionName)')

PREVIOUS_REVISION=$(gcloud run revisions list \
    --service="$SERVICE_NAME" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format='value(name)' \
    --limit=2 | tail -n1)

echo ""
log_info "Revisão atual: $CURRENT_REVISION"
log_info "Revisão anterior: $PREVIOUS_REVISION"
echo ""

# Confirmar rollback
read -p "Deseja fazer rollback para $PREVIOUS_REVISION? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_error "Rollback cancelado"
    exit 0
fi

# Executar rollback
log_info "Fazendo rollback..."
gcloud run services update-traffic "$SERVICE_NAME" \
    --to-revisions="$PREVIOUS_REVISION=100" \
    --region="$REGION" \
    --project="$PROJECT_ID"

log_success "Rollback concluído para: $PREVIOUS_REVISION"

# Health check
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format='value(status.url)')

log_info "Verificando health check..."
sleep 5

if curl -sf "$SERVICE_URL/health" > /dev/null; then
    log_success "Health check passou! ✨"
else
    log_error "Health check falhou após rollback!"
    exit 1
fi

log_success "🎉 Rollback finalizado!"
