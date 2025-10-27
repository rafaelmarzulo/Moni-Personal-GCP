#!/bin/bash

# Script para corrigir permissões da service account do GitHub Actions
# Execute este script após fazer login com gcloud auth login

set -e

PROJECT_ID="monipersonal-prod"
SERVICE_ACCOUNT="github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com"
REPOSITORY="moni-personal-repo"
REGION="us-central1"

echo "🔐 Configurando permissões para GitHub Actions..."
echo "Projeto: $PROJECT_ID"
echo "Service Account: $SERVICE_ACCOUNT"
echo ""

# Verificar se está logado
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "❌ Não está autenticado. Execute: gcloud auth login"
    exit 1
fi

echo "✅ Verificando conta ativa..."
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
echo "Conta ativa: $ACTIVE_ACCOUNT"
echo ""

# Permissões a nível de projeto
echo "📋 Adicionando permissões de projeto..."

ROLES=(
    "roles/artifactregistry.admin"
    "roles/run.admin"
    "roles/storage.admin"
    "roles/cloudbuild.builds.builder"
    "roles/iam.serviceAccountUser"
)

for ROLE in "${ROLES[@]}"; do
    echo "  → Adicionando $ROLE..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member=serviceAccount:$SERVICE_ACCOUNT \
        --role=$ROLE \
        --quiet
done

# Permissões específicas no repositório
echo ""
echo "📦 Adicionando permissões no repositório Artifact Registry..."
gcloud artifacts repositories add-iam-policy-binding $REPOSITORY \
    --location=$REGION \
    --member=serviceAccount:$SERVICE_ACCOUNT \
    --role=roles/artifactregistry.writer \
    --quiet

echo ""
echo "🔍 Verificando permissões..."

echo "Permissões no projeto:"
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:$SERVICE_ACCOUNT"

echo ""
echo "Permissões no repositório:"
gcloud artifacts repositories get-iam-policy $REPOSITORY \
    --location=$REGION

echo ""
echo "✅ Configuração concluída!"
echo ""
echo "🚀 Próximos passos:"
echo "1. Certifique-se de que atualizou a secret GCP_SA_KEY no GitHub"
echo "2. Execute o workflow novamente"
echo ""