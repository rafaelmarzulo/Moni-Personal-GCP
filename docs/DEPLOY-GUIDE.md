# 🚀 Guia Rápido de Deploy - Moni Personal GCP

## 📋 Índice
1. [Pré-requisitos](#pré-requisitos)
2. [Deploy no Cloud Run (Recomendado)](#deploy-no-cloud-run)
3. [Deploy no App Engine](#deploy-no-app-engine)
4. [Configuração do Cloud SQL](#configuração-do-cloud-sql)
5. [Variáveis de Ambiente](#variáveis-de-ambiente)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Pré-requisitos

### 1. Instalar Google Cloud SDK
```bash
# Linux/WSL
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Ou via package manager
# Ubuntu/Debian
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt-get update && sudo apt-get install google-cloud-sdk
```

### 2. Autenticar no GCP
```bash
# Login
gcloud auth login

# Configurar projeto
gcloud config set project YOUR_PROJECT_ID

# Listar projetos
gcloud projects list
```

### 3. Habilitar APIs necessárias
```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com
```

---

## 🐳 Deploy no Cloud Run (Recomendado)

### Por que Cloud Run?
- ✅ Serverless (pague apenas pelo uso)
- ✅ Auto-scaling automático (0 a milhares de instâncias)
- ✅ Deploy em segundos
- ✅ HTTPS automático
- ✅ Mais barato para aplicações com tráfego variável

### Passo 1: Build da Imagem
```bash
# Definir variáveis
export PROJECT_ID=$(gcloud config get-value project)
export REGION=southamerica-east1
export SERVICE_NAME=moni-personal

# Build usando Cloud Build (recomendado)
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# OU build local e push
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME .
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME
```

### Passo 2: Deploy
```bash
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars ENVIRONMENT=production,FORCE_HTTPS=true \
  --set-secrets DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest
```

### Passo 3: Configurar Domínio Customizado (Opcional)
```bash
# Mapear domínio
gcloud run domain-mappings create \
  --service $SERVICE_NAME \
  --domain seu-dominio.com.br \
  --region $REGION
```

---

## 📦 Deploy no App Engine

### Por que App Engine?
- ✅ Zero configuração de infraestrutura
- ✅ Integração nativa com Cloud SQL
- ✅ Versioning e traffic splitting
- ✅ Mais previsível para aplicações com tráfego constante

### Passo 1: Deploy
```bash
# Deploy direto (usa app.yaml)
gcloud app deploy app.yaml

# Especificar projeto e região
gcloud app deploy \
  --project=YOUR_PROJECT_ID \
  --version=v1 \
  --quiet
```

### Passo 2: Visualizar
```bash
# Abrir no browser
gcloud app browse

# Ver logs
gcloud app logs tail -s default
```

### Passo 3: Gerenciar Versões
```bash
# Listar versões
gcloud app versions list

# Traffic splitting (blue/green deployment)
gcloud app services set-traffic default \
  --splits v2=0.5,v1=0.5

# Promover versão
gcloud app versions migrate v2
```

---

## 🗄️ Configuração do Cloud SQL

### Passo 1: Criar Instância PostgreSQL
```bash
export INSTANCE_NAME=moni-personal-db
export DB_VERSION=POSTGRES_15
export REGION=southamerica-east1

gcloud sql instances create $INSTANCE_NAME \
  --database-version=$DB_VERSION \
  --tier=db-f1-micro \
  --region=$REGION \
  --storage-size=10GB \
  --storage-type=SSD \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --enable-bin-log \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=04
```

### Passo 2: Criar Database e User
```bash
# Criar database
gcloud sql databases create monipersonal \
  --instance=$INSTANCE_NAME

# Criar usuário
gcloud sql users create moniuser \
  --instance=$INSTANCE_NAME \
  --password=STRONG_PASSWORD_HERE

# Obter connection name
gcloud sql instances describe $INSTANCE_NAME \
  --format='value(connectionName)'
```

### Passo 3: Configurar Conexão

**Para Cloud Run:**
```bash
gcloud run services update $SERVICE_NAME \
  --add-cloudsql-instances $PROJECT_ID:$REGION:$INSTANCE_NAME \
  --region $REGION
```

**Para App Engine:**
Adicionar no `app.yaml`:
```yaml
vpc_access_connector:
  name: projects/PROJECT_ID/locations/REGION/connectors/CONNECTOR_NAME
```

### Passo 4: Rodar Migrations
```bash
# Conectar via proxy local
cloud_sql_proxy -instances=$PROJECT_ID:$REGION:$INSTANCE_NAME=tcp:5432

# Em outro terminal
export DATABASE_URL="postgresql://moniuser:password@localhost:5432/monipersonal"
alembic upgrade head
```

---

## 🔐 Variáveis de Ambiente

### Usando Secret Manager (Recomendado)

#### Criar Secrets
```bash
# SECRET_KEY
echo -n "$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" | \
  gcloud secrets create SECRET_KEY --data-file=-

# DATABASE_URL
echo -n "postgresql://user:pass@/db?host=/cloudsql/PROJECT:REGION:INSTANCE" | \
  gcloud secrets create DATABASE_URL --data-file=-

# JWT_SECRET_KEY
echo -n "$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" | \
  gcloud secrets create JWT_SECRET_KEY --data-file=-
```

#### Dar Permissão ao Cloud Run
```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

gcloud secrets add-iam-policy-binding SECRET_KEY \
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding DATABASE_URL \
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### Usar no Deploy
```bash
gcloud run deploy $SERVICE_NAME \
  --set-secrets="SECRET_KEY=SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest"
```

---

## 📊 Monitoramento

### Cloud Logging
```bash
# Ver logs em tempo real
gcloud run services logs tail $SERVICE_NAME --region=$REGION

# Filtrar por severidade
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit 50
```

### Cloud Monitoring
```bash
# Abrir dashboard no browser
gcloud alpha monitoring dashboards list
```

### Criar Alertas
```bash
# Criar alert policy para erros
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05
```

---

## 🛠️ Troubleshooting

### Problema: Container não inicia
```bash
# Ver logs detalhados
gcloud run services logs read $SERVICE_NAME --region=$REGION --limit=100

# Testar localmente
docker run -p 8080:8080 -e PORT=8080 gcr.io/$PROJECT_ID/$SERVICE_NAME
```

### Problema: Erro de conexão com Cloud SQL
```bash
# Verificar se Cloud SQL connector está ativo
gcloud sql instances describe $INSTANCE_NAME

# Testar conexão com proxy
cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5432

# Verificar permissões
gcloud projects get-iam-policy $PROJECT_ID
```

### Problema: Secret Manager não acessível
```bash
# Listar secrets
gcloud secrets list

# Verificar permissões
gcloud secrets get-iam-policy SECRET_KEY

# Adicionar permissão
gcloud secrets add-iam-policy-binding SECRET_KEY \
  --member="serviceAccount:SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"
```

### Problema: Build falha
```bash
# Ver histórico de builds
gcloud builds list

# Ver logs de build específico
gcloud builds log BUILD_ID

# Testar build local
docker build -t test .
```

---

## 🚀 Scripts de Deploy Automatizado

### deploy-cloud-run.sh
```bash
#!/bin/bash
set -e

PROJECT_ID=$(gcloud config get-value project)
REGION="southamerica-east1"
SERVICE_NAME="moni-personal"

echo "🏗️  Building image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10 \
  --set-secrets="SECRET_KEY=SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest"

echo "✅ Deploy completed!"
gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)'
```

### rollback.sh
```bash
#!/bin/bash
PREVIOUS_REVISION=$(gcloud run revisions list --service=$SERVICE_NAME --region=$REGION --format='value(name)' --limit=2 | tail -n1)

gcloud run services update-traffic $SERVICE_NAME \
  --to-revisions=$PREVIOUS_REVISION=100 \
  --region=$REGION

echo "✅ Rolled back to: $PREVIOUS_REVISION"
```

---

## 📚 Recursos Adicionais

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [App Engine Documentation](https://cloud.google.com/appengine/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)

---

## 💰 Estimativa de Custos

### Cloud Run (Tráfego Médio)
- 1M requests/mês: ~$10-15/mês
- 512Mi RAM, 1 vCPU
- Incluindo Cloud SQL db-f1-micro: ~$25/mês

### App Engine (Standard)
- F2 instance: ~$50-100/mês
- Incluindo Cloud SQL: ~$75-125/mês

### Otimizações
- Use `--min-instances=0` em Cloud Run para economizar
- Configure auto-scaling adequadamente
- Use cache (Redis) para reduzir queries ao banco

---

**Última atualização:** 2025-10-21
**Versão:** 1.0
**Autor:** Moni Personal Team
