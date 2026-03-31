@echo off
REM TechCorp Customer Success FTE - Kubernetes Status Check
REM For Windows

setlocal

set NAMESPACE=customer-success-fte

echo ============================================================
echo TechCorp Customer Success FTE - Cluster Status
echo ============================================================
echo.

REM Check if kubectl is available
where kubectl >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: kubectl is not installed or not in PATH
    exit /b 1
)

echo Namespace: %NAMESPACE%
echo.

echo === Pods ===
kubectl get pods -n %NAMESPACE% -o wide
echo.

echo === Deployments ===
kubectl get deployments -n %NAMESPACE%
echo.

echo === Services ===
kubectl get services -n %NAMESPACE%
echo.

echo === Ingress ===
kubectl get ingress -n %NAMESPACE%
echo.

echo === HorizontalPodAutoscalers ===
kubectl get hpa -n %NAMESPACE%
echo.

echo === ConfigMaps ===
kubectl get configmaps -n %NAMESPACE%
echo.

echo === Secrets ===
kubectl get secrets -n %NAMESPACE%
echo.

echo === Recent Events ===
kubectl get events -n %NAMESPACE% --sort-by='.lastTimestamp'
echo.

echo ============================================================
echo For detailed pod info: kubectl describe pod ^<pod-name^> -n %NAMESPACE%
echo For logs: kubectl logs -f -n %NAMESPACE% -l component=api
echo ============================================================

endlocal
