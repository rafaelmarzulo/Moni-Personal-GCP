#!/bin/bash
#==============================================================================
# Script: Deploy para GCP Cloud Run (Free Tier Optimized)
# Descrição: Deploy otimizado para maximizar uso do Free Tier
# Autor: DevOps Team
# Versão: 1.0.0
#==============================================================================

set -euo pipefail

# Cores para output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configurações
readonly PROJECT_NAME="${GCP_PROJECT_NAME:-monipersonal-prod}"
readonly REGION="${GCP_REGION:-us-central1}"
readonly SERVICE_NAME="${SERVICE_NAME:-monipersonal-api}"
readonly MEMORY="${MEMORY:-512Mi}"
readonly CPU="${CPU:-1}"
readonly MIN_INSTANCES="${MIN_INSTANCES:-0}"
readonly MAX_INSTANCES="${MAX_INSTANCES:-3}"
readonly TIMEOUT="${TIMEOUT:-60s}"
readonly CONCURRENCY="${CONCURRENCY:-80}"

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Validar pré-requisitos
check_prerequisites() {
    log_info "Validando pré-requisitos..."

    # Verificar gcloud
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI não encontrado"
    fi

    # Verificar se está no diretório correto
    if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
        log_error "Execute este script da raiz do projeto MoniPersonal"
    fi

    # Verificar projeto configurado
    local current_project
    current_project=$(gcloud config get-value project 2>/dev/null)
    if [ "${current_project}" != "${PROJECT_NAME}" ]; then
        log_warning "Projeto atual: ${current_project}"
        log_info "Mudando para projeto: ${PROJECT_NAME}"
        gcloud config set project "${PROJECT_NAME}"
    fi

    log_success "Pré-requisitos validados"
}

# Validar variáveis de ambiente
validate_environment() {
    log_info "Validando variáveis de ambiente..."

    local required_secrets=(
        "ADMIN_PASSWORD"
        "DATABASE_URL"
        "JWT_SECRET_KEY"
    )

    local missing_secrets=()
    for secret in "${required_secrets[@]}"; do
        if ! gcloud secrets describe "${secret}" --project="${PROJECT_NAME}" &> /dev/null; then
            missing_secrets+=("${secret}")
        fi
    done

    if [ ${#missing_secrets[@]} -gt 0 ]; then
        log_warning "Secrets ausentes: ${missing_secrets[*]}"
        log_warning "Execute: bash scripts/gcp/setup-secrets.sh"
        read -p "Continuar mesmo assim? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_success "Todos os secrets configurados"
    fi
}

# Build da imagem Docker
build_image() {
    log_info "Construindo imagem Docker..."

    local image_name="${REGION}-docker.pkg.dev/${PROJECT_NAME}/monipersonal-images/${SERVICE_NAME}"
    local image_tag="$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')"
    local full_image="${image_name}:${image_tag}"

    # Build usando Cloud Build (120 min/dia grátis)
    log_info "Usando Cloud Build para construir imagem..."
    gcloud builds submit \
        --tag="${full_image}" \
        --project="${PROJECT_NAME}" \
        --timeout=20m

    log_success "Imagem construída: ${full_image}"
    echo "${full_image}"
}

# Deploy no Cloud Run
deploy_cloudrun() {
    local image="$1"

    log_info "Fazendo deploy no Cloud Run..."
    log_info "Configuração Free Tier Optimized:"
    echo "  - Memory: ${MEMORY}"
    echo "  - CPU: ${CPU}"
    echo "  - Min instances: ${MIN_INSTANCES} (scale to zero = \$0)"
    echo "  - Max instances: ${MAX_INSTANCES}"
    echo "  - Concurrency: ${CONCURRENCY}"
    echo ""

    # Construir lista de secrets
    local secrets_args=""
    if gcloud secrets describe "ADMIN_PASSWORD" --project="${PROJECT_NAME}" &> /dev/null; then
        secrets_args="--set-secrets=ADMIN_PASSWORD=ADMIN_PASSWORD:latest"
    fi
    if gcloud secrets describe "DATABASE_URL" --project="${PROJECT_NAME}" &> /dev/null; then
        secrets_args="${secrets_args},DATABASE_URL=DATABASE_URL:latest"
    fi
    if gcloud secrets describe "JWT_SECRET_KEY" --project="${PROJECT_NAME}" &> /dev/null; then
        secrets_args="${secrets_args},JWT_SECRET_KEY=JWT_SECRET_KEY:latest"
    fi

    # Deploy
    gcloud run deploy "${SERVICE_NAME}" \
        --image="${image}" \
        --platform=managed \
        --region="${REGION}" \
        --allow-unauthenticated \
        --memory="${MEMORY}" \
        --cpu="${CPU}" \
        --min-instances="${MIN_INSTANCES}" \
        --max-instances="${MAX_INSTANCES}" \
        --timeout="${TIMEOUT}" \
        --concurrency="${CONCURRENCY}" \
        --port=8000 \
        --set-env-vars="ENV=production,REGION=${REGION}" \
        ${secrets_args:+$secrets_args} \
        --project="${PROJECT_NAME}" \
        --quiet

    log_success "Deploy concluído!"
}

# Obter URL do serviço
get_service_url() {
    log_info "Obtendo URL do serviço..."

    local service_url
    service_url=$(gcloud run services describe "${SERVICE_NAME}" \
        --platform=managed \
        --region="${REGION}" \
        --format="value(status.url)" \
        --project="${PROJECT_NAME}")

    log_success "Serviço disponível em: ${service_url}"
    echo "${service_url}"
}

# Executar smoke tests
run_smoke_tests() {
    local service_url="$1"

    log_info "Executando smoke tests..."

    # Test 1: Health check
    log_info "Test 1: Health check endpoint"
    if curl -sf "${service_url}/health" > /dev/null; then
        log_success "✅ Health check passou"
    else
        log_error "❌ Health check falhou"
    fi

    # Test 2: Ping
    log_info "Test 2: Ping endpoint"
    if curl -sf "${service_url}/ping" > /dev/null; then
        log_success "✅ Ping passou"
    else
        log_error "❌ Ping falhou"
    fi

    # Test 3: Login page
    log_info "Test 3: Login page"
    if curl -sf "${service_url}/login" > /dev/null; then
        log_success "✅ Login page passou"
    else
        log_warning "⚠️  Login page pode não estar respondendo"
    fi

    log_success "Smoke tests concluídos"
}

# Mostrar métricas de custo
show_cost_metrics() {
    log_info "Métricas de Free Tier..."

    log_info "Cloud Run Free Tier (mensal):"
    echo "  ✅ 2.000.000 de requisições"
    echo "  ✅ 360.000 GB-segundos de memória"
    echo "  ✅ 180.000 vCPU-segundos"
    echo "  ✅ 1 GB de egress (América do Norte)"
    echo ""

    log_info "Estimativa com configuração atual:"
    echo "  - Memory: ${MEMORY} = $(echo ${MEMORY} | sed 's/Mi/ MB/')"
    echo "  - Min instances: ${MIN_INSTANCES} (scale to zero quando sem tráfego)"
    echo "  - Custo quando idle: \$0.00/mês 💰"
    echo ""

    log_warning "Monitore o uso em:"
    echo "  https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}/metrics?project=${PROJECT_NAME}"
}

# Exibir resumo
show_summary() {
    local service_url="$1"

    echo ""
    log_success "════════════════════════════════════════════════════════════"
    log_success "🎉 Deploy Concluído com Sucesso!"
    log_success "════════════════════════════════════════════════════════════"
    echo ""
    log_info "Informações do serviço:"
    echo "  🌐 URL: ${service_url}"
    echo "  📍 Região: ${REGION}"
    echo "  🏷️  Service: ${SERVICE_NAME}"
    echo "  💾 Memory: ${MEMORY}"
    echo "  ⚙️  CPU: ${CPU}"
    echo "  📊 Instances: ${MIN_INSTANCES}-${MAX_INSTANCES}"
    echo ""
    log_info "Endpoints principais:"
    echo "  🏥 Health: ${service_url}/health"
    echo "  📡 Ping: ${service_url}/ping"
    echo "  🔐 Login: ${service_url}/login"
    echo ""
    log_info "Próximos passos:"
    echo "  1. Teste a aplicação: curl ${service_url}/health"
    echo "  2. Configure domínio customizado (opcional)"
    echo "  3. Configure CI/CD: bash scripts/gcp/setup-github-actions.sh"
    echo "  4. Monitore logs: gcloud run services logs read ${SERVICE_NAME}"
    echo ""
    log_info "Monitoramento:"
    echo "  📊 Métricas: https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}/metrics"
    echo "  📝 Logs: https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}/logs"
    echo ""
}

# Função principal
main() {
    echo ""
    log_info "═══════════════════════════════════════════════════════════"
    log_info "🚀 Deploy GCP Cloud Run (Free Tier Optimized)"
    log_info "═══════════════════════════════════════════════════════════"
    echo ""

    check_prerequisites
    validate_environment

    local image
    image=$(build_image)

    deploy_cloudrun "${image}"

    local service_url
    service_url=$(get_service_url)

    run_smoke_tests "${service_url}"
    show_cost_metrics
    show_summary "${service_url}"
}

# Executar script
main "$@"
