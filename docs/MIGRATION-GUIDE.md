# 📦 Guia de Migração - Moni-Personal para GCP

Este guia documenta como este projeto foi organizado a partir do projeto original DigitalOcean.

---

## 🔄 **Histórico de Migração**

### **Repositório Original: Moni-Personal**
- **Platform**: DigitalOcean App Platform
- **Architecture**: Docker Compose tradicional
- **Location**: `/home/rafael/projetos/Moni-Personal`
- **Status**: ✅ Mantido e em produção

### **Novo Repositório: Moni-Personal-GCP**
- **Platform**: Google Cloud Platform (GKE)
- **Architecture**: Cloud Native (Kubernetes)
- **Location**: `/home/rafael/projetos/Moni-Personal-GCP`
- **Status**: ✅ Projeto showcase separado

---

## 📁 **O Que Foi Copiado**

### **Application Code (Mantido Idêntico)**
```
✅ app/                    # Application modules
✅ templates/              # HTML templates
✅ static/                 # CSS, JS, images
✅ main.py                 # FastAPI application
✅ models.py               # Database models
✅ schemas.py              # Pydantic schemas
✅ database.py             # Database connection
✅ requirements.txt        # Python dependencies
✅ Dockerfile              # Container image
✅ compose.yml             # Docker Compose (para teste local)
✅ nginx.conf              # Nginx config
```

### **Novos Arquivos (Específicos para GCP)**
```
🆕 infrastructure/         # Toda infraestrutura GCP
🆕 .github/workflows/      # CI/CD pipelines
🆕 DEPLOYMENT-GCP.md       # Guia de deploy GCP
🆕 SHOWCASE-GUIDE.md       # Guia de apresentação
🆕 QUICK-REFERENCE.md      # Comandos rápidos
🆕 PROJETO-CRIADO.md       # Resumo do projeto
🆕 README.md               # README específico GCP
🆕 .gitignore              # Git ignore rules
```

---

## 🚫 **O Que NÃO Foi Copiado**

### **Arquivos Específicos do DigitalOcean**
- Configurações específicas da DigitalOcean
- Histórico Git do projeto original
- Arquivos temporários e logs
- Variáveis de ambiente (`.env`)
- Dados de banco de dados local

---

## 🔑 **Diferenças Chave**

| Aspecto | Moni-Personal (Original) | Moni-Personal-GCP (Novo) |
|---------|-------------------------|--------------------------|
| **Platform** | DigitalOcean App Platform | Google Cloud Platform |
| **Deployment** | Git push deploy | Terraform + Kubernetes |
| **Infrastructure** | Managed by platform | Infrastructure as Code |
| **Database** | Managed PostgreSQL | Cloud SQL |
| **Scaling** | Platform managed | Kubernetes HPA |
| **CI/CD** | DigitalOcean built-in | GitHub Actions |
| **Purpose** | Production app | Showcase + Production-ready |

---

## 📋 **Como Manter os Dois Projetos**

### **Projeto Original (DigitalOcean)**
```bash
cd /home/rafael/projetos/Moni-Personal

# Continuar desenvolvimento normalmente
git add .
git commit -m "Feature: nova funcionalidade"
git push origin main

# Deploy automático na DigitalOcean
```

### **Projeto GCP (Showcase)**
```bash
cd /home/rafael/projetos/Moni-Personal-GCP

# Sincronizar mudanças da aplicação (se necessário)
rsync -av --exclude='.git' --exclude='infrastructure' \
  ../Moni-Personal/app/ ./app/

# Commit e push
git add .
git commit -m "Sync: atualização da aplicação"
git push origin main
```

---

## 🔄 **Sincronizar Mudanças Entre Projetos**

### **Opção 1: Sincronização Manual (Recomendado)**

Quando fizer alterações importantes na **aplicação** (não na infraestrutura):

```bash
#!/bin/bash
# Script: sync-from-original.sh

cd /home/rafael/projetos/Moni-Personal-GCP

# Sincronizar código da aplicação
rsync -av --exclude='.git' \
          --exclude='infrastructure' \
          --exclude='.github' \
          --exclude='DEPLOYMENT-GCP.md' \
          --exclude='SHOWCASE-GUIDE.md' \
          ../Moni-Personal/ ./

echo "Sincronização completa!"
echo "Revise as mudanças e faça commit se necessário."
```

### **Opção 2: Cherry-pick Commits**

```bash
# No projeto GCP
cd /home/rafael/projetos/Moni-Personal-GCP

# Adicionar projeto original como remote
git remote add original ../Moni-Personal

# Fetch mudanças
git fetch original

# Cherry-pick commits específicos
git cherry-pick <commit-hash>
```

---

## 🎯 **Quando Usar Cada Projeto**

### **Use Moni-Personal (Original):**
- ✅ Desenvolvimento diário da aplicação
- ✅ Features novas para usuários finais
- ✅ Manutenção e bug fixes
- ✅ Produção real com usuários

### **Use Moni-Personal-GCP:**
- ✅ Demonstrações técnicas
- ✅ Aprendizado de GCP/Kubernetes/Terraform
- ✅ Entrevistas técnicas
- ✅ Portfolio profissional
- ✅ Testes de infraestrutura
- ✅ Experimentação com cloud-native patterns

---

## 📝 **Checklist de Sincronização**

Quando sincronizar mudanças:

```bash
# 1. Commit pendências no projeto original
cd /home/rafael/projetos/Moni-Personal
git status
git add .
git commit -m "Feature: descrição"
git push

# 2. Sincronizar para GCP
cd /home/rafael/projetos/Moni-Personal-GCP
./sync-from-original.sh  # ou rsync manual

# 3. Testar localmente
docker-compose up -d
# Verificar funcionamento

# 4. Commit no GCP
git add .
git commit -m "Sync: feature da aplicação original"
git push

# 5. Deploy no GCP (opcional)
cd infrastructure/terraform/environments/dev
terraform apply
kubectl rollout restart deployment/monipersonal-web -n monipersonal
```

---

## 🚨 **Importante**

### **❌ NÃO Faça:**
- Não commite secrets ou credenciais
- Não commite arquivos `.env`
- Não commite state do Terraform
- Não commite `terraform.tfvars` (apenas `.example`)

### **✅ Sempre Faça:**
- Revise mudanças antes de commit
- Teste localmente antes de deploy
- Mantenha documentação atualizada
- Use `.gitignore` apropriado

---

## 📚 **Referências**

- **Projeto Original**: `~/projetos/Moni-Personal`
- **Projeto GCP**: `~/projetos/Moni-Personal-GCP`
- **Documentação GCP**: `DEPLOYMENT-GCP.md`
- **Guia Showcase**: `SHOWCASE-GUIDE.md`

---

## 🤝 **Contribuindo**

### **Para o Projeto Original**
Siga workflow normal da DigitalOcean

### **Para o Projeto GCP**
1. Fork o repositório
2. Crie branch feature
3. Faça mudanças
4. Teste localmente
5. Pull request

---

**Criado em**: 2025-01-21
**Última atualização**: 2025-01-21
**Versão**: 1.0
