#!/bin/bash
#==============================================================================
# Script: Setup GCP Free Tier para MoniPersonal
# Descrição: Configuração inicial completa do Google Cloud Platform
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

# Configurações do projeto
readonly PROJECT_NAME="${GCP_PROJECT_NAME:-monipersonal-prod}"
readonly REGION="${GCP_REGION:-us-central1}"
readonly SERVICE_NAME="${SERVICE_NAME:-monipersonal-api}"

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

# Validação de pré-requisitos
check_prerequisites() {
    log_info "Verificando pré-requisitos..."

    # Verificar gcloud
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI não encontrado. Instale: https://cloud.google.com/sdk/docs/install"
    fi

    # Verificar autenticação
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        log_warning "Não autenticado no gcloud. Executando login..."
        gcloud auth login
    fi

    log_success "Pré-requisitos verificados"
}

# Criar ou selecionar projeto
setup_project() {
    log_info "Configurando projeto GCP: ${PROJECT_NAME}"

    # Verificar se projeto existe
    if gcloud projects describe "${PROJECT_NAME}" &> /dev/null; then
        log_warning "Projeto ${PROJECT_NAME} já existe. Usando projeto existente."
    else
        log_info "Criando novo projeto: ${PROJECT_NAME}"
        gcloud projects create "${PROJECT_NAME}" --name="MoniPersonal Production"
        log_success "Projeto criado"
    fi

    # Configurar projeto padrão
    gcloud config set project "${PROJECT_NAME}"
    log_success "Projeto configurado: ${PROJECT_NAME}"
}

# Habilitar APIs necessárias
enable_apis() {
    log_info "Habilitando APIs necessárias..."

    local apis=(
        "run.googleapis.com"                    # Cloud Run
        "cloudbuild.googleapis.com"             # Cloud Build
        "artifactregistry.googleapis.com"       # Artifact Registry
        "cloudresourcemanager.googleapis.com"   # Resource Manager
        "storage-api.googleapis.com"            # Cloud Storage
        "secretmanager.googleapis.com"          # Secret Manager
        "logging.googleapis.com"                # Cloud Logging
        "monitoring.googleapis.com"             # Cloud Monitoring
    )

    for api in "${apis[@]}"; do
        log_info "Habilitando API: ${api}"
        gcloud services enable "${api}" --quiet
    done

    log_success "APIs habilitadas com sucesso"
}

# Configurar billing (se necessário)
setup_billing() {
    log_info "Verificando configuração de billing..."

    # Obter billing account
    local billing_account
    billing_account=$(gcloud billing accounts list --format="value(name)" --limit=1)

    if [ -z "$billing_account" ]; then
        log_warning "Nenhuma conta de billing encontrada. Configure manualmente em:"
        log_warning "https://console.cloud.google.com/billing"
        read -p "Pressione ENTER após configurar billing..." -r
    else
        log_info "Vinculando projeto à conta de billing..."
        gcloud billing projects link "${PROJECT_NAME}" \
            --billing-account="${billing_account}" || true
        log_success "Billing configurado"
    fi
}

# Configurar Artifact Registry
setup_artifact_registry() {
    log_info "Configurando Artifact Registry..."

    local repo_name="monipersonal-images"

    # Criar repositório se não existir
    if ! gcloud artifacts repositories describe "${repo_name}" \
        --location="${REGION}" &> /dev/null; then

        gcloud artifacts repositories create "${repo_name}" \
            --repository-format=docker \
            --location="${REGION}" \
            --description="Docker images para MoniPersonal"

        log_success "Artifact Registry criado: ${repo_name}"
    else
        log_warning "Artifact Registry já existe: ${repo_name}"
    fi

    # Configurar autenticação Docker
    gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
    log_success "Autenticação Docker configurada"
}

# Configurar Cloud Storage para arquivos estáticos
setup_cloud_storage() {
    log_info "Configurando Cloud Storage..."

    local bucket_name="${PROJECT_NAME}-static"

    # Criar bucket se não existir
    if ! gsutil ls "gs://${bucket_name}" &> /dev/null; then
        gsutil mb -l "${REGION}" "gs://${bucket_name}"

        # Tornar público para leitura
        gsutil iam ch allUsers:objectViewer "gs://${bucket_name}"

        log_success "Bucket criado: ${bucket_name}"
    else
        log_warning "Bucket já existe: ${bucket_name}"
    fi

    # Configurar CORS
    cat > /tmp/cors.json <<'EOF'
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

    gsutil cors set /tmp/cors.json "gs://${bucket_name}"
    rm /tmp/cors.json

    log_success "Cloud Storage configurado"
}

# Criar service account para Cloud Run
setup_service_account() {
    log_info "Configurando Service Account..."

    local sa_name="monipersonal-runner"
    local sa_email="${sa_name}@${PROJECT_NAME}.iam.gserviceaccount.com"

    # Criar service account se não existir
    if ! gcloud iam service-accounts describe "${sa_email}" &> /dev/null; then
        gcloud iam service-accounts create "${sa_name}" \
            --display-name="MoniPersonal Cloud Run Service Account"

        log_success "Service Account criado: ${sa_name}"
    else
        log_warning "Service Account já existe: ${sa_name}"
    fi

    # Atribuir roles necessárias
    local roles=(
        "roles/cloudsql.client"
        "roles/secretmanager.secretAccessor"
        "roles/storage.objectViewer"
    )

    for role in "${roles[@]}"; do
        gcloud projects add-iam-policy-binding "${PROJECT_NAME}" \
            --member="serviceAccount:${sa_email}" \
            --role="${role}" \
            --quiet
    done

    log_success "Permissões configuradas para Service Account"
}

# Configurar budget alert (importante para Free Tier)
setup_budget_alert() {
    log_info "Configurando Budget Alert..."

    log_warning "Configure Budget Alert manualmente para monitorar custos:"
    log_warning "1. Acesse: https://console.cloud.google.com/billing/budgets"
    log_warning "2. Crie um budget de \$5 ou \$0 (se quiser ficar 100% no free tier)"
    log_warning "3. Configure alertas em 50%, 90%, 100%"

    read -p "Pressione ENTER para continuar..." -r
}

# Exibir resumo da configuração
show_summary() {
    echo ""
    log_success "════════════════════════════════════════════════════════════"
    log_success "🎉 Setup do GCP Free Tier Concluído com Sucesso!"
    log_success "════════════════════════════════════════════════════════════"
    echo ""
    log_info "Configurações:"
    echo "  - Projeto: ${PROJECT_NAME}"
    echo "  - Região: ${REGION}"
    echo "  - Service Name: ${SERVICE_NAME}"
    echo ""
    log_info "Próximos passos:"
    echo "  1. Configure secrets: bash scripts/gcp/setup-secrets.sh"
    echo "  2. Faça deploy: bash scripts/gcp/deploy-free-tier.sh"
    echo "  3. Configure CI/CD: bash scripts/gcp/setup-github-actions.sh"
    echo ""
    log_info "Recursos criados:"
    echo "  ✅ Projeto GCP configurado"
    echo "  ✅ APIs habilitadas"
    echo "  ✅ Artifact Registry criado"
    echo "  ✅ Cloud Storage configurado"
    echo "  ✅ Service Account criado"
    echo ""
    log_warning "Não esqueça de:"
    echo "  ⚠️  Configurar Budget Alert para monitorar custos"
    echo "  ⚠️  Revisar permissões do Service Account"
    echo "  ⚠️  Configurar backup do banco de dados"
    echo ""
}

# Função principal
main() {
    echo ""
    log_info "═══════════════════════════════════════════════════════════"
    log_info "🚀 Setup GCP Free Tier - MoniPersonal"
    log_info "═══════════════════════════════════════════════════════════"
    echo ""

    check_prerequisites
    setup_project
    setup_billing
    enable_apis
    setup_artifact_registry
    setup_cloud_storage
    setup_service_account
    setup_budget_alert
    show_summary
}

# Executar script
main "$@"
