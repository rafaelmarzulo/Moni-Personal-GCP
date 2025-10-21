# ⚡ MoniPersonal - Quick Reference Card

## 🚀 **Deploy Rápido (Copy & Paste)**

### **1. Setup Inicial**
```bash
cd /home/rafael/projetos/Moni-Personal/infrastructure/scripts
./setup-gcp.sh
# Seguir prompts interativos
```

### **2. Deploy Infraestrutura**
```bash
cd ../terraform/environments/dev

# Configurar variáveis (se não usou setup-gcp.sh)
export TF_VAR_project_id="seu-project-id"

# Deploy
terraform init
terraform plan
terraform apply -auto-approve

# Salvar outputs
terraform output > outputs.txt
```

### **3. Configurar kubectl**
```bash
PROJECT_ID=$(terraform output -raw project_id 2>/dev/null || echo "seu-project-id")
CLUSTER_NAME="monipersonal-dev"
ZONE="us-central1-a"

gcloud container clusters get-credentials $CLUSTER_NAME \
  --zone $ZONE \
  --project $PROJECT_ID

kubectl get nodes
```

### **4. Build & Push Imagem**
```bash
cd /home/rafael/projetos/Moni-Personal

PROJECT_ID="seu-project-id"  # ou do terraform output

# Authenticate Docker
gcloud auth configure-docker

# Build
docker build -t gcr.io/$PROJECT_ID/monipersonal:latest .

# Push
docker push gcr.io/$PROJECT_ID/monipersonal:latest
```

### **5. Deploy Aplicação**
```bash
cd infrastructure/kubernetes

# Atualizar PROJECT_ID no kustomization
sed -i "s/PROJECT_ID/$PROJECT_ID/g" overlays/dev/kustomization.yaml

# Deploy
kubectl apply -k overlays/dev/

# Acompanhar
kubectl rollout status deployment/monipersonal-web -n monipersonal
kubectl get pods -n monipersonal -w
```

---

## 🔍 **Comandos de Debug**

### **Verificar Status**
```bash
# Cluster
kubectl get nodes -o wide

# Aplicação
kubectl get all -n monipersonal
kubectl get hpa -n monipersonal
kubectl get ingress -n monipersonal

# Detalhes de um pod
kubectl describe pod <POD_NAME> -n monipersonal
```

### **Ver Logs**
```bash
# Logs em tempo real
kubectl logs -f -n monipersonal -l app=monipersonal

# Últimas 100 linhas
kubectl logs -n monipersonal -l app=monipersonal --tail=100

# Logs de um pod específico
kubectl logs <POD_NAME> -n monipersonal
```

### **Acessar Pod**
```bash
# Shell no pod
kubectl exec -it <POD_NAME> -n monipersonal -- /bin/bash

# Executar comando
kubectl exec <POD_NAME> -n monipersonal -- env
```

### **Verificar Recursos**
```bash
# CPU e Memory usage
kubectl top nodes
kubectl top pods -n monipersonal

# Eventos
kubectl get events -n monipersonal --sort-by='.lastTimestamp'
```

---

## 🔄 **Operações Comuns**

### **Scaling Manual**
```bash
# Escalar deployment
kubectl scale deployment monipersonal-web --replicas=5 -n monipersonal

# Ver escalando
watch kubectl get pods -n monipersonal
```

### **Rolling Update**
```bash
# Atualizar imagem
kubectl set image deployment/monipersonal-web \
  web=gcr.io/$PROJECT_ID/monipersonal:new-tag \
  -n monipersonal

# Acompanhar rollout
kubectl rollout status deployment/monipersonal-web -n monipersonal

# Histórico
kubectl rollout history deployment/monipersonal-web -n monipersonal

# Rollback
kubectl rollout undo deployment/monipersonal-web -n monipersonal
```

### **Port Forward (Teste Local)**
```bash
# Acessar aplicação localmente
kubectl port-forward -n monipersonal svc/monipersonal-web 8000:80

# Acessar: http://localhost:8000
```

### **Restart Pods**
```bash
kubectl rollout restart deployment/monipersonal-web -n monipersonal
```

---

## 🗑️ **Cleanup**

### **Destruir Infraestrutura**
```bash
cd /home/rafael/projetos/Moni-Personal/infrastructure/terraform/environments/dev

# WARNING: Isso vai deletar TUDO!
terraform destroy -auto-approve

# Ou seletivo
terraform destroy -target=module.gke_cluster
```

### **Deletar Aplicação**
```bash
cd /home/rafael/projetos/Moni-Personal/infrastructure/kubernetes

kubectl delete -k overlays/dev/

# Ou force delete namespace
kubectl delete namespace monipersonal --grace-period=0 --force
```

---

## 📊 **GCP Console URLs**

### **Quick Links**
```bash
PROJECT_ID="seu-project-id"

# GKE
echo "https://console.cloud.google.com/kubernetes/clusters/details/us-central1-a/monipersonal-dev?project=$PROJECT_ID"

# Cloud SQL
echo "https://console.cloud.google.com/sql/instances?project=$PROJECT_ID"

# Monitoring
echo "https://console.cloud.google.com/monitoring?project=$PROJECT_ID"

# Billing
echo "https://console.cloud.google.com/billing?project=$PROJECT_ID"

# IAM
echo "https://console.cloud.google.com/iam-admin?project=$PROJECT_ID"
```

---

## 🔐 **Secrets Management**

### **Criar Secret Manualmente**
```bash
# Database password
kubectl create secret generic cloudsql-credentials \
  --from-literal=connection-string="postgresql://user:pass@host:5432/db" \
  -n monipersonal

# Ver secrets
kubectl get secrets -n monipersonal
kubectl describe secret cloudsql-credentials -n monipersonal
```

### **Acessar Secret Manager**
```bash
# List secrets
gcloud secrets list --project=$PROJECT_ID

# Ver secret value
gcloud secrets versions access latest \
  --secret="monipersonal-dev-password" \
  --project=$PROJECT_ID
```

---

## 🧪 **Testing**

### **Smoke Test**
```bash
# Get LoadBalancer IP
LB_IP=$(kubectl get svc monipersonal-web -n monipersonal -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Health check
curl http://$LB_IP/health

# Full test
curl -v http://$LB_IP/
```

### **Load Test**
```bash
# Install k6
brew install k6  # ou baixar de k6.io

# Simple load test
k6 run --vus 10 --duration 30s - <<EOF
import http from 'k6/http';
import { sleep } from 'k6';

export default function () {
  http.get('http://$LB_IP/');
  sleep(1);
}
EOF

# Watch HPA scaling
watch kubectl get hpa -n monipersonal
```

---

## 📝 **Terraform Commands**

### **Operações Comuns**
```bash
cd /home/rafael/projetos/Moni-Personal/infrastructure/terraform/environments/dev

# Ver estado
terraform show
terraform state list

# Output specific value
terraform output cluster_name
terraform output -raw gke_cluster_endpoint

# Refresh state
terraform refresh

# Import existing resource
terraform import google_compute_network.vpc projects/$PROJECT_ID/global/networks/vpc-name

# Taint resource (forçar recreate)
terraform taint module.gke_cluster.google_container_node_pool.primary_nodes

# Format code
terraform fmt -recursive

# Validate
terraform validate
```

### **Debugging**
```bash
# Verbose logging
TF_LOG=DEBUG terraform apply

# Specific module
TF_LOG=DEBUG terraform plan -target=module.vpc_networking

# Graph
terraform graph | dot -Tpng > graph.png
```

---

## 🔧 **Kustomize Commands**

### **Build & Apply**
```bash
cd /home/rafael/projetos/Moni-Personal/infrastructure/kubernetes

# Ver YAML gerado (dry-run)
kustomize build overlays/dev/

# Aplicar
kubectl apply -k overlays/dev/

# Delete
kubectl delete -k overlays/dev/

# Diff
kubectl diff -k overlays/dev/
```

---

## 🐛 **Troubleshooting Quick Fixes**

### **Pods não iniciam**
```bash
kubectl describe pod <POD> -n monipersonal | grep -A 5 Events
kubectl logs <POD> -n monipersonal --previous  # logs do pod anterior
```

### **ImagePullBackOff**
```bash
# Verificar se imagem existe
gcloud container images list --repository=gcr.io/$PROJECT_ID

# Verificar permissões
gcloud projects get-iam-policy $PROJECT_ID | grep serviceAccount
```

### **CrashLoopBackOff**
```bash
kubectl logs <POD> -n monipersonal --previous
kubectl describe pod <POD> -n monipersonal
```

### **LoadBalancer pending**
```bash
kubectl describe svc monipersonal-web -n monipersonal
kubectl get events -n monipersonal | grep LoadBalancer
```

---

## 📚 **Documentação Links**

- **Infrastructure**: `infrastructure/README.md`
- **Deployment**: `DEPLOYMENT-GCP.md`
- **Showcase**: `SHOWCASE-GUIDE.md`
- **Summary**: `PROJETO-CRIADO.md`

---

## ☎️ **Emergency Commands**

### **Cluster inacessível**
```bash
gcloud container clusters get-credentials monipersonal-dev \
  --zone us-central1-a --project $PROJECT_ID --internal-ip
```

### **Pod travado (force delete)**
```bash
kubectl delete pod <POD> -n monipersonal --grace-period=0 --force
```

### **Namespace travado**
```bash
kubectl get namespace monipersonal -o json \
  | jq '.spec.finalizers = []' \
  | kubectl replace --raw /api/v1/namespaces/monipersonal/finalize -f -
```

---

## 💾 **Backup & Restore**

### **Backup**
```bash
# Export all Kubernetes resources
kubectl get all -n monipersonal -o yaml > backup-$(date +%Y%m%d).yaml

# Terraform state
cd infrastructure/terraform/environments/dev
terraform state pull > terraform-state-backup-$(date +%Y%m%d).json
```

### **Restore**
```bash
# Kubernetes
kubectl apply -f backup-20250121.yaml

# Terraform (se state corrompido)
terraform state push terraform-state-backup-20250121.json
```

---

**Última atualização:** 2025-01-21
**Versão:** 1.0

**💡 Dica:** Adicione este arquivo aos seus bookmarks para acesso rápido!
