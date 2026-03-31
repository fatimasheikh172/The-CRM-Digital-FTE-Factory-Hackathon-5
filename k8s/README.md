# Kubernetes Deployment Guide

## TechCorp Customer Success FTE

This directory contains all Kubernetes manifests for deploying the TechCorp Customer Success AI Agent.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Namespace: customer-success-fte              │   │
│  │                                                       │   │
│  │  ┌─────────────┐      ┌─────────────┐               │   │
│  │  │  fte-api    │      │ fte-worker  │               │   │
│  │  │  (x3-20)    │      │   (x3-30)   │               │   │
│  │  │ Deployment  │      │  Deployment │               │   │
│  │  └──────┬──────┘      └──────┬──────┘               │   │
│  │         │                    │                       │   │
│  │  ┌──────▼────────────────────▼──────┐               │   │
│  │  │         ClusterIP Service         │               │   │
│  │  │    customer-success-fte:80        │               │   │
│  │  └───────────────┬───────────────────┘               │   │
│  │                  │                                   │   │
│  │  ┌───────────────▼───────────────────┐               │   │
│  │  │         NGINX Ingress              │               │   │
│  │  │   support-api.techcorp.com         │               │   │
│  │  └───────────────────────────────────┘               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  External Services:                                          │
│  - PostgreSQL (StatefulSet or external)                     │
│  - Kafka (StatefulSet or external)                          │
│  - Gemini API (Google Cloud)                                │
│  - Twilio API (WhatsApp)                                    │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- **kubectl** installed and configured
- **Docker** for building images
- Access to a **Kubernetes cluster** (minikube, kind, EKS, GKE, AKS, etc.)
- **NGINX Ingress Controller** installed (for production)
- **cert-manager** installed (for TLS certificates)

## Quick Start (Local Testing with minikube)

### 1. Start minikube

```bash
minikube start --memory=4096 --cpus=2
```

### 2. Build Docker image

```bash
eval $(minikube docker-env)
docker build -t customer-success-fte:latest .
```

### 3. Deploy to minikube

```bash
cd k8s
./deploy.sh    # Linux/Mac
# or
deploy.bat     # Windows
```

### 4. Access the API

```bash
# Port forward
kubectl port-forward -n customer-success-fte svc/customer-success-fte 8000:80

# Or use minikube service
minikube service customer-success-fte -n customer-success-fte --url
```

### 5. Check status

```bash
kubectl get all -n customer-success-fte
# or
cd k8s && status.bat
```

## Production Deployment

### 1. Update Configuration

Edit `k8s/configmap.yaml` with your production settings:
- Kafka bootstrap servers
- PostgreSQL connection details
- Environment variables

### 2. Configure Secrets

**IMPORTANT**: Do not use the default `secret.yaml` in production!

Use one of these approaches:

#### Option A: External Secrets Operator (Recommended)

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: fte-secrets
  namespace: customer-success-fte
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: fte-secrets
  data:
  - secretKey: GEMINI_API_KEY
    remoteRef:
      key: techcorp/fte/gemini-api-key
```

#### Option B: Sealed Secrets

```bash
# Install kubeseal
# Then seal your secrets
kubeseal --format yaml < k8s/secret.yaml > k8s/secret-sealed.yaml
kubectl apply -f k8s/secret-sealed.yaml
```

#### Option C: Manual Secret Creation

```bash
kubectl create secret generic fte-secrets \
  -n customer-success-fte \
  --from-literal=GEMINI_API_KEY=your-actual-key \
  --from-literal=POSTGRES_PASSWORD=your-actual-password
```

### 3. Build and Push Image

```bash
docker build -t your-registry/customer-success-fte:v2.6.0 .
docker push your-registry/customer-success-fte:v2.6.0
```

Update image reference in deployment files.

### 4. Deploy

```bash
cd k8s
./deploy.sh
```

### 5. Verify Deployment

```bash
kubectl get pods -n customer-success-fte
kubectl get hpa -n customer-success-fte
kubectl get ingress -n customer-success-fte
```

## Scaling

### Automatic Scaling (HPA)

The HorizontalPodAutoscalers are configured to:

| Component | Min Replicas | Max Replicas | CPU Target | Memory Target |
|-----------|--------------|--------------|------------|---------------|
| API       | 3            | 20           | 70%        | 80%           |
| Worker    | 3            | 30           | 70%        | 80%           |

### Manual Scaling

```bash
# Scale API
kubectl scale deployment fte-api -n customer-success-fte --replicas=5

# Scale Workers
kubectl scale deployment fte-worker -n customer-success-fte --replicas=10
```

### Event-Driven Scaling (KEDA)

For Kafka-based scaling, install KEDA:

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm install keda kedacore/keda-operator -n keda --create-namespace
```

Then apply the ScaledObject configuration (see worker-hpa.yaml comments).

## Monitoring

### Check Pod Status

```bash
kubectl get pods -n customer-success-fte
kubectl describe pod <pod-name> -n customer-success-fte
```

### View Logs

```bash
# API logs
kubectl logs -f -n customer-success-fte -l component=api

# Worker logs
kubectl logs -f -n customer-success-fte -l component=worker

# Specific pod
kubectl logs -f <pod-name> -n customer-success-fte
```

### Health Check

```bash
# Port forward
kubectl port-forward -n customer-success-fte svc/customer-success-fte 8000:80

# Then
curl http://localhost:8000/health
```

### Prometheus Metrics

If Prometheus is installed, the API exposes metrics at `/metrics`.

## Troubleshooting

### Pod Not Starting

```bash
# Check events
kubectl get events -n customer-success-fte --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod <pod-name> -n customer-success-fte

# Check logs
kubectl logs <pod-name> -n customer-success-fte
```

### Database Connection Issues

1. Verify PostgreSQL is running
2. Check ConfigMap has correct host
3. Verify Secret has correct password
4. Check network policies

### Kafka Connection Issues

1. Verify Kafka is accessible from the cluster
2. Check bootstrap servers in ConfigMap
3. Verify network connectivity

## Rollback

```bash
# Rollback deployment
kubectl rollout undo deployment/fte-api -n customer-success-fte
kubectl rollout undo deployment/fte-worker -n customer-success-fte

# Check rollout history
kubectl rollout history deployment/fte-api -n customer-success-fte
```

## Cleanup

```bash
# Delete all resources
kubectl delete namespace customer-success-fte

# Or delete individual resources
kubectl delete -f k8s/hpa/
kubectl delete -f k8s/ingress/
kubectl delete -f k8s/services/
kubectl delete -f k8s/deployments/
kubectl delete -f k8s/secret.yaml
kubectl delete -f k8s/configmap.yaml
kubectl delete -f k8s/namespace.yaml
```

## File Structure

```
k8s/
├── namespace.yaml           # Namespace definition
├── configmap.yaml           # Configuration (non-sensitive)
├── secret.yaml              # Secrets (use external secrets in prod)
├── deploy.sh                # Deployment script (Linux/Mac)
├── deploy.bat               # Deployment script (Windows)
├── status.bat               # Status check script (Windows)
├── README.md                # This file
├── deployments/
│   ├── api-deployment.yaml  # API server deployment
│   └── worker-deployment.yaml # Worker deployment
├── services/
│   ├── api-service.yaml     # API ClusterIP service
│   └── postgres-service.yaml # PostgreSQL service
├── ingress/
│   └── ingress.yaml         # NGINX Ingress
└── hpa/
    ├── api-hpa.yaml         # API autoscaler
    └── worker-hpa.yaml      # Worker autoscaler
```

## Security Considerations

1. **Network Policies**: Implement network policies to restrict pod-to-pod communication
2. **Pod Security Standards**: Use restricted pod security standard
3. **Secrets Management**: Use External Secrets or Vault
4. **Image Security**: Scan images for vulnerabilities
5. **RBAC**: Implement least-privilege access
6. **TLS**: Always use TLS for ingress traffic

## Support

For issues or questions:
- Check Kubernetes events: `kubectl get events -n customer-success-fte`
- Review pod logs
- Verify ConfigMap and Secret values
- Check cluster resources (CPU, memory)
