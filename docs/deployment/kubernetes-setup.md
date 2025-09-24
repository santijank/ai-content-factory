# 🚀 Kubernetes Setup Guide - AI Content Factory

คู่มือการติดตั้งและ deploy AI Content Factory บน Kubernetes cluster

## 📋 Prerequisites

### System Requirements
- Kubernetes cluster (v1.20+)
- kubectl configured
- Helm 3.x (optional)
- Docker registry access
- Minimum 4GB RAM, 2 CPU cores per node

### Required Tools
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm (optional)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify installation
kubectl version --client
```

## 🏗️ Cluster Preparation

### 1. Create Namespace
```bash
kubectl apply -f kubernetes/namespace.yaml
```

### 2. Set Default Namespace
```bash
kubectl config set-context --current --namespace=ai-content-factory
```

### 3. Create Storage Classes (if needed)
```bash
# For local storage (development)
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
EOF

# For cloud storage (production)
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/gce-pd  # Change based on cloud provider
parameters:
  type: pd-ssd
  replication-type: regional-pd
EOF
```

## 🔐 Secrets Management

### 1. Create Database Secrets
```bash
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=admin \
  --from-literal=POSTGRES_PASSWORD=your-secure-password \
  --from-literal=POSTGRES_DB=content_factory
```

### 2. Create AI API Secrets
```bash
kubectl create secret generic ai-api-secrets \
  --from-literal=GROQ_API_KEY=your-groq-key \
  --from-literal=OPENAI_API_KEY=your-openai-key \
  --from-literal=CLAUDE_API_KEY=your-claude-key \
  --from-literal=YOUTUBE_API_KEY=your-youtube-key
```

### 3. Create Platform Integration Secrets
```bash
kubectl create secret generic platform-secrets \
  --from-literal=YOUTUBE_CLIENT_ID=your-client-id \
  --from-literal=YOUTUBE_CLIENT_SECRET=your-client-secret \
  --from-literal=TIKTOK_ACCESS_TOKEN=your-tiktok-token
```

## 📦 ConfigMaps Setup

### 1. Apply Main ConfigMap
```bash
kubectl apply -f kubernetes/configmap.yaml
```

### 2. Create Custom ConfigMaps (if needed)
```bash
# Application configuration
kubectl create configmap app-config \
  --from-file=config/app_config.yaml \
  --from-file=config/ai_models.yaml \
  --from-file=config/quality_tiers.yaml

# Platform configurations
kubectl create configmap platform-config \
  --from-file=config/platform_configs/
```

## 🗄️ Database Deployment

### 1. Deploy PostgreSQL
```bash
# Create persistent volumes
kubectl apply -f kubernetes/storage/persistent-volumes.yaml

# Deploy PostgreSQL
kubectl apply -f kubernetes/deployments/postgres-deployment.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s
```

### 2. Initialize Database
```bash
# Run database migrations
kubectl run db-init --rm -i --restart=Never \
  --image=ai-content-factory/database:latest \
  --env="DATABASE_URL=postgresql://admin:password@postgres:5432/content_factory" \
  -- python migrate.py
```

## 🚀 Application Deployment

### 1. Build and Push Images
```bash
# Build all images
./scripts/build.sh

# Push to registry (update registry URL)
docker tag ai-content-factory/trend-monitor:latest your-registry/trend-monitor:latest
docker tag ai-content-factory/content-engine:latest your-registry/content-engine:latest
docker tag ai-content-factory/platform-manager:latest your-registry/platform-manager:latest
docker tag ai-content-factory/web-dashboard:latest your-registry/web-dashboard:latest

docker push your-registry/trend-monitor:latest
docker push your-registry/content-engine:latest
docker push your-registry/platform-manager:latest
docker push your-registry/web-dashboard:latest
```

### 2. Deploy Core Services
```bash
# Deploy in order
kubectl apply -f kubernetes/deployments/trend-monitor-deployment.yaml
kubectl apply -f kubernetes/deployments/content-engine-deployment.yaml
kubectl apply -f kubernetes/deployments/platform-manager-deployment.yaml
kubectl apply -f kubernetes/deployments/web-dashboard-deployment.yaml

# Wait for deployments
kubectl wait --for=condition=available deployment --all --timeout=600s
```

### 3. Create Services
```bash
kubectl apply -f kubernetes/services/all-services.yaml
```

### 4. Setup Ingress
```bash
# Install ingress controller (if not exists)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# Apply ingress configuration
kubectl apply -f kubernetes/ingress/main-ingress.yaml
```

## 📊 Monitoring Setup

### 1. Deploy Prometheus (Optional)
```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin123
```

### 2. Deploy Custom Monitoring
```bash
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: monitoring-dashboard
spec:
  replicas: 1
  selector:
    matchLabels:
      app: monitoring-dashboard
  template:
    metadata:
      labels:
        app: monitoring-dashboard
    spec:
      containers:
      - name: monitoring
        image: ai-content-factory/monitoring:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: DATABASE_URL
EOF
```

## ⚡ Auto-scaling Configuration

### 1. Apply HPA Configs
```bash
kubectl apply -f kubernetes/hpa/hpa-configs.yaml
```

### 2. Verify HPA
```bash
kubectl get hpa
kubectl describe hpa content-engine-hpa
```

## 🔍 Verification & Testing

### 1. Check All Pods
```bash
kubectl get pods -o wide
```

### 2. Check Services
```bash
kubectl get services
```

### 3. Check Ingress
```bash
kubectl get ingress
```

### 4. Test API Endpoints
```bash
# Get external IP
EXTERNAL_IP=$(kubectl get ingress main-ingress -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test endpoints
curl http://$EXTERNAL_IP/api/trends/health
curl http://$EXTERNAL_IP/api/content/health
curl http://$EXTERNAL_IP/api/platform/health
```

### 5. Check Logs
```bash
# Check logs for each service
kubectl logs -f deployment/trend-monitor
kubectl logs -f deployment/content-engine
kubectl logs -f deployment/platform-manager
kubectl logs -f deployment/web-dashboard
```

## 🔧 Configuration Management

### 1. Update Configuration
```bash
# Update configmap
kubectl apply -f kubernetes/configmap.yaml

# Restart deployments to pick up changes
kubectl rollout restart deployment/trend-monitor
kubectl rollout restart deployment/content-engine
kubectl rollout restart deployment/platform-manager
```

### 2. Update Secrets
```bash
# Update secret
kubectl delete secret ai-api-secrets
kubectl create secret generic ai-api-secrets \
  --from-literal=GROQ_API_KEY=new-groq-key \
  --from-literal=OPENAI_API_KEY=new-openai-key

# Restart affected deployments
kubectl rollout restart deployment/content-engine
```

## 📈 Scaling Operations

### 1. Manual Scaling
```bash
# Scale specific deployment
kubectl scale deployment content-engine --replicas=5

# Scale all deployments
kubectl scale deployment --all --replicas=3
```

### 2. Update Resource Limits
```bash
# Edit deployment
kubectl edit deployment content-engine

# Or apply updated YAML
kubectl apply -f kubernetes/deployments/content-engine-deployment.yaml
```

## 🗄️ Database Management

### 1. Database Backup
```bash
# Create backup job
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: db-backup-$(date +%Y%m%d)
spec:
  template:
    spec:
      containers:
      - name: backup
        image: postgres:13
        command: ["pg_dump"]
        args: ["-h", "postgres", "-U", "admin", "-d", "content_factory", "-f", "/backup/backup.sql"]
        env:
        - name: PGPASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: POSTGRES_PASSWORD
        volumeMounts:
        - name: backup-storage
          mountPath: /backup
      volumes:
      - name: backup-storage
        persistentVolumeClaim:
          claimName: backup-pvc
      restartPolicy: Never
EOF
```

### 2. Database Migration
```bash
# Run migration job
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate-$(date +%Y%m%d)
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: ai-content-factory/database:latest
        command: ["python", "migrate.py"]
        env:
        - name: DATABASE_URL
          value: "postgresql://admin:password@postgres:5432/content_factory"
      restartPolicy: Never
EOF
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Pods Not Starting
```bash
# Check pod status
kubectl describe pod <pod-name>

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp

# Check resource usage
kubectl top pods
kubectl top nodes
```

#### 2. Service Connection Issues
```bash
# Test service connectivity
kubectl run test-pod --rm -i --restart=Never --image=busybox -- sh
# Inside pod:
# nslookup postgres
# wget -qO- http://content-engine:8000/health
```

#### 3. Ingress Issues
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress configuration
kubectl describe ingress main-ingress

# Check ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

#### 4. Storage Issues
```bash
# Check PVs and PVCs
kubectl get pv
kubectl get pvc

# Check storage class
kubectl get storageclass
```

### Recovery Procedures

#### 1. Restart All Services
```bash
kubectl rollout restart deployment --all
```

#### 2. Reset Database
```bash
# Delete and recreate database
kubectl delete deployment postgres
kubectl delete pvc postgres-pvc
kubectl apply -f kubernetes/storage/persistent-volumes.yaml
kubectl apply -f kubernetes/deployments/postgres-deployment.yaml
```

## 🔄 Updates & Maintenance

### 1. Rolling Updates
```bash
# Update image version
kubectl set image deployment/content-engine content-engine=your-registry/content-engine:v2.0.0

# Check rollout status
kubectl rollout status deployment/content-engine

# Rollback if needed
kubectl rollout undo deployment/content-engine
```

### 2. Cluster Maintenance
```bash
# Drain node for maintenance
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Uncordon node after maintenance
kubectl uncordon <node-name>
```

## 📊 Production Monitoring

### 1. Resource Monitoring
```bash
# Check resource usage
kubectl top nodes
kubectl top pods --containers

# Check cluster events
kubectl get events --sort-by=.metadata.creationTimestamp
```

### 2. Application Monitoring
```bash
# Check application metrics
curl http://your-domain/api/monitoring/metrics

# Check service health
curl http://your-domain/api/trends/health
curl http://your-domain/api/content/health
curl http://your-domain/api/platform/health
```

## 🔒 Security Best Practices

### 1. Network Policies
```bash
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-content-factory-netpol
spec:
  podSelector:
    matchLabels:
      app: ai-content-factory
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector: {}
    ports:
    - protocol: TCP
      port: 8000
EOF
```

### 2. Pod Security Standards
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: ai-content-factory
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
EOF
```

## 📝 Environment-Specific Configurations

### Development Environment
```bash
# Use local storage and minimal resources
kubectl apply -f config/environment/development/
```

### Staging Environment
```bash
# Use cloud storage and moderate resources
kubectl apply -f config/environment/staging/
```

### Production Environment
```bash
# Use high-availability setup
kubectl apply -f config/environment/production/
```

---

## 🆘 Support & Resources

- **Documentation**: `/docs/`
- **Issue Tracking**: Check application logs
- **Monitoring**: Access Grafana dashboard
- **Backup**: Automated daily backups

ระบบพร้อมใช้งานแล้ว! 🎉