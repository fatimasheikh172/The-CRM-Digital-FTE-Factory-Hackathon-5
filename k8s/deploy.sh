#!/bin/bash
# TechCorp Customer Success FTE - Kubernetes Deployment Script
# For Linux/Mac

set -e

NAMESPACE="customer-success-fte"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================================"
echo "TechCorp Customer Success FTE - Kubernetes Deployment"
echo "============================================================"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "ERROR: kubectl is not installed or not in PATH"
    exit 1
fi

# Check cluster connection
echo "Checking cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    echo "ERROR: Cannot connect to Kubernetes cluster"
    echo "Please ensure you are connected to your cluster"
    exit 1
fi

echo "Connected to cluster: $(kubectl config current-context)"
echo ""

# Step 1: Create namespace
echo "[1/7] Creating namespace..."
kubectl apply -f "$SCRIPT_DIR/namespace.yaml"

# Step 2: Create ConfigMap
echo "[2/7] Creating ConfigMap..."
kubectl apply -f "$SCRIPT_DIR/configmap.yaml"

# Step 3: Create Secrets
echo "[3/7] Creating Secrets..."
echo "      NOTE: Remember to update secrets with real values!"
kubectl apply -f "$SCRIPT_DIR/secret.yaml"

# Step 4: Create Deployments
echo "[4/7] Creating Deployments..."
kubectl apply -f "$SCRIPT_DIR/deployments/"

# Step 5: Create Services
echo "[5/7] Creating Services..."
kubectl apply -f "$SCRIPT_DIR/services/"

# Step 6: Create Ingress
echo "[6/7] Creating Ingress..."
kubectl apply -f "$SCRIPT_DIR/ingress/"

# Step 7: Create HPAs
echo "[7/7] Creating HorizontalPodAutoscalers..."
kubectl apply -f "$SCRIPT_DIR/hpa/"

echo ""
echo "============================================================"
echo "Deployment initiated!"
echo "============================================================"
echo ""
echo "Checking pod status..."
sleep 5
kubectl get pods -n "$NAMESPACE"

echo ""
echo "To check deployment status:"
echo "  kubectl get all -n $NAMESPACE"
echo ""
echo "To view logs:"
echo "  kubectl logs -f -n $NAMESPACE -l component=api"
echo "  kubectl logs -f -n $NAMESPACE -l component=worker"
echo ""
echo "To access the API (if port-forwarding):"
echo "  kubectl port-forward -n $NAMESPACE svc/customer-success-fte 8000:80"
echo ""
echo "============================================================"
