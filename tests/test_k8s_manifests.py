"""
TechCorp Customer Success AI Agent - Kubernetes Manifest Tests

Validates YAML files for:
- All required files exist
- YAML syntax is valid
- Namespace consistent across files
- Labels match selectors
- Required fields present
"""

import os
import yaml
import pytest
from pathlib import Path
from typing import Dict, List, Any


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def k8s_dir() -> Path:
    """Get the k8s directory path."""
    return Path(__file__).parent.parent / "k8s"


@pytest.fixture
def k8s_files(k8s_dir: Path) -> Dict[str, Path]:
    """Get all k8s YAML files."""
    files = {
        "namespace": k8s_dir / "namespace.yaml",
        "configmap": k8s_dir / "configmap.yaml",
        "secret": k8s_dir / "secret.yaml",
        "api_deployment": k8s_dir / "deployments" / "api-deployment.yaml",
        "worker_deployment": k8s_dir / "deployments" / "worker-deployment.yaml",
        "api_service": k8s_dir / "services" / "api-service.yaml",
        "postgres_service": k8s_dir / "services" / "postgres-service.yaml",
        "ingress": k8s_dir / "ingress" / "ingress.yaml",
        "api_hpa": k8s_dir / "hpa" / "api-hpa.yaml",
        "worker_hpa": k8s_dir / "hpa" / "worker-hpa.yaml",
        "readme": k8s_dir / "README.md",
        "deploy_sh": k8s_dir / "deploy.sh",
        "deploy_bat": k8s_dir / "deploy.bat",
    }
    return files


@pytest.fixture
def namespace() -> str:
    """Expected namespace name."""
    return "customer-success-fte"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_yaml(file_path: Path) -> Any:
    """Load and parse a YAML file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_all_yaml(file_path: Path) -> List[Any]:
    """Load all documents from a multi-document YAML file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return list(yaml.safe_load_all(f))


# ============================================================================
# TEST 1: FILE EXISTENCE
# ============================================================================

class TestFileExistence:
    """Test that all required files exist."""

    def test_namespace_file_exists(self, k8s_files):
        """namespace.yaml exists."""
        assert k8s_files["namespace"].exists(), "namespace.yaml not found"

    def test_configmap_file_exists(self, k8s_files):
        """configmap.yaml exists."""
        assert k8s_files["configmap"].exists(), "configmap.yaml not found"

    def test_secret_file_exists(self, k8s_files):
        """secret.yaml exists."""
        assert k8s_files["secret"].exists(), "secret.yaml not found"

    def test_api_deployment_file_exists(self, k8s_files):
        """deployments/api-deployment.yaml exists."""
        assert k8s_files["api_deployment"].exists(), "api-deployment.yaml not found"

    def test_worker_deployment_file_exists(self, k8s_files):
        """deployments/worker-deployment.yaml exists."""
        assert k8s_files["worker_deployment"].exists(), "worker-deployment.yaml not found"

    def test_api_service_file_exists(self, k8s_files):
        """services/api-service.yaml exists."""
        assert k8s_files["api_service"].exists(), "api-service.yaml not found"

    def test_ingress_file_exists(self, k8s_files):
        """ingress/ingress.yaml exists."""
        assert k8s_files["ingress"].exists(), "ingress.yaml not found"

    def test_api_hpa_file_exists(self, k8s_files):
        """hpa/api-hpa.yaml exists."""
        assert k8s_files["api_hpa"].exists(), "api-hpa.yaml not found"

    def test_worker_hpa_file_exists(self, k8s_files):
        """hpa/worker-hpa.yaml exists."""
        assert k8s_files["worker_hpa"].exists(), "worker-hpa.yaml not found"

    def test_readme_file_exists(self, k8s_files):
        """README.md exists."""
        assert k8s_files["readme"].exists(), "README.md not found"

    def test_deploy_scripts_exist(self, k8s_files):
        """deploy.sh and deploy.bat exist."""
        assert k8s_files["deploy_sh"].exists(), "deploy.sh not found"
        assert k8s_files["deploy_bat"].exists(), "deploy.bat not found"


# ============================================================================
# TEST 2: YAML SYNTAX VALIDATION
# ============================================================================

class TestYamlSyntax:
    """Test that all YAML files have valid syntax."""

    def test_namespace_yaml_valid(self, k8s_files):
        """namespace.yaml has valid YAML syntax."""
        data = load_yaml(k8s_files["namespace"])
        assert data is not None

    def test_configmap_yaml_valid(self, k8s_files):
        """configmap.yaml has valid YAML syntax."""
        data = load_yaml(k8s_files["configmap"])
        assert data is not None
        assert data.get("data") is not None

    def test_secret_yaml_valid(self, k8s_files):
        """secret.yaml has valid YAML syntax."""
        data = load_yaml(k8s_files["secret"])
        assert data is not None
        assert data.get("type") == "Opaque"

    def test_api_deployment_yaml_valid(self, k8s_files):
        """api-deployment.yaml has valid YAML syntax."""
        data = load_yaml(k8s_files["api_deployment"])
        assert data is not None
        assert data.get("spec") is not None

    def test_worker_deployment_yaml_valid(self, k8s_files):
        """worker-deployment.yaml has valid YAML syntax."""
        data = load_yaml(k8s_files["worker_deployment"])
        assert data is not None

    def test_ingress_yaml_valid(self, k8s_files):
        """ingress.yaml has valid YAML syntax."""
        data = load_all_yaml(k8s_files["ingress"])
        assert len(data) > 0


# ============================================================================
# TEST 3: NAMESPACE CONSISTENCY
# ============================================================================

class TestNamespaceConsistency:
    """Test that namespace is consistent across all files."""

    def test_namespace_name_correct(self, k8s_files, namespace):
        """Namespace name is correct."""
        data = load_yaml(k8s_files["namespace"])
        assert data["metadata"]["name"] == namespace

    def test_configmap_namespace(self, k8s_files, namespace):
        """ConfigMap uses correct namespace."""
        data = load_yaml(k8s_files["configmap"])
        assert data["metadata"]["namespace"] == namespace

    def test_secret_namespace(self, k8s_files, namespace):
        """Secret uses correct namespace."""
        data = load_yaml(k8s_files["secret"])
        assert data["metadata"]["namespace"] == namespace

    def test_api_deployment_namespace(self, k8s_files, namespace):
        """API Deployment uses correct namespace."""
        data = load_yaml(k8s_files["api_deployment"])
        assert data["metadata"]["namespace"] == namespace
        assert data["spec"]["template"]["metadata"]["labels"]["app"] == namespace

    def test_worker_deployment_namespace(self, k8s_files, namespace):
        """Worker Deployment uses correct namespace."""
        data = load_yaml(k8s_files["worker_deployment"])
        assert data["metadata"]["namespace"] == namespace
        assert data["spec"]["template"]["metadata"]["labels"]["app"] == namespace

    def test_service_namespace(self, k8s_files, namespace):
        """Service uses correct namespace."""
        data = load_yaml(k8s_files["api_service"])
        assert data["metadata"]["namespace"] == namespace

    def test_ingress_namespace(self, k8s_files, namespace):
        """Ingress uses correct namespace."""
        data = load_all_yaml(k8s_files["ingress"])
        for doc in data:
            if doc and doc.get("kind") == "Ingress":
                assert doc["metadata"]["namespace"] == namespace

    def test_hpa_namespace(self, k8s_files, namespace):
        """HPAs use correct namespace."""
        for hpa_file in ["api_hpa", "worker_hpa"]:
            data = load_yaml(k8s_files[hpa_file])
            assert data["metadata"]["namespace"] == namespace


# ============================================================================
# TEST 4: LABEL SELECTOR MATCHING
# ============================================================================

class TestLabelSelectors:
    """Test that labels and selectors match correctly."""

    def test_api_deployment_selector_matches_template(self, k8s_files):
        """API Deployment selector matches template labels."""
        data = load_yaml(k8s_files["api_deployment"])
        selector = data["spec"]["selector"]["matchLabels"]
        template_labels = data["spec"]["template"]["metadata"]["labels"]
        
        for key, value in selector.items():
            assert template_labels.get(key) == value, \
                f"API Deployment selector {key}={value} doesn't match template"

    def test_worker_deployment_selector_matches_template(self, k8s_files):
        """Worker Deployment selector matches template labels."""
        data = load_yaml(k8s_files["worker_deployment"])
        selector = data["spec"]["selector"]["matchLabels"]
        template_labels = data["spec"]["template"]["metadata"]["labels"]
        
        for key, value in selector.items():
            assert template_labels.get(key) == value, \
                f"Worker Deployment selector {key}={value} doesn't match template"

    def test_service_selector_matches_deployment(self, k8s_files):
        """Service selector matches API Deployment labels."""
        service_data = load_yaml(k8s_files["api_service"])
        deployment_data = load_yaml(k8s_files["api_deployment"])
        
        service_selector = service_data["spec"]["selector"]
        deployment_labels = deployment_data["spec"]["template"]["metadata"]["labels"]
        
        for key, value in service_selector.items():
            assert deployment_labels.get(key) == value, \
                f"Service selector {key}={value} doesn't match Deployment labels"


# ============================================================================
# TEST 5: REQUIRED FIELDS
# ============================================================================

class TestRequiredFields:
    """Test that required fields are present."""

    def test_deployment_has_image(self, k8s_files):
        """Deployments have image specified."""
        for dep_file in ["api_deployment", "worker_deployment"]:
            data = load_yaml(k8s_files[dep_file])
            containers = data["spec"]["template"]["spec"]["containers"]
            for container in containers:
                assert "image" in container, f"{dep_file} missing image"

    def test_deployment_has_resources(self, k8s_files):
        """Deployments have resource limits."""
        for dep_file in ["api_deployment", "worker_deployment"]:
            data = load_yaml(k8s_files[dep_file])
            containers = data["spec"]["template"]["spec"]["containers"]
            for container in containers:
                assert "resources" in container, f"{dep_file} missing resources"
                assert "limits" in container["resources"], f"{dep_file} missing limits"
                assert "memory" in container["resources"]["limits"], f"{dep_file} missing memory limit"
                assert "cpu" in container["resources"]["limits"], f"{dep_file} missing cpu limit"

    def test_api_deployment_has_probes(self, k8s_files):
        """API Deployment has health probes."""
        data = load_yaml(k8s_files["api_deployment"])
        containers = data["spec"]["template"]["spec"]["containers"]
        
        for container in containers:
            assert "livenessProbe" in container, "API Deployment missing livenessProbe"
            assert "readinessProbe" in container, "API Deployment missing readinessProbe"
            
            # Check probe paths
            assert container["livenessProbe"]["httpGet"]["path"] == "/health"
            assert container["readinessProbe"]["httpGet"]["path"] == "/health"

    def test_hpa_has_scaling_bounds(self, k8s_files):
        """HPAs have min and max replicas."""
        for hpa_file in ["api_hpa", "worker_hpa"]:
            data = load_yaml(k8s_files[hpa_file])
            assert "minReplicas" in data["spec"], f"{hpa_file} missing minReplicas"
            assert "maxReplicas" in data["spec"], f"{hpa_file} missing maxReplicas"
            assert data["spec"]["minReplicas"] >= 1
            assert data["spec"]["maxReplicas"] >= data["spec"]["minReplicas"]

    def test_hpa_has_metrics(self, k8s_files):
        """HPAs have scaling metrics."""
        for hpa_file in ["api_hpa", "worker_hpa"]:
            data = load_yaml(k8s_files[hpa_file])
            assert "metrics" in data["spec"], f"{hpa_file} missing metrics"
            assert len(data["spec"]["metrics"]) > 0, f"{hpa_file} has no metrics"


# ============================================================================
# TEST 6: SCALING CONFIGURATION
# ============================================================================

class TestScalingConfiguration:
    """Test scaling configuration is correct."""

    def test_api_hpa_replica_bounds(self, k8s_files):
        """API HPA has correct replica bounds (3-20)."""
        data = load_yaml(k8s_files["api_hpa"])
        assert data["spec"]["minReplicas"] == 3, "API minReplicas should be 3"
        assert data["spec"]["maxReplicas"] == 20, "API maxReplicas should be 20"

    def test_worker_hpa_replica_bounds(self, k8s_files):
        """Worker HPA has correct replica bounds (3-30)."""
        data = load_yaml(k8s_files["worker_hpa"])
        assert data["spec"]["minReplicas"] == 3, "Worker minReplicas should be 3"
        assert data["spec"]["maxReplicas"] == 30, "Worker maxReplicas should be 30"

    def test_hpa_cpu_target(self, k8s_files):
        """HPAs have 70% CPU target."""
        for hpa_file in ["api_hpa", "worker_hpa"]:
            data = load_yaml(k8s_files[hpa_file])
            cpu_metrics = [
                m for m in data["spec"]["metrics"]
                if m.get("resource", {}).get("name") == "cpu"
            ]
            assert len(cpu_metrics) > 0, f"{hpa_file} missing CPU metric"
            assert cpu_metrics[0]["resource"]["target"]["averageUtilization"] == 70


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
