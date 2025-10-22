# 🎁 Configuração do GCP Free Tier para Moni-Personal

## 📋 Passo a Passo Completo

### 1️⃣ Ativar Google Cloud Free Trial

#### Requisitos
- [ ] Conta Google válida
- [ ] Cartão de crédito para verificação
- [ ] Primeira vez usando GCP Free Trial

#### Passos
1. Acesse: https://cloud.google.com/free
2. Clique em "Get started for free"
3. Faça login com sua conta Google
4. Preencha informações de pagamento (não será cobrado)
5. Aceite os termos e condições
6. Receba **US$ 300 em créditos** válidos por **90 dias**

---

### 2️⃣ Criar Projeto no GCP

```bash
# Via gcloud CLI
gcloud projects create monipersonal-prod --name="MoniPersonal Production"

# Configurar projeto padrão
gcloud config set project monipersonal-prod

# Verificar projeto
gcloud config get-value project
```

#### Via Console Web:
1. Acesse: https://console.cloud.google.com
2. Menu superior: "Select a project" → "New Project"
3. Nome: `monipersonal-prod`
4. Organization: (sua organização ou vazio)
5. Click "Create"

---

### 3️⃣ Habilitar APIs Necessárias

```bash
# Habilitar todas as APIs de uma vez
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  cloudresourcemanager.googleapis.com \
  storage-api.googleapis.com \
  secretmanager.googleapis.com \
  sqladmin.googleapis.com

# Verificar APIs habilitadas
gcloud services list --enabled
```

---

### 4️⃣ Configurar Cloud Run (Always Free)

#### Limites Gratuitos:
- ✅ **2 milhões** de requisições por mês
- ✅ **360.000 GB-segundos** de memória
- ✅ **180.000 vCPU-segundos** de CPU
- ✅ **1 GB** de tráfego de rede (egress América do Norte)

#### Deploy Inicial:
```bash
# Fazer deploy usando Cloud Run
cd /home/rafael/projetos/Moni-Personal-GCP

# Build e deploy em um comando
gcloud run deploy monipersonal-api \
  --source . \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --set-env-vars="ENV=production"
```

**⚠️ Configurações para Maximizar Free Tier:**
```yaml
Configuração Recomendada:
- Memory: 512Mi (ou 256Mi para economia)
- CPU: 1 (mínimo)
- Min instances: 0 (escala para zero = $0)
- Max instances: 3 (limite para não estourar free tier)
- Region: us-central1 (elegível para free tier)
```

---

### 5️⃣ Configurar Banco de Dados (Opções)

#### Opção A: Cloud SQL (PAGO - ~$10/mês)
```bash
# Criar instância PostgreSQL (menor configuração)
gcloud sql instances create monipersonal-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-size=10GB \
  --storage-type=HDD \
  --backup-start-time=03:00

# Criar database
gcloud sql databases create monipersonal \
  --instance=monipersonal-db

# Criar usuário
gcloud sql users create app_user \
  --instance=monipersonal-db \
  --password=SENHA_SEGURA
```

**💰 Custo:** ~$9.37/mês (db-f1-micro)

---

#### Opção B: Railway PostgreSQL (100% GRATUITO)

1. Acesse: https://railway.app
2. Crie conta (GitHub login)
3. New Project → Provision PostgreSQL
4. Copie a `DATABASE_URL`
5. Configure no Cloud Run:

```bash
# Adicionar DATABASE_URL ao Cloud Run
gcloud run services update monipersonal-api \
  --set-env-vars="DATABASE_URL=postgresql://user:pass@host:port/db"
```

**✅ Free Tier Railway:**
- 5 GB storage
- Backup automático
- SSL incluído
- 99.9% uptime

---

#### Opção C: Supabase PostgreSQL (100% GRATUITO)

1. Acesse: https://supabase.com
2. Create new project
3. Choose free tier
4. Copie connection string
5. Configure no Cloud Run

**✅ Free Tier Supabase:**
- 500 MB storage
- Backup diário
- Dashboard de gestão
- API REST automática

---

### 6️⃣ Configurar Secrets Manager

```bash
# Criar secrets
echo -n "sua-chave-secreta-aqui" | \
  gcloud secrets create ADMIN_PASSWORD --data-file=-

echo -n "postgresql://user:pass@host/db" | \
  gcloud secrets create DATABASE_URL --data-file=-

echo -n "seu-jwt-secret-key" | \
  gcloud secrets create JWT_SECRET_KEY --data-file=-

# Dar acesso ao Cloud Run
gcloud secrets add-iam-policy-binding ADMIN_PASSWORD \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Configurar Cloud Run para usar secrets
gcloud run services update monipersonal-api \
  --update-secrets=ADMIN_PASSWORD=ADMIN_PASSWORD:latest,\
DATABASE_URL=DATABASE_URL:latest,\
JWT_SECRET_KEY=JWT_SECRET_KEY:latest
```

---

### 7️⃣ Configurar Cloud Storage (Always Free)

```bash
# Criar bucket para arquivos estáticos
gsutil mb -l us-central1 gs://monipersonal-static

# Tornar público para leitura
gsutil iam ch allUsers:objectViewer gs://monipersonal-static

# Upload de arquivos estáticos
gsutil -m cp -r static/* gs://monipersonal-static/

# Configurar CORS (se necessário)
cat > cors.json <<EOF
[
  {
    "origin": ["https://monipersonal-api-*.run.app"],
    "method": ["GET"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://monipersonal-static
```

**✅ Free Tier Storage:**
- 5 GB armazenamento
- Classe Standard em us-east1, us-west1, us-central1

---

### 8️⃣ Configurar Cloud Build (Always Free)

```bash
# Criar cloudbuild.yaml
cat > cloudbuild.yaml <<'EOF'
steps:
  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/monipersonal-api:$SHORT_SHA', '.']

  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/monipersonal-api:$SHORT_SHA']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'monipersonal-api'
      - '--image=gcr.io/$PROJECT_ID/monipersonal-api:$SHORT_SHA'
      - '--region=us-central1'
      - '--platform=managed'

images:
  - 'gcr.io/$PROJECT_ID/monipersonal-api:$SHORT_SHA'

timeout: '20m'
EOF

# Trigger manual
gcloud builds submit --config=cloudbuild.yaml .
```

**✅ Free Tier Cloud Build:**
- 120 minutos de build por dia
- Suficiente para ~6 deploys diários

---

## 💰 Monitoramento de Custos

### 1. Configurar Budget Alert

```bash
# Via Console Web:
# 1. Billing → Budgets & alerts
# 2. Create Budget
# 3. Name: "MoniPersonal Monthly Budget"
# 4. Budget amount: $5 (ou $0 se quiser ficar no free tier)
# 5. Set email alerts: 50%, 90%, 100%
```

### 2. Ativar Cost Table

```bash
# Criar tabela de custos no BigQuery
gcloud alpha billing accounts list

# Via Console:
# Billing → Billing export → Enable BigQuery export
```

### 3. Monitorar Free Tier Usage

```bash
# Verificar uso do Cloud Run
gcloud run services describe monipersonal-api \
  --region=us-central1 \
  --format="value(status.traffic)"

# Logs de requisições (para contar)
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=monipersonal-api" \
  --limit=10 \
  --format=json
```

---

## 📊 Arquitetura Final (100% Gratuita)

```
┌─────────────────────────────────────────────────┐
│          Google Cloud Platform (Free Tier)      │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐       ┌──────────────┐      │
│  │  Cloud Run   │       │ Cloud Storage│      │
│  │  (API)       │◄─────►│ (Static)     │      │
│  │  2M req/mês  │       │ 5 GB         │      │
│  └──────┬───────┘       └──────────────┘      │
│         │                                       │
│         │ DATABASE_URL                          │
│         ▼                                       │
│  ┌──────────────────────────┐                  │
│  │   Railway/Supabase       │                  │
│  │   PostgreSQL (External)  │                  │
│  │   100% Gratuito          │                  │
│  └──────────────────────────┘                  │
│                                                 │
│  ┌──────────────┐       ┌──────────────┐      │
│  │ Cloud Build  │       │ Secrets      │      │
│  │ 120 min/dia  │       │ Manager      │      │
│  └──────────────┘       └──────────────┘      │
└─────────────────────────────────────────────────┘

Total Monthly Cost: $0 💰
```

---

## ✅ Checklist de Setup

- [ ] Criar conta GCP e ativar Free Trial (US$ 300)
- [ ] Criar projeto `monipersonal-prod`
- [ ] Habilitar APIs necessárias
- [ ] Fazer deploy no Cloud Run
- [ ] Configurar PostgreSQL (Railway/Supabase)
- [ ] Adicionar secrets no Secret Manager
- [ ] Configurar Cloud Storage para estáticos
- [ ] Configurar Cloud Build para CI/CD
- [ ] Configurar budget alerts
- [ ] Testar aplicação
- [ ] Monitorar uso do free tier

---

## 🔗 Links Úteis

- **GCP Free Tier:** https://cloud.google.com/free
- **Cloud Run Pricing:** https://cloud.google.com/run/pricing
- **Railway:** https://railway.app
- **Supabase:** https://supabase.com
- **GCP Calculator:** https://cloud.google.com/products/calculator
- **GCP Console:** https://console.cloud.google.com

---

## ⚠️ Avisos Importantes

1. **Free Trial não renova automaticamente** - Após 90 dias ou US$ 300, você precisa atualizar para conta paga
2. **Always Free continua para sempre** - Desde que fique dentro dos limites
3. **Monitore seu uso** - Configure alerts para não ter surpresas
4. **Cloud SQL não é free** - Use alternativas gratuitas (Railway/Supabase)
5. **Region matters** - Use `us-central1`, `us-west1` ou `us-east1` para free tier

---

**Data de criação:** 2025-10-21
**Válido para:** MoniPersonal GCP Deployment
