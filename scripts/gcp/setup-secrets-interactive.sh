#!/bin/bash
#==============================================================================
# Script: Setup de Secrets no GCP Secret Manager (Interativo)
# Descrição: Configuração segura de secrets com validação
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
readonly SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-monipersonal-runner@${PROJECT_NAME}.iam.gserviceaccount.com}"

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

# Gerar senha segura
generate_secure_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Gerar JWT secret
generate_jwt_secret() {
    openssl rand -hex 32
}

# Criar secret no GCP
create_secret() {
    local secret_name="$1"
    local secret_value="$2"
    local description="$3"

    log_info "Criando secret: ${secret_name}"

    # Verificar se secret já existe
    if gcloud secrets describe "${secret_name}" --project="${PROJECT_NAME}" &> /dev/null; then
        log_warning "Secret ${secret_name} já existe"
        read -p "Sobrescrever? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi

        # Adicionar nova versão
        echo -n "${secret_value}" | gcloud secrets versions add "${secret_name}" \
            --data-file=- \
            --project="${PROJECT_NAME}"

        log_success "Secret atualizado: ${secret_name}"
    else
        # Criar novo secret
        echo -n "${secret_value}" | gcloud secrets create "${secret_name}" \
            --data-file=- \
            --replication-policy="automatic" \
            --project="${PROJECT_NAME}"

        log_success "Secret criado: ${secret_name}"
    fi

    # Dar acesso ao service account
    gcloud secrets add-iam-policy-binding "${secret_name}" \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/secretmanager.secretAccessor" \
        --project="${PROJECT_NAME}" \
        --quiet

    log_success "Permissões configuradas para ${secret_name}"
}

# Setup ADMIN_PASSWORD
setup_admin_password() {
    echo ""
    log_info "═══ Configuração: ADMIN_PASSWORD ═══"
    echo ""

    log_info "Este é o password do usuário admin da aplicação."
    log_warning "IMPORTANTE: Guarde este password em local seguro!"
    echo ""

    local password
    read -p "Usar password gerado automaticamente? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        read -sp "Digite o password do admin: " password
        echo
        read -sp "Confirme o password: " password_confirm
        echo

        if [ "${password}" != "${password_confirm}" ]; then
            log_error "Passwords não conferem!"
        fi

        if [ ${#password} -lt 8 ]; then
            log_error "Password deve ter no mínimo 8 caracteres!"
        fi
    else
        password=$(generate_secure_password)
        log_success "Password gerado: ${password}"
        log_warning "GUARDE ESTE PASSWORD EM LOCAL SEGURO!"
        read -p "Pressione ENTER para continuar..." -r
    fi

    create_secret "ADMIN_PASSWORD" "${password}" "Admin password for MoniPersonal"
}

# Setup DATABASE_URL
setup_database_url() {
    echo ""
    log_info "═══ Configuração: DATABASE_URL ═══"
    echo ""

    log_info "Opções de banco de dados:"
    echo "  1. Railway PostgreSQL (Gratuito)"
    echo "  2. Supabase PostgreSQL (Gratuito)"
    echo "  3. Cloud SQL PostgreSQL (Pago ~\$10/mês)"
    echo "  4. Fornecer URL customizada"
    echo ""

    local choice
    read -p "Escolha uma opção (1-4): " -n 1 -r choice
    echo

    local database_url=""
    case $choice in
        1)
            log_info "Railway PostgreSQL:"
            echo "  1. Acesse: https://railway.app"
            echo "  2. Crie um projeto novo"
            echo "  3. Provision PostgreSQL"
            echo "  4. Copie a DATABASE_URL"
            echo ""
            read -p "Cole a DATABASE_URL do Railway: " database_url
            ;;
        2)
            log_info "Supabase PostgreSQL:"
            echo "  1. Acesse: https://supabase.com"
            echo "  2. Create new project"
            echo "  3. Settings → Database → Connection string"
            echo "  4. Copie a connection string"
            echo ""
            read -p "Cole a DATABASE_URL do Supabase: " database_url
            ;;
        3)
            log_info "Cloud SQL PostgreSQL:"
            echo "  Execute: bash scripts/gcp/setup-cloudsql.sh"
            echo "  Depois volte aqui para configurar a URL"
            echo ""
            read -p "Cole a DATABASE_URL do Cloud SQL: " database_url
            ;;
        4)
            read -p "Cole sua DATABASE_URL customizada: " database_url
            ;;
        *)
            log_error "Opção inválida!"
            ;;
    esac

    # Validar formato básico da URL
    if [[ ! $database_url =~ ^postgres(ql)?:// ]]; then
        log_error "DATABASE_URL inválida! Deve começar com postgres:// ou postgresql://"
    fi

    create_secret "DATABASE_URL" "${database_url}" "PostgreSQL connection string"
}

# Setup JWT_SECRET_KEY
setup_jwt_secret() {
    echo ""
    log_info "═══ Configuração: JWT_SECRET_KEY ═══"
    echo ""

    log_info "Chave secreta para assinatura de tokens JWT."
    echo ""

    local jwt_secret
    read -p "Gerar chave automaticamente? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        read -sp "Digite a JWT secret key (mín. 32 caracteres): " jwt_secret
        echo

        if [ ${#jwt_secret} -lt 32 ]; then
            log_error "JWT secret deve ter no mínimo 32 caracteres!"
        fi
    else
        jwt_secret=$(generate_jwt_secret)
        log_success "JWT secret gerado: ${jwt_secret}"
    fi

    create_secret "JWT_SECRET_KEY" "${jwt_secret}" "JWT signing secret key"
}

# Setup secrets opcionais
setup_optional_secrets() {
    echo ""
    log_info "═══ Secrets Opcionais ═══"
    echo ""

    read -p "Configurar secrets opcionais? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi

    # EMAIL_HOST
    read -p "Configurar EMAIL_HOST para envio de emails? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        local email_host email_port email_user email_pass
        read -p "SMTP Host (ex: smtp.gmail.com): " email_host
        read -p "SMTP Port (ex: 587): " email_port
        read -p "SMTP User: " email_user
        read -sp "SMTP Password: " email_pass
        echo

        create_secret "EMAIL_HOST" "${email_host}" "SMTP host"
        create_secret "EMAIL_PORT" "${email_port}" "SMTP port"
        create_secret "EMAIL_USER" "${email_user}" "SMTP user"
        create_secret "EMAIL_PASSWORD" "${email_pass}" "SMTP password"
    fi
}

# Listar secrets criados
list_secrets() {
    echo ""
    log_info "═══ Secrets Configurados ═══"
    echo ""

    gcloud secrets list --project="${PROJECT_NAME}" --format="table(name,createTime)"

    echo ""
    log_info "Para ver um secret:"
    echo "  gcloud secrets versions access latest --secret=SECRET_NAME"
    echo ""
}

# Validar secrets
validate_secrets() {
    log_info "Validando secrets..."

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
        log_error "Secrets ausentes: ${missing_secrets[*]}"
    else
        log_success "Todos os secrets obrigatórios configurados!"
    fi
}

# Exibir resumo
show_summary() {
    echo ""
    log_success "════════════════════════════════════════════════════════════"
    log_success "🎉 Secrets Configurados com Sucesso!"
    log_success "════════════════════════════════════════════════════════════"
    echo ""
    log_info "Secrets criados no projeto: ${PROJECT_NAME}"
    echo ""
    log_warning "IMPORTANTE:"
    echo "  ⚠️  Guarde o ADMIN_PASSWORD em local seguro (1Password, LastPass, etc.)"
    echo "  ⚠️  Nunca commite secrets no repositório Git"
    echo "  ⚠️  Use Secret Manager para todos os ambientes"
    echo ""
    log_info "Próximos passos:"
    echo "  1. Faça deploy: bash scripts/gcp/deploy-free-tier.sh"
    echo "  2. Teste a aplicação"
    echo "  3. Configure CI/CD: bash scripts/gcp/setup-github-actions.sh"
    echo ""
}

# Função principal
main() {
    echo ""
    log_info "═══════════════════════════════════════════════════════════"
    log_info "🔐 Setup de Secrets - GCP Secret Manager"
    log_info "═══════════════════════════════════════════════════════════"
    echo ""

    log_warning "Este script irá configurar secrets sensíveis."
    log_warning "Certifique-se de estar em ambiente seguro!"
    echo ""
    read -p "Continuar? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Operação cancelada."
        exit 0
    fi

    # Verificar projeto
    local current_project
    current_project=$(gcloud config get-value project 2>/dev/null)
    if [ "${current_project}" != "${PROJECT_NAME}" ]; then
        log_info "Configurando projeto: ${PROJECT_NAME}"
        gcloud config set project "${PROJECT_NAME}"
    fi

    setup_admin_password
    setup_database_url
    setup_jwt_secret
    setup_optional_secrets
    list_secrets
    validate_secrets
    show_summary
}

# Executar script
main "$@"
