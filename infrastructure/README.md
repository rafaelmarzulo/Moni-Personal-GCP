# 🚀 MoniPersonal - Infrastructure as Code (GCP + GKE)

[![Terraform](https://img.shields.io/badge/Terraform-1.6+-623CE4?logo=terraform)](https://terraform.io)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.28+-326CE5?logo=kubernetes)](https://kubernetes.io)
[![GCP](https://img.shields.io/badge/GCP-Cloud-4285F4?logo=google-cloud)](https://cloud.google.com)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=github-actions)](https://github.com/features/actions)

Enterprise-grade infrastructure for MoniPersonal running on **Google Kubernetes Engine (GKE)** with complete automation using **Terraform**, **Kubernetes**, and **GitHub Actions**.

---

## 📊 **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE CLOUD PLATFORM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            GKE Cluster (Zonal/Regional)                   │  │
│  │                                                            │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │  │
│  │  │  FastAPI   │  │  FastAPI   │  │  FastAPI   │         │  │
│  │  │   Pod 1    │  │   Pod 2    │  │   Pod 3    │         │  │
│  │  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘         │  │
│  │         └────────────────┴────────────────┘               │  │
│  │                          │                                 │  │
│  │                 ┌────────▼────────┐                       │  │
│  │                 │ Nginx Ingress   │                       │  │
│  │                 │   Controller    │                       │  │
│  │                 └────────┬────────┘                       │  │
│  └──────────────────────────┼────────────────────────────────┘  │
│                              │                                   │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │         Cloud Load Balancer + Cloud Armor               │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │      Cloud SQL (PostgreSQL) - Private IP + Backups      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │    Secret Manager (Database Credentials & Secrets)      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │     Cloud Monitoring + Logging + Trace                  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ **Features**

### Infrastructure (Terraform)
- ✅ **VPC Networking** with private subnets and Cloud NAT
- ✅ **GKE Cluster** with auto-scaling, private nodes, and Workload Identity
- ✅ **Cloud SQL** PostgreSQL with high availability and automated backups
- ✅ **Secret Manager** for secure credentials management
- ✅ **Firewall Rules** with defense-in-depth security
- ✅ **Modular Architecture** for reusability across environments

### Kubernetes
- ✅ **Declarative Manifests** with Kustomize for multi-environment
- ✅ **Horizontal Pod Autoscaler** for automatic scaling
- ✅ **Resource Limits** and requests properly configured
- ✅ **Health Checks** (liveness, readiness, startup probes)
- ✅ **Security Context** with non-root user and read-only filesystem
- ✅ **Ingress** with TLS termination and rate limiting

### CI/CD (GitHub Actions)
- ✅ **Terraform Validation** with tfsec and Checkov security scanning
- ✅ **Docker Build** with multi-stage builds and layer caching
- ✅ **Vulnerability Scanning** with Trivy
- ✅ **Automated Deployment** to GKE with rollback support
- ✅ **Smoke Tests** post-deployment

---

## 🛠️ **Tech Stack**

| Layer | Technology |
|-------|-----------|
| **Cloud** | Google Cloud Platform (GCP) |
| **IaC** | Terraform 1.6+ |
| **Orchestration** | Google Kubernetes Engine (GKE 1.28+) |
| **Package Mgmt** | Kustomize |
| **CI/CD** | GitHub Actions |
| **Database** | Cloud SQL PostgreSQL 15 |
| **Secrets** | Secret Manager |
| **Monitoring** | Cloud Monitoring + Prometheus |
| **Security** | tfsec, Checkov, Trivy, OPA Gatekeeper |

---

## 📁 **Project Structure**

```
infrastructure/
├── terraform/
│   ├── environments/
│   │   ├── dev/                  # Development environment
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── terraform.tfvars.example
│   │   ├── staging/              # Staging environment
│   │   └── prod/                 # Production environment
│   └── modules/
│       ├── vpc-networking/       # VPC, Subnets, Firewall, NAT
│       ├── gke-cluster/          # GKE cluster with node pools
│       ├── cloud-sql/            # PostgreSQL database
│       ├── workload-identity/    # Workload Identity config
│       └── monitoring/           # Cloud Monitoring setup
├── kubernetes/
│   ├── base/                     # Base Kubernetes manifests
│   │   ├── namespace.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── ingress.yaml
│   │   ├── configmap.yaml
│   │   ├── hpa.yaml
│   │   └── kustomization.yaml
│   └── overlays/
│       ├── dev/                  # Dev-specific customizations
│       ├── staging/
│       └── prod/
├── scripts/
│   ├── setup-gcp.sh              # Initial GCP setup
│   ├── deploy.sh                 # Manual deployment script
│   └── destroy.sh                # Cleanup script
└── docs/
    ├── architecture.md
    ├── deployment.md
    ├── troubleshooting.md
    └── cost-optimization.md
```

---

## 🚀 **Quick Start**

### **Prerequisites**

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- [Terraform](https://terraform.io/downloads) >= 1.6.0
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [kustomize](https://kubectl.docs.kubernetes.io/installation/kustomize/)
- [Docker](https://docs.docker.com/get-docker/)
- GCP Account with billing enabled

### **Step 1: Setup GCP Project**

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export ZONE="us-central1-a"

# Authenticate
gcloud auth login
gcloud auth application-default login

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  compute.googleapis.com \
  container.googleapis.com \
  servicenetworking.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com

# Create GCS bucket for Terraform state
gsutil mb -p $PROJECT_ID -l $REGION gs://${PROJECT_ID}-terraform-state

# Enable versioning on state bucket
gsutil versioning set on gs://${PROJECT_ID}-terraform-state
```

### **Step 2: Configure Terraform Variables**

```bash
cd infrastructure/terraform/environments/dev

# Create terraform.tfvars from example
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars
```

**terraform.tfvars:**
```hcl
project_id   = "your-gcp-project-id"
project_name = "monipersonal"
environment  = "dev"
region       = "us-central1"
zone         = "us-central1-a"
```

### **Step 3: Deploy Infrastructure**

```bash
# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply infrastructure
terraform apply

# Save outputs
terraform output -json > ../../outputs/dev-outputs.json
```

⏱️ **Deployment time:** ~15-20 minutes

### **Step 4: Configure kubectl**

```bash
# Get cluster credentials
gcloud container clusters get-credentials \
  monipersonal-dev \
  --zone us-central1-a \
  --project $PROJECT_ID

# Verify connection
kubectl get nodes
kubectl get namespaces
```

### **Step 5: Deploy Application**

```bash
cd ../../kubernetes

# Deploy to dev environment
kubectl apply -k overlays/dev/

# Watch deployment
kubectl rollout status deployment/monipersonal-web -n monipersonal

# Get pods
kubectl get pods -n monipersonal

# Get services
kubectl get svc -n monipersonal
```

### **Step 6: Access Application**

```bash
# Get LoadBalancer IP
kubectl get ingress -n monipersonal

# Or port-forward for testing
kubectl port-forward -n monipersonal \
  svc/monipersonal-web 8000:80

# Access: http://localhost:8000
```

---

## 🔐 **Security**

### **Implemented Security Measures**

- ✅ **Private GKE Nodes** - No public IPs on worker nodes
- ✅ **Workload Identity** - Secure authentication between GKE and GCP services
- ✅ **Network Policies** - Micro-segmentation within cluster
- ✅ **Pod Security Standards** - Restricted pod security policies
- ✅ **Secret Manager** - Encrypted secrets storage
- ✅ **Cloud Armor** - DDoS protection
- ✅ **Binary Authorization** - Image verification before deployment
- ✅ **Shielded Nodes** - Secure boot and integrity monitoring
- ✅ **RBAC** - Role-based access control
- ✅ **Audit Logging** - Complete audit trail

### **Security Scanning**

```bash
# Terraform security scan
cd infrastructure/terraform
tfsec .
checkov -d .

# Container vulnerability scan
trivy image gcr.io/$PROJECT_ID/monipersonal:latest

# Kubernetes manifest scan
kubesec scan kubernetes/base/deployment.yaml
```

---

## 📊 **Monitoring & Observability**

### **Cloud Monitoring**

- **Metrics**: CPU, Memory, Disk, Network
- **Logs**: Application logs, Audit logs, System logs
- **Traces**: Distributed tracing with Cloud Trace
- **Alerts**: Configured for critical thresholds

### **Access Monitoring**

```bash
# View logs
gcloud logging read "resource.type=k8s_cluster" --limit 50

# View metrics in Cloud Console
open "https://console.cloud.google.com/monitoring?project=$PROJECT_ID"

# Kubectl logs
kubectl logs -n monipersonal -l app=monipersonal --tail=100 -f
```

---

## 💰 **Cost Optimization**

### **Development Environment**

| Resource | Configuration | Monthly Cost (Estimate) |
|----------|--------------|-------------------------|
| GKE Cluster | Zonal, 1 node e2-medium, preemptible | ~$15-20 |
| Cloud SQL | db-f1-micro, 10GB | ~$7-10 |
| Load Balancer | Single forwarding rule | ~$18 |
| **Total** | | **~$40-50/month** |

### **Cost-Saving Tips**

1. **Use Preemptible Nodes** for dev/staging (−60-80% cost)
2. **Auto-scaling** - Scale down to 0 replicas after hours
3. **Committed Use Discounts** for production
4. **Budget Alerts** - Set budget alerts in GCP
5. **Clean up** unused resources regularly

### **Setup Budget Alerts**

```bash
# Create budget alert
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="MoniPersonal Dev Budget" \
  --budget-amount=50USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

---

## 🔄 **CI/CD Pipeline**

### **Automated Workflows**

1. **Pull Request** → Terraform validation + Security scan
2. **Push to main** → Build Docker image → Push to GCR
3. **Image built** → Deploy to GKE → Smoke tests → Notify

### **Manual Deployment**

```bash
# Trigger deployment
gh workflow run deploy-gke.yml -f environment=dev

# Check status
gh run list --workflow=deploy-gke.yml
```

---

## 🧹 **Cleanup**

### **Destroy Infrastructure**

```bash
cd infrastructure/terraform/environments/dev

# Destroy all resources
terraform destroy

# Or use script
../../scripts/destroy.sh dev
```

⚠️ **Warning:** This will delete ALL resources including databases and data!

---

## 📚 **Additional Documentation**

- [Architecture Details](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Cost Optimization](docs/cost-optimization.md)
- [Security Best Practices](docs/security.md)

---

## 🎯 **Roadmap**

- [ ] **Helm Chart** implementation
- [ ] **ArgoCD** for GitOps
- [ ] **Istio** service mesh integration
- [ ] **Multi-region** deployment
- [ ] **Disaster Recovery** automation
- [ ] **Cost Optimization** with FinOps practices

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 **License**

This project is licensed under the MIT License.

---

## 📞 **Support**

For issues and questions:
- GitHub Issues: [Report Bug](https://github.com/your-username/Moni-Personal/issues)
- Email: your-email@example.com

---

**Built with ❤️ using Terraform + Kubernetes + GCP**
