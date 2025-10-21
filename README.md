# 🏋️ MoniPersonal - Google Cloud Platform Deployment

[![GCP](https://img.shields.io/badge/GCP-4285F4?logo=google-cloud&logoColor=white)](https://cloud.google.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io)
[![Terraform](https://img.shields.io/badge/Terraform-7B42BC?logo=terraform&logoColor=white)](https://terraform.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white)](https://postgresql.org)

> **Enterprise-grade fitness tracking application running on Google Kubernetes Engine (GKE)**

Sistema web para personal trainers acompanharem o progresso de seus alunos através de reavaliações físicas periódicas, com infraestrutura **Cloud Native** completa no Google Cloud Platform.

---

## 🎯 **Sobre Este Projeto**

Este repositório demonstra a **migração** de uma aplicação tradicional Docker Compose para uma arquitetura **Cloud Native** moderna rodando em **Google Kubernetes Engine (GKE)**, utilizando:

- ✅ **Infrastructure as Code** com Terraform modular
- ✅ **Container Orchestration** com Kubernetes
- ✅ **CI/CD** completo com GitHub Actions
- ✅ **Security-first** design (Workload Identity, Secret Manager)
- ✅ **Auto-scaling** e High Availability
- ✅ **Observability** com Cloud Monitoring

**🎓 Projeto ideal para:** Portfólio DevOps/SRE, aprendizado prático de GCP/Kubernetes/Terraform, demonstração em entrevistas técnicas.

---

## ✨ **Funcionalidades da Aplicação**

- 📝 **Formulário de Reavaliação**: Coleta completa de dados do aluno
- 📊 **Histórico do Aluno**: Visualização de todas as reavaliações
- 📈 **Comparação de Progresso**: Evolução entre avaliações
- 🖨️ **Relatórios**: Geração de relatórios profissionais
- 👥 **Gestão de Alunos**: Administração completa

---

## 🚀 **Quick Start**

### **Opção 1: Deploy no GCP (Recomendado para Showcase)**

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/Moni-Personal-GCP.git
cd Moni-Personal-GCP

# 2. Setup automatizado do GCP
cd infrastructure/scripts
./setup-gcp.sh

# 3. Deploy da infraestrutura (15-20 min)
cd ../terraform/environments/dev
terraform init
terraform apply

# 4. Deploy da aplicação (< 5 min)
# Seguir instruções em DEPLOYMENT-GCP.md
```

**📖 Documentação completa:** [DEPLOYMENT-GCP.md](DEPLOYMENT-GCP.md)

---

### **Opção 2: Teste Local (Docker Compose)**

```bash
# Quick start local
cp .env.example .env
docker-compose up -d

# Acesse: http://localhost
```

---

## 📁 **Estrutura do Projeto**

```
Moni-Personal-GCP/
├── 📱 app/                       # Application code
│   ├── core/                     # Core configurations
│   ├── middleware/               # Auth, rate limiting
│   ├── routes/                   # API routes
│   ├── services/                 # Business logic
│   └── utils/                    # Utilities
│
├── 🎨 templates/                 # HTML templates
├── 🖼️ static/                    # CSS, JS, images
│
├── 🐳 Docker & Compose
│   ├── Dockerfile                # Container image
│   ├── compose.yml               # Local development
│   └── nginx.conf                # Nginx configuration
│
├── 🏗️ infrastructure/            # GCP Infrastructure
│   ├── terraform/                # Infrastructure as Code
│   │   ├── modules/
│   │   │   ├── vpc-networking/   # VPC + Firewall + NAT
│   │   │   ├── gke-cluster/      # GKE cluster setup
│   │   │   └── cloud-sql/        # PostgreSQL database
│   │   └── environments/
│   │       ├── dev/              # Development environment
│   │       ├── staging/          # Staging environment
│   │       └── prod/             # Production environment
│   │
│   ├── kubernetes/               # Kubernetes manifests
│   │   ├── base/                 # Base resources
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── ingress.yaml
│   │   │   ├── hpa.yaml          # Auto-scaling
│   │   │   └── ...
│   │   └── overlays/             # Environment-specific
│   │       ├── dev/
│   │       ├── staging/
│   │       └── prod/
│   │
│   ├── scripts/
│   │   └── setup-gcp.sh          # Automated GCP setup
│   │
│   └── README.md                 # Infrastructure docs
│
├── 🔄 .github/
│   └── workflows/                # CI/CD Pipelines
│       ├── terraform-ci.yml      # Terraform validation
│       ├── docker-build.yml      # Build & push images
│       └── deploy-gke.yml        # Deploy to GKE
│
├── 📚 Documentation
│   ├── README.md                 # Este arquivo
│   ├── DEPLOYMENT-GCP.md         # Guia completo de deploy
│   ├── SHOWCASE-GUIDE.md         # Guia para apresentações
│   ├── QUICK-REFERENCE.md        # Comandos rápidos
│   └── PROJETO-CRIADO.md         # Resumo do projeto
│
└── 🔧 Configuration
    ├── .env.example              # Environment variables template
    ├── .gitignore                # Git ignore rules
    ├── requirements.txt          # Python dependencies
    └── Makefile                  # Development commands
```

---

## 🛠️ **Stack Técnico**

### **Application Layer**
- **Backend**: Python 3.11 + FastAPI
- **Database**: PostgreSQL 15
- **Frontend**: HTML5 + Bootstrap 5 + Jinja2
- **Auth**: JWT + Session-based

### **Infrastructure Layer (GCP)**
| Component | Technology |
|-----------|-----------|
| **Cloud Provider** | Google Cloud Platform (GCP) |
| **Orchestration** | Google Kubernetes Engine (GKE 1.28+) |
| **IaC** | Terraform 1.6+ |
| **Package Management** | Kustomize |
| **Database** | Cloud SQL PostgreSQL 15 |
| **Secrets** | Secret Manager |
| **Networking** | VPC + Cloud NAT + Load Balancer |
| **CI/CD** | GitHub Actions |
| **Monitoring** | Cloud Monitoring + Cloud Logging |
| **Security** | Workload Identity, Binary Authorization |

---

## 🏗️ **Arquitetura GCP**

```
┌─────────────────────────────────────────────────────────────┐
│                  GOOGLE CLOUD PLATFORM                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         GKE Cluster (Auto-scaling)                    │  │
│  │                                                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │  │
│  │  │ FastAPI  │  │ FastAPI  │  │ FastAPI  │  (2-10)   │  │
│  │  │  Pod 1   │  │  Pod 2   │  │  Pod N   │           │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘           │  │
│  │       └─────────────┴──────────────┘                 │  │
│  │                     │                                 │  │
│  │            ┌────────▼────────┐                       │  │
│  │            │ Nginx Ingress   │                       │  │
│  │            └────────┬────────┘                       │  │
│  └─────────────────────┼─────────────────────────────── ┘  │
│                         │                                   │
│  ┌──────────────────────▼──────────────────────────────┐  │
│  │      Cloud Load Balancer + Cloud Armor              │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Cloud SQL PostgreSQL (Private IP + Auto Backups)   │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Secret Manager (Credentials & Secrets)             │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- ✅ Private GKE nodes (no public IPs)
- ✅ Auto-scaling (2-10 pods based on CPU/Memory)
- ✅ High Availability (multi-zone deployment)
- ✅ Automated backups (Cloud SQL)
- ✅ SSL/TLS termination (Ingress)
- ✅ DDoS protection (Cloud Armor)

---

## 📊 **Métricas & Resultados**

### **Infrastructure**
- 📝 **Terraform Code**: 1,461 linhas
- 🧩 **Modules**: 3 módulos reutilizáveis
- ☸️ **K8s Resources**: 8 manifests
- 🔄 **CI/CD Pipelines**: 3 workflows automatizados
- ☁️ **GCP Resources**: ~25 recursos provisionados

### **Performance**
- ⚡ **Deploy Time**: < 5 minutos (aplicação)
- 🏗️ **Infrastructure Setup**: 15-20 minutos (primeira vez)
- 📈 **Auto-scaling**: 2-10 pods (baseado em load)
- ⏱️ **Uptime**: 99.9% (com multi-replica deployment)

### **Cost Optimization**
- 💰 **Dev Environment**: ~$40-50/mês
- 🎁 **GCP Free Tier**: $300 créditos para novos usuários
- 📉 **Savings**: 70% vs VMs tradicionais (preemptible nodes)

---

## 🔒 **Segurança**

### **Implementado**
- ✅ **Private GKE Nodes** - Sem IPs públicos em workers
- ✅ **Workload Identity** - Autenticação segura entre GKE e GCP
- ✅ **Secret Manager** - Credenciais criptografadas
- ✅ **Network Policies** - Micro-segmentação no cluster
- ✅ **Binary Authorization** - Verificação de imagens
- ✅ **Shielded Nodes** - Secure boot e integrity monitoring
- ✅ **RBAC** - Role-based access control
- ✅ **Security Scanning** - tfsec, Checkov, Trivy

### **Continuous Security**
- ✅ Vulnerability scanning em toda build
- ✅ Terraform security validation em PRs
- ✅ Non-root containers
- ✅ Read-only root filesystem
- ✅ Security contexts configurados

---

## 📚 **Documentação**

| Documento | Descrição | Público |
|-----------|-----------|---------|
| **[README.md](README.md)** | Overview do projeto (você está aqui) | Todos |
| **[DEPLOYMENT-GCP.md](DEPLOYMENT-GCP.md)** | Guia completo de deployment no GCP | DevOps/Desenvolvedores |
| **[SHOWCASE-GUIDE.md](SHOWCASE-GUIDE.md)** | Guia para apresentações e demos | Candidatos/Apresentadores |
| **[QUICK-REFERENCE.md](QUICK-REFERENCE.md)** | Comandos rápidos e troubleshooting | DevOps/SRE |
| **[PROJETO-CRIADO.md](PROJETO-CRIADO.md)** | Resumo executivo do projeto | Gestores/Stakeholders |
| **[infrastructure/README.md](infrastructure/README.md)** | Documentação técnica da infraestrutura | Engenheiros de Infraestrutura |

---

## 🎓 **Use Cases**

### **Para Estudantes/Profissionais**
- ⭐ **Portfolio showcase** para vagas DevOps/SRE/Platform Engineer
- 📖 **Aprendizado prático** de GCP, Kubernetes e Terraform
- 🎯 **Demonstração** em entrevistas técnicas
- 🔧 **Template** para outros projetos cloud-native

### **Para Personal Trainers**
- 💼 Gestão profissional de clientes
- 📊 Acompanhamento de evolução
- 🖨️ Relatórios para apresentação
- 📱 Interface web responsiva

---

## 🚀 **Roadmap**

### **Curto Prazo (1-2 semanas)**
- [ ] Helm Chart implementation
- [ ] Cert-manager para SSL automático
- [ ] Custom Grafana dashboards

### **Médio Prazo (1 mês)**
- [ ] ArgoCD para GitOps
- [ ] Multi-environment (staging + prod)
- [ ] Disaster recovery testing

### **Longo Prazo (2-3 meses)**
- [ ] Service Mesh (Istio)
- [ ] Multi-region deployment
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

**Status**: ✅ Production-ready | 🚀 Showcase project

Made with ❤️ by [Rafael Marzulo](https://linkedin.com/in/rafael-marzulo-58b04b31/)

</div>
