# 🚀 Quick Start - Deploy no GCP Free Tier

Guia rápido para fazer deploy do **MoniPersonal** no Google Cloud Platform usando o Free Tier.

---

## ⏱️ Tempo Estimado

- **Setup inicial**: 15-20 minutos
- **Primeiro deploy**: 10-15 minutos
- **Total**: ~30-35 minutos

---

## 📋 Pré-requisitos

### 1. Conta Google Cloud
- [ ] Conta Google válida
- [ ] Free Trial ativado (US$ 300 por 90 dias) ou Always Free Tier
- [ ] Cartão de crédito para verificação

### 2. Ferramentas Instaladas
```bash
# Verificar instalações
gcloud --version    # Google Cloud SDK
git --version       # Git
docker --version    # Docker (opcional, para testes locais)
```

**Instalar gcloud CLI:**
- Linux: https://cloud.google.com/sdk/docs/install#linux
- macOS: `brew install google-cloud-sdk`
- Windows: https://cloud.google.com/sdk/docs/install#windows

### 3. Banco de Dados (Escolha uma opção)

**Opção A: Railway PostgreSQL (100% Gratuito)**
- Acesse: https://railway.app
- Crie conta com GitHub
- New Project → Provision PostgreSQL
- Copie a `DATABASE_URL`

**Opção B: Supabase PostgreSQL (100% Gratuito)**
- Acesse: https://supabase.com
- Create new project
- Settings → Database → Connection string

**Opção C: Cloud SQL (~$10/mês)**
- Use o script: `bash scripts/gcp/setup-cloudsql.sh`

---

## 🎯 Deploy em 3 Passos

### Passo 1: Setup Inicial do GCP (Uma vez)

```bash
# Clonar repositório (se ainda não tiver)
git clone https://github.com/rafaelmarzulo/Moni-Personal-GCP.git
cd Moni-Personal-GCP

# Executar setup do GCP
bash scripts/gcp/setup-gcp-free-tier.sh
```

**O que este script faz:**
- ✅ Cria projeto GCP
- ✅ Habilita APIs necessárias
- ✅ Configura Artifact Registry
- ✅ Configura Cloud Storage
- ✅ Cria Service Account com permissões

**Tempo:** ~10-15 minutos

---

### Passo 2: Configurar Secrets (Uma vez)

```bash
# Executar configuração de secrets
bash scripts/gcp/setup-secrets-interactive.sh
```

**O que você precisará fornecer:**
1. **ADMIN_PASSWORD**: Senha do admin (gerada automaticamente ou customizada)
2. **DATABASE_URL**: URL do PostgreSQL (Railway/Supabase/Cloud SQL)
3. **JWT_SECRET_KEY**: Chave JWT (gerada automaticamente)

**Tempo:** ~5 minutos

---

### Passo 3: Deploy da Aplicação

```bash
# Fazer deploy no Cloud Run
bash scripts/gcp/deploy-free-tier.sh
```

**O que este script faz:**
- ✅ Faz build da imagem Docker (usando Cloud Build)
- ✅ Faz push para Artifact Registry
- ✅ Deploy no Cloud Run (configuração Free Tier optimized)
- ✅ Executa smoke tests
- ✅ Retorna URL da aplicação

**Tempo:** ~10-15 minutos

---

## ✅ Verificar Deploy

Após o deploy, você receberá uma URL tipo:
```
https://monipersonal-api-xxxxxxxxx-uc.a.run.app
```

### Testar Endpoints:

```bash
# Health check
curl https://sua-url.run.app/health

# Ping
curl https://sua-url.run.app/ping

# Login page (browser)
open https://sua-url.run.app/login
```

---

## 🔄 Deploy Contínuo (CI/CD)

### Configurar GitHub Actions

**1. Criar Service Account Key:**

```bash
# Criar chave do service account
gcloud iam service-accounts keys create gcp-key.json \
  --iam-account=monipersonal-runner@monipersonal-prod.iam.gserviceaccount.com

# Copiar conteúdo (NÃO commitar!)
cat gcp-key.json | base64
```

**2. Adicionar GitHub Secrets:**

No GitHub: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

Adicione:
- **GCP_PROJECT_ID**: `monipersonal-prod`
- **GCP_SA_KEY**: (conteúdo do gcp-key.json em base64)

**3. Deploy Automático:**

Agora cada push para `main` fará deploy automaticamente! 🎉

---

## 💰 Monitoramento de Custos

### Configurar Budget Alert

1. Acesse: https://console.cloud.google.com/billing/budgets
2. Click: "Create Budget"
3. Nome: "MoniPersonal Monthly Budget"
4. Amount: $5 (ou $0 para ficar 100% no free tier)
5. Alerts: 50%, 90%, 100%
6. Email notifications: seu email

### Verificar Uso do Free Tier

```bash
# Verificar métricas do Cloud Run
gcloud run services describe monipersonal-api \
  --region=us-central1 \
  --format="table(status.traffic)"

# Ver logs
gcloud run services logs read monipersonal-api \
  --region=us-central1 \
  --limit=50
```

**Dashboard de Métricas:**
```
https://console.cloud.google.com/run/detail/us-central1/monipersonal-api/metrics
```

---

## 🔧 Comandos Úteis

### Logs em Tempo Real
```bash
gcloud run services logs tail monipersonal-api \
  --region=us-central1
```

### Atualizar Secrets
```bash
# Adicionar nova versão de um secret
echo -n "novo-valor" | gcloud secrets versions add SECRET_NAME --data-file=-
```

### Rollback para Versão Anterior
```bash
# Listar revisões
gcloud run revisions list --service=monipersonal-api

# Fazer rollback
gcloud run services update-traffic monipersonal-api \
  --to-revisions=REVISION_NAME=100
```

### Deletar Serviço (Limpar)
```bash
# Deletar service do Cloud Run
gcloud run services delete monipersonal-api --region=us-central1

# Deletar projeto completo (CUIDADO!)
gcloud projects delete monipersonal-prod
```

---

## 🆘 Troubleshooting

### Erro: "Permission denied"
```bash
# Re-autenticar
gcloud auth login
gcloud config set project monipersonal-prod
```

### Erro: "API not enabled"
```bash
# Habilitar manualmente
gcloud services enable run.googleapis.com
```

### Erro: "Build timeout"
```bash
# Aumentar timeout
gcloud builds submit --timeout=30m
```

### Deploy falha com erro de secrets
```bash
# Verificar secrets
gcloud secrets list

# Verificar permissões
gcloud secrets describe SECRET_NAME
```

---

## 📊 Arquitetura Implementada

```
┌─────────────────────────────────────────────┐
│        GitHub Repository                    │
│  ┌───────────────────────────────────┐     │
│  │  Push to main branch              │     │
│  └──────────┬────────────────────────┘     │
└─────────────┼──────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│      GitHub Actions (CI/CD)                 │
│  ┌─────────┬─────────┬──────────┐          │
│  │ Test    │ Security│ Build &  │          │
│  │         │ Scan    │ Deploy   │          │
│  └─────────┴─────────┴──────────┘          │
└─────────────┼──────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│   Google Cloud Platform (Free Tier)         │
│                                             │
│  ┌──────────────────────────────────┐      │
│  │  Cloud Build (Build Docker)       │      │
│  │  120 min/dia grátis              │      │
│  └────────┬─────────────────────────┘      │
│           │                                 │
│           ▼                                 │
│  ┌──────────────────────────────────┐      │
│  │  Artifact Registry (Store Image) │      │
│  │  0.5 GB grátis                   │      │
│  └────────┬─────────────────────────┘      │
│           │                                 │
│           ▼                                 │
│  ┌──────────────────────────────────┐      │
│  │  Cloud Run (Run API)             │      │
│  │  2M requests/mês grátis          │      │
│  │  Scale to zero = $0              │      │
│  └────────┬─────────────────────────┘      │
│           │                                 │
│           │ DATABASE_URL                    │
│           ▼                                 │
│  ┌──────────────────────────────────┐      │
│  │  Secret Manager (Secrets)        │      │
│  │  ADMIN_PASSWORD, JWT_SECRET, etc.│      │
│  └──────────────────────────────────┘      │
└─────────────────────────────────────────────┘
              │
              │ DATABASE_URL
              ▼
┌─────────────────────────────────────────────┐
│   Railway/Supabase PostgreSQL (External)    │
│   100% Gratuito - 5GB storage               │
└─────────────────────────────────────────────┘

Total Monthly Cost: $0 💰
```

---

## 📚 Próximos Passos

Após o deploy básico:

1. **[ ] Configurar domínio customizado**
   - Cloud Run → Mapping → Add mapping
   - Configure DNS (A record ou CNAME)

2. **[ ] Configurar SSL customizado**
   - Automático com domínio verificado
   - Certificado gerenciado pelo Google

3. **[ ] Configurar monitoring avançado**
   - Cloud Monitoring dashboard
   - Alertas customizados
   - APM integration

4. **[ ] Implementar backup automatizado**
   - Database backups
   - Cloud Storage backup policy

5. **[ ] Configurar ambientes múltiplos**
   - Staging environment
   - Development environment
   - Feature branch deployments

---

## 🔗 Links Úteis

- **GCP Console**: https://console.cloud.google.com
- **Cloud Run Dashboard**: https://console.cloud.google.com/run
- **Artifact Registry**: https://console.cloud.google.com/artifacts
- **Secret Manager**: https://console.cloud.google.com/security/secret-manager
- **Billing**: https://console.cloud.google.com/billing
- **Railway**: https://railway.app
- **Supabase**: https://supabase.com

---

## ✅ Checklist Completo

- [ ] Instalar gcloud CLI
- [ ] Criar conta GCP e ativar Free Trial
- [ ] Criar banco de dados (Railway/Supabase)
- [ ] Executar `setup-gcp-free-tier.sh`
- [ ] Executar `setup-secrets-interactive.sh`
- [ ] Executar `deploy-free-tier.sh`
- [ ] Testar aplicação (health, ping, login)
- [ ] Configurar GitHub Actions secrets
- [ ] Configurar Budget Alert
- [ ] Fazer primeiro push e validar CI/CD

---

**Deploy completo em ~30 minutos!** 🚀

**Custo estimado:** $0/mês (Free Tier) 💰

---

*Última atualização: 2025-10-21*
*Versão: 1.0.0*
