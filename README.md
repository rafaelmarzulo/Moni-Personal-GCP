# 🏋️ Moni Personal - Google Cloud Platform Edition

[![GCP](https://img.shields.io/badge/GCP-4285F4?logo=google-cloud&logoColor=white)](https://cloud.google.com)
[![Cloud Run](https://img.shields.io/badge/Cloud_Run-4285F4?logo=google-cloud&logoColor=white)](https://cloud.google.com/run)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)](https://python.org)

> **Sistema de Gestão de Reavaliações Físicas rodando em Google Cloud Platform**

Aplicação web moderna para personal trainers gerenciarem avaliações físicas de alunos, com deploy otimizado para Google Cloud Platform usando Cloud Run, Cloud SQL e Secret Manager.

---

## 🎯 Sobre Este Projeto

Sistema completo de gestão de reavaliações físicas com foco em:

- ✅ **Cloud Native**: Otimizado para Google Cloud Platform
- ✅ **Serverless**: Deploy em Cloud Run com auto-scaling
- ✅ **Segurança**: Secrets gerenciados, HTTPS forçado, autenticação robusta
- ✅ **Performance**: Cache estratégico, conexão pooling, otimizações
- ✅ **Observabilidade**: Logging estruturado, monitoramento integrado
- ✅ **DevOps**: Scripts de deploy automatizado, rollback fácil

**🎓 Ideal para:** Portfólio Cloud/Backend, demonstração de boas práticas, casos de uso real.

---

## ✨ Funcionalidades

### Para Personal Trainers
- 📝 **Reavaliações Completas**: Formulário com peso, medidas, dobras cutâneas
- 📊 **Histórico Detalhado**: Visualize a evolução de cada aluno
- 📈 **Comparação Visual**: Gráficos de progresso entre avaliações
- 🖨️ **Relatórios PDF**: Geração automática de relatórios profissionais
- 👥 **Gestão de Alunos**: Cadastro e organização de clientes

### Técnicas
- 🔐 **Autenticação Segura**: Sistema de login com sessões seguras
- 📱 **Responsivo**: Interface adaptável para mobile/tablet/desktop
- ⚡ **Performance**: Otimizado para carregamento rápido
- 🌐 **PWA Ready**: Pode ser instalado como app

---

## 🚀 Quick Start

### Opção 1: Deploy no Cloud Run (Recomendado)

**Mais rápido, mais barato, serverless!**

```bash
# 1. Clone e entre no diretório
git clone https://github.com/seu-usuario/Moni-Personal-GCP.git
cd Moni-Personal-GCP

# 2. Configure o projeto GCP
gcloud config set project SEU_PROJECT_ID

# 3. Configure secrets e Cloud SQL
./scripts/gcp/setup-secrets.sh
./scripts/gcp/setup-cloudsql.sh

# 4. Deploy automatizado
./scripts/gcp/deploy-cloud-run.sh
```

**Pronto! 🎉** Sua aplicação estará rodando em Cloud Run.

### Opção 2: Deploy no App Engine

**Para aplicações com tráfego mais constante:**

```bash
# 1. Configure variáveis no app.yaml
# 2. Deploy direto
gcloud app deploy app.yaml
```

### Opção 3: Desenvolvimento Local

```bash
# 1. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar variáveis
cp .env.example .env
# Edite .env com suas configurações

# 4. Rodar aplicação
uvicorn main:app --reload --port 8080
```

Acesse: http://localhost:8080

**📖 Guias de Deploy:**
- [DEPLOY-GUIDE.md](DEPLOY-GUIDE.md) - Guia rápido e prático
- [DEPLOYMENT-GCP.md](DEPLOYMENT-GCP.md) - Documentação completa (GKE/Terraform)

---

## 📁 Estrutura do Projeto

```
Moni-Personal-GCP/
├── 📱 app/                       # Código modular da aplicação
│   ├── core/                     # Configurações centrais
│   ├── middleware/               # Autenticação, rate limiting
│   ├── routes/                   # Rotas da API
│   ├── services/                 # Lógica de negócio
│   └── utils/                    # Utilitários e helpers
│
├── 🎨 templates/                 # Templates HTML (Jinja2)
│   ├── index.html                # Landing page
│   ├── login.html                # Página de login
│   ├── reavaliacao.html          # Formulário de avaliação
│   ├── historico.html            # Histórico do aluno
│   └── ...                       # Outras páginas
│
├── 🖼️ static/                    # Assets estáticos
│   ├── css/                      # Estilos customizados
│   ├── img/                      # Imagens e ícones
│   └── favicon.png               # Favicon
│
├── 🗄️ Banco de Dados
│   ├── database.py               # Configuração do SQLAlchemy
│   ├── models.py                 # Modelos ORM
│   └── alembic/                  # Migrations de banco
│
├── 🐳 Docker & GCP
│   ├── Dockerfile                # Otimizado para Cloud Run
│   ├── .dockerignore             # Arquivos ignorados no build
│   ├── app.yaml                  # Configuração App Engine
│   └── .gcloudignore             # Arquivos ignorados no deploy
│
├── 🔧 Scripts de Automação
│   └── scripts/gcp/              # Scripts para GCP
│       ├── deploy-cloud-run.sh   # Deploy automatizado
│       ├── setup-secrets.sh      # Configurar Secret Manager
│       ├── setup-cloudsql.sh     # Criar Cloud SQL instance
│       └── rollback.sh           # Rollback de versão
│
├── 📋 Configurações
│   ├── main.py                   # Aplicação FastAPI principal
│   ├── config.py                 # Configurações da app
│   ├── requirements.txt          # Dependências Python (GCP)
│   ├── .env.example              # Template de variáveis
│   └── compose.yml               # Docker Compose (dev local)
│
└── 📖 Documentação
    ├── README.md                 # Este arquivo
    ├── DEPLOY-GUIDE.md           # Guia rápido de deploy
    └── DEPLOYMENT-GCP.md         # Documentação completa (GKE)
```

---

## 🛠️ Stack Técnico

### Backend
- **Framework**: FastAPI 0.104+ (Python 3.11)
- **ORM**: SQLAlchemy 2.0 com suporte async
- **Autenticação**: Passlib + python-jose (JWT)
- **Templates**: Jinja2
- **Server**: Uvicorn + Gunicorn

### Frontend
- **UI Framework**: Bootstrap 5
- **Templates**: Jinja2 (server-side rendering)
- **Icons**: Font Awesome
- **Charts**: Chart.js (para gráficos de progresso)

### Database
- **Cloud SQL PostgreSQL 15** (produção)
- **SQLAlchemy ORM** com connection pooling
- **Alembic** para migrations

### GCP Services
| Serviço | Uso | Custo Estimado |
|---------|-----|----------------|
| **Cloud Run** | Hospedagem serverless | ~$10-15/mês |
| **Cloud SQL** | Database PostgreSQL | ~$15-25/mês |
| **Secret Manager** | Gerenciamento de secrets | ~$1/mês |
| **Cloud Logging** | Logs centralizados | Free tier |
| **Cloud Monitoring** | Métricas e alertas | Free tier |
| **Cloud Build** | CI/CD pipelines | Free tier |

**Custo total estimado: ~$25-40/mês** (tráfego médio)

### DevOps
- **Container**: Docker multi-stage builds
- **Deploy**: Cloud Run (serverless)
- **Secrets**: Google Secret Manager
- **Logging**: Cloud Logging (estruturado)
- **Monitoring**: Cloud Monitoring + OpenTelemetry

---

## 🏗️ Arquitetura Cloud Run

```
┌─────────────────────────────────────────────────────────────┐
│                  GOOGLE CLOUD PLATFORM                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Internet / CDN                           │  │
│  └────────────────────────┬─────────────────────────────┘  │
│                            │ HTTPS                           │
│  ┌─────────────────────────▼──────────────────────────────┐ │
│  │         Cloud Run Service                              │ │
│  │  (Auto-scale: 0-10 instances)                          │ │
│  │                                                         │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │ │
│  │  │ FastAPI  │  │ FastAPI  │  │ FastAPI  │            │ │
│  │  │ Container│  │ Container│  │ Container│            │ │
│  │  │  512Mi   │  │  512Mi   │  │  512Mi   │            │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘            │ │
│  └───────┼─────────────┼─────────────┼──────────────────┘ │
│          │             │             │                      │
│          └─────────────┴─────────────┘                      │
│                        │                                     │
│  ┌─────────────────────▼──────────────────────────────────┐ │
│  │         Cloud SQL PostgreSQL                           │ │
│  │  (Private IP + Unix Socket Connection)                 │ │
│  │  - Auto backups (03:00 daily)                          │ │
│  │  - Point-in-time recovery                              │ │
│  │  - Connection pooling (max 10)                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Secret Manager                                  │ │
│  │  - DATABASE_URL                                         │ │
│  │  - SECRET_KEY                                           │ │
│  │  - JWT_SECRET_KEY                                       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Observability                                   │ │
│  │  - Cloud Logging (structured logs)                     │ │
│  │  - Cloud Monitoring (metrics + dashboards)             │ │
│  │  - Error Reporting (alerts)                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Principais Recursos:**
- ✅ **Serverless**: Scale to zero quando não está em uso
- ✅ **Auto-scaling**: 0-10 instâncias baseado em tráfego
- ✅ **HTTPS Automático**: Certificado SSL gerenciado pelo GCP
- ✅ **Private Connection**: Cloud SQL via Unix Socket
- ✅ **Secrets Management**: Integração com Secret Manager
- ✅ **Observability**: Logs e métricas nativos do GCP

---

## 💻 Comandos Úteis

### Desenvolvimento Local
```bash
# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Rodar aplicação
uvicorn main:app --reload --port 8080

# Testes (quando implementados)
pytest

# Formatar código
black .
isort .
```

### GCP - Cloud Run
```bash
# Deploy
./scripts/gcp/deploy-cloud-run.sh

# Ver logs em tempo real
gcloud run services logs tail moni-personal --region=southamerica-east1

# Rollback para versão anterior
./scripts/gcp/rollback.sh

# Abrir no browser
gcloud run services browse moni-personal --region=southamerica-east1

# Listar revisões
gcloud run revisions list --service=moni-personal --region=southamerica-east1
```

### GCP - Cloud SQL
```bash
# Conectar ao banco via proxy
cloud_sql_proxy -instances=PROJECT:REGION:INSTANCE=tcp:5432

# Rodar migrations
alembic upgrade head

# Criar nova migration
alembic revision --autogenerate -m "descrição"

# Backup manual
gcloud sql backups create --instance=INSTANCE_NAME
```

### Docker Local
```bash
# Build da imagem
docker build -t moni-personal-gcp .

# Rodar container
docker run -p 8080:8080 \
  -e PORT=8080 \
  -e DATABASE_URL="sua-url" \
  moni-personal-gcp

# Verificar logs
docker logs -f CONTAINER_ID
```

---

## 🔒 Segurança

### Implementado
- ✅ **HTTPS Forçado**: Todas conexões via SSL/TLS
- ✅ **Secret Manager**: Credenciais nunca em código
- ✅ **Non-root Container**: Usuário não-privilegiado
- ✅ **Rate Limiting**: Proteção contra abuso
- ✅ **Session Security**: Cookies httponly + secure + samesite
- ✅ **SQL Injection Protection**: Prepared statements via ORM
- ✅ **Password Hashing**: Bcrypt para senhas
- ✅ **CORS Policy**: Configuração restritiva

### Boas Práticas
- 🔐 Secrets gerenciados via Secret Manager
- 🛡️ Validação de entrada com Pydantic
- 📝 Logging estruturado (não loga dados sensíveis)
- 🔄 Rotação de secrets recomendada a cada 90 dias
- 📊 Auditoria de acessos via Cloud Logging

---

## 📊 Performance & Otimizações

### Database
- Connection pooling (10 conexões max)
- Pool recycle a cada 1 hora
- Índices otimizados nas queries principais
- Timezone-aware timestamps (America/Sao_Paulo)

### Application
- Lazy loading de módulos pesados
- Cache de templates Jinja2
- Compressão de responses
- Health checks otimizados

### Cloud Run
- Startup time < 2 segundos
- Request timeout: 300 segundos
- Memory: 512Mi (otimizado)
- CPU: 1 vCPU (auto-scaling)

---

## 🎓 Para Estudantes e Portfólio

Este projeto demonstra:

### Backend Skills
- ✅ Python moderno (3.11+, type hints)
- ✅ FastAPI (async, dependency injection)
- ✅ SQLAlchemy 2.0 (ORM moderno)
- ✅ Autenticação e autorização
- ✅ Estrutura modular e escalável

### Cloud & DevOps
- ✅ Google Cloud Platform (Cloud Run, Cloud SQL)
- ✅ Containerização (Docker multi-stage)
- ✅ Infrastructure as Code (configurável)
- ✅ Secrets management
- ✅ Monitoring e logging

### Boas Práticas
- ✅ Código limpo e documentado
- ✅ Separação de responsabilidades
- ✅ Segurança by design
- ✅ Observabilidade
- ✅ Scripts de automação

---

## 📚 Documentação

| Documento | Descrição |
|-----------|-----------|
| **[README.md](README.md)** | Você está aqui! |
| **[DEPLOY-GUIDE.md](DEPLOY-GUIDE.md)** | Guia rápido e prático de deploy |
| **[DEPLOYMENT-GCP.md](DEPLOYMENT-GCP.md)** | Documentação completa (GKE/Terraform) |
| **.env.example** | Template de variáveis de ambiente |

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para mudanças grandes:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📝 License

Este projeto é open source para fins educacionais e de portfólio.
- [ ] FinOps dashboard
- [ ] Mobile app integration

---

## 🤝 **Contribuindo**

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add: AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📄 **Licença**

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👤 **Autor**

**Rafael Marzulo**

- 🔗 LinkedIn: [rafael-marzulo](https://linkedin.com/in/rafael-marzulo-58b04b31/)
- 💻 GitHub: [@rafaelmarzulo](https://github.com/rafaelmarzulo)
- 📧 Email: contato@exemplo.com

---

## 🙏 **Agradecimentos**

- FastAPI pela excelente framework
- Google Cloud Platform pela infraestrutura robusta
- Comunidade Kubernetes pelos recursos educacionais
- HashiCorp pelo Terraform
- Todos os contribuidores open-source

---

## 📞 **Suporte**

Para dúvidas e issues:

- 📖 **Documentação**: Consulte os arquivos markdown neste repositório
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/seu-usuario/Moni-Personal-GCP/issues)
- 💬 **Discussões**: [GitHub Discussions](https://github.com/seu-usuario/Moni-Personal-GCP/discussions)

---

## 🎯 **Skills Demonstradas**

<div align="center">

### **Backend & Database**
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white)

### **Cloud & Infrastructure**
![GCP](https://img.shields.io/badge/GCP-4285F4?logo=google-cloud&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?logo=terraform&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?logo=kubernetes&logoColor=white)

### **DevOps & CI/CD**
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=github-actions&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?logo=nginx&logoColor=white)

</div>

---

<div align="center">

**⭐ Se este projeto foi útil, considere dar uma estrela!**

[![GitHub Stars](https://img.shields.io/github/stars/seu-usuario/Moni-Personal-GCP?style=social)](https://github.com/seu-usuario/Moni-Personal-GCP)

---

**💪 MoniPersonal GCP** - Enterprise-grade Cloud Native Application

**Status**: ✅ Production-ready | 🚀 Showcase project | 🔄 CI/CD Active | 🔐 SA Fixed

Made with ❤️ by [Rafael Marzulo](https://linkedin.com/in/rafael-marzulo-58b04b31/)

</div>
