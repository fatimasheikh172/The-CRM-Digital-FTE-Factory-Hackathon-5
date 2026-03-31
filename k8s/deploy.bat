@echo off
REM TechCorp Customer Success FTE - Kubernetes Deployment Script
REM For Windows

setlocal enabledelayedexpansion

set NAMESPACE=customer-success-fte
set SCRIPT_DIR=%~dp0

echo ============================================================
echo TechCorp Customer Success FTE - Kubernetes Deployment
echo ============================================================
echo.

REM Check if kubectl is available
where kubectl >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: kubectl is not installed or not in PATH
    echo Please install kubectl and add it to your PATH
    exit /b 1
)

REM Check cluster connection
echo Checking cluster connection...
kubectl cluster-info >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Cannot connect to Kubernetes cluster
    echo Please ensure you are connected to your cluster
    exit /b 1
)

echo Connected to cluster:
kubectl config current-context
echo.

REM Step 1: Create namespace
echo [1/7] Creating namespace...
kubectl apply -f "%SCRIPT_DIR%namespace.yaml"

REM Step 2: Create ConfigMap
echo [2/7] Creating ConfigMap...
kubectl apply -f "%SCRIPT_DIR%configmap.yaml"

REM Step 3: Create Secrets
echo [3/7] Creating Secrets...
echo       NOTE: Remember to update secrets with real values!
kubectl apply -f "%SCRIPT_DIR%secret.yaml"

REM Step 4: Create Deployments
echo [4/7] Creating Deployments...
kubectl apply -f "%SCRIPT_DIR%deployments/"

REM Step 5: Create Services
echo [5/7] Creating Services...
kubectl apply -f "%SCRIPT_DIR%services/"

REM Step 6: Create Ingress
echo [6/7] Creating Ingress...
kubectl apply -f "%SCRIPT_DIR%ingress/"

REM Step 7: Create HPAs
echo [7/7] Creating HorizontalPodAutoscalers...
kubectl apply -f "%SCRIPT_DIR%hpa/"

echo.
echo ============================================================
echo Deployment initiated!
echo ============================================================
echo.
echo Checking pod status...
timeout /t 5 /nobreak >nul
kubectl get pods -n %NAMESPACE%

echo.
echo To check deployment status:
echo   kubectl get all -n %NAMESPACE%
echo.
echo To view logs:
echo   kubectl logs -f -n %NAMESPACE% -l component=api
echo   kubectl logs -f -n %NAMESPACE% -l component=worker
echo.
echo To access the API (if port-forwarding):
echo   kubectl port-forward -n %NAMESPACE% svc/customer-success-fte 8000:80
echo.
echo ============================================================

endlocal
