#!/bin/bash
# ====================================
# Deploy para Google Cloud Run
# Moni Personal GCP Edition
# ====================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções helper
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar se gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    log_error "Google Cloud SDK não encontrado. Instale: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Configurações
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
REGION="${GCP_REGION:-southamerica-east1}"
SERVICE_NAME="${SERVICE_NAME:-moni-personal}"
MEMORY="${MEMORY:-512Mi}"
CPU="${CPU:-1}"
MAX_INSTANCES="${MAX_INSTANCES:-10}"
MIN_INSTANCES="${MIN_INSTANCES:-0}"
TIMEOUT="${TIMEOUT:-300}"

# Verificar projeto configurado
if [ -z "$PROJECT_ID" ]; then
    log_error "Projeto GCP não configurado. Execute: gcloud config set project PROJECT_ID"
    exit 1
fi

log_info "Projeto: $PROJECT_ID"
log_info "Região: $REGION"
log_info "Serviço: $SERVICE_NAME"
echo ""

# Confirmar deploy
read -p "Deseja continuar com o deploy? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warning "Deploy cancelado pelo usuário"
    exit 0
fi

# 1. Build da imagem com Cloud Build
log_info "Iniciando build da imagem Docker..."
gcloud builds submit \
    --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
    --project "$PROJECT_ID" \
    --timeout=15m

log_success "Imagem Docker criada: gcr.io/$PROJECT_ID/$SERVICE_NAME"

# 2. Deploy no Cloud Run
log_info "Fazendo deploy no Cloud Run..."

# Verificar se serviço já existe
if gcloud run services describe "$SERVICE_NAME" --region="$REGION" --project="$PROJECT_ID" &>/dev/null; then
    log_warning "Atualizando serviço existente: $SERVICE_NAME"
    ACTION="update"
else
    log_info "Criando novo serviço: $SERVICE_NAME"
    ACTION="create"
fi

# Deploy command
gcloud run deploy "$SERVICE_NAME" \
    --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
    --platform managed \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --allow-unauthenticated \
    --port 8080 \
    --memory "$MEMORY" \
    --cpu "$CPU" \
    --timeout "$TIMEOUT" \
    --max-instances "$MAX_INSTANCES" \
    --min-instances "$MIN_INSTANCES" \
    --set-env-vars "ENVIRONMENT=production,FORCE_HTTPS=true" \
    --set-secrets "DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest,JWT_SECRET_KEY=JWT_SECRET_KEY:latest" \
    --quiet

log_success "Deploy concluído com sucesso!"

# 3. Obter URL do serviço
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format='value(status.url)')

echo ""
log_success "Aplicação disponível em: $SERVICE_URL"

# 4. Health check
log_info "Executando health check..."
sleep 5

if curl -sf "$SERVICE_URL/health" > /dev/null; then
    log_success "Health check passou! ✨"
else
    log_error "Health check falhou. Verifique os logs:"
    echo "  gcloud run services logs tail $SERVICE_NAME --region=$REGION"
    exit 1
fi

# 5. Mostrar informações do serviço
echo ""
log_info "Informações do serviço:"
gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format='table(
        metadata.name,
        status.conditions[0].type,
        status.url,
        spec.template.spec.containers[0].resources.limits.memory,
        spec.template.spec.containers[0].resources.limits.cpu
    )'

echo ""
log_success "🎉 Deploy finalizado com sucesso!"
log_info "Para ver logs: gcloud run services logs tail $SERVICE_NAME --region=$REGION"
log_info "Para abrir no browser: gcloud run services browse $SERVICE_NAME --region=$REGION"
