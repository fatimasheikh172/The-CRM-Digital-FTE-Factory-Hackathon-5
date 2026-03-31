"""
TechCorp Customer Success AI Agent - Load Tests

Tests that run using FastAPI TestClient instead of aiohttp.
"""

import pytest
import asyncio
import time
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from api.main import app


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Get TestClient for API."""
    return TestClient(app)


# ============================================================================
# TEST 1: WEB FORM UNDER LOAD
# ============================================================================

class TestWebFormUnderLoad:
    """Test web form endpoint under load."""

    def test_web_form_under_load(self, client):
        """
        Web form load test.

        Send 20 concurrent form submissions.
        All must succeed (200 response).
        P95 under 3000ms.
        No errors.
        """
        form_data = {
            "name": "Load Test User",
            "email": "loadtest@test.com",
            "subject": "Load Test",
            "category": "General",
            "priority": "medium",
            "message": "This is a load test message."
        }

        results = []
        
        def send_request():
            start = time.time()
            response = client.post("/support/submit", json=form_data)
            elapsed = (time.time() - start) * 1000
            return {
                "status": response.status_code,
                "latency_ms": elapsed,
                "success": response.status_code == 200
            }

        # Send 20 requests with 10 concurrent
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(send_request) for _ in range(20)]
            results = [f.result() for f in futures]

        success_count = sum(1 for r in results if r["success"])
        failed_count = sum(1 for r in results if not r["success"])
        latencies = sorted([r["latency_ms"] for r in results])
        p95_ms = latencies[int(len(latencies) * 0.95)] if latencies else 0

        # Assertions
        assert success_count == 20, f"Expected 20 successes, got {success_count}"
        assert failed_count == 0, f"Expected 0 failures, got {failed_count}"
        assert p95_ms < 3000, f"P95 {p95_ms}ms exceeds 3000ms"


# ============================================================================
# TEST 2: EMAIL WEBHOOK UNDER LOAD
# ============================================================================

class TestEmailWebhookUnderLoad:
    """Test email webhook endpoint under load."""

    def test_email_webhook_under_load(self, client):
        """
        Email webhook load test.

        Send 20 concurrent email webhooks.
        All must succeed.
        P95 under 2000ms.
        """
        email_data = {
            "from_email": "test@test.com",
            "subject": "Load Test",
            "body": "Load test message"
        }

        results = []
        
        def send_request():
            start = time.time()
            response = client.post("/webhooks/gmail/test", json=email_data)
            elapsed = (time.time() - start) * 1000
            return {
                "status": response.status_code,
                "latency_ms": elapsed,
                "success": response.status_code == 200
            }

        # Send 20 requests with 10 concurrent
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(send_request) for _ in range(20)]
            results = [f.result() for f in futures]

        success_count = sum(1 for r in results if r["success"])
        failed_count = sum(1 for r in results if not r["success"])
        latencies = sorted([r["latency_ms"] for r in results])
        p95_ms = latencies[int(len(latencies) * 0.95)] if latencies else 0

        # Assertions
        assert success_count == 20, f"Expected 20 successes, got {success_count}"
        assert failed_count == 0, f"Expected 0 failures, got {failed_count}"
        assert p95_ms < 2000, f"P95 {p95_ms}ms exceeds 2000ms"


# ============================================================================
# TEST 3: WHATSAPP UNDER LOAD
# ============================================================================

class TestWhatsAppUnderLoad:
    """Test WhatsApp webhook endpoint under load."""

    def test_whatsapp_under_load(self, client):
        """
        WhatsApp load test.

        Send 20 concurrent WhatsApp webhooks.
        All must succeed.
        P95 under 2000ms.
        """
        whatsapp_data = {
            "from_phone": "+14155551234",
            "body": "load test"
        }

        results = []
        
        def send_request():
            start = time.time()
            response = client.post("/webhooks/whatsapp/test", json=whatsapp_data)
            elapsed = (time.time() - start) * 1000
            return {
                "status": response.status_code,
                "latency_ms": elapsed,
                "success": response.status_code == 200
            }

        # Send 20 requests with 10 concurrent
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(send_request) for _ in range(20)]
            results = [f.result() for f in futures]

        success_count = sum(1 for r in results if r["success"])
        failed_count = sum(1 for r in results if not r["success"])
        latencies = sorted([r["latency_ms"] for r in results])
        p95_ms = latencies[int(len(latencies) * 0.95)] if latencies else 0

        # Assertions
        assert success_count == 20, f"Expected 20 successes, got {success_count}"
        assert failed_count == 0, f"Expected 0 failures, got {failed_count}"
        assert p95_ms < 2000, f"P95 {p95_ms}ms exceeds 2000ms"


# ============================================================================
# TEST 4: HEALTH CHECK STABILITY
# ============================================================================

class TestHealthCheckStability:
    """Test health check endpoint stability under load."""

    def test_health_check_stability(self, client):
        """
        Health check stability test.

        Send 50 concurrent health checks.
        ALL must return healthy.
        P95 under 500ms.
        """
        results = []
        
        def send_request():
            start = time.time()
            response = client.get("/health")
            elapsed = (time.time() - start) * 1000
            return {
                "status": response.status_code,
                "latency_ms": elapsed,
                "success": response.status_code == 200
            }

        # Send 50 requests with 20 concurrent
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(send_request) for _ in range(50)]
            results = [f.result() for f in futures]

        success_count = sum(1 for r in results if r["success"])
        failed_count = sum(1 for r in results if not r["success"])
        latencies = sorted([r["latency_ms"] for r in results])
        p95_ms = latencies[int(len(latencies) * 0.95)] if latencies else 0

        # Assertions
        assert success_count == 50, f"Expected 50 successes, got {success_count}"
        assert failed_count == 0, f"Expected 0 failures, got {failed_count}"
        assert p95_ms < 500, f"P95 {p95_ms}ms exceeds 500ms"


# ============================================================================
# TEST 5: MIXED TRAFFIC LOAD
# ============================================================================

class TestMixedTrafficLoad:
    """Test mixed traffic across all channels."""

    def test_mixed_traffic_load(self, client):
        """
        Mixed traffic load test.

        Send simultaneously:
        - 10 web form submissions
        - 5 email webhooks
        - 5 WhatsApp webhooks
        - 10 health checks

        All must succeed.
        No interference between channels.
        """
        results = []
        
        def send_form():
            form_data = {
                "name": "Mixed Test",
                "email": "mixed@test.com",
                "subject": "Mixed Test",
                "category": "General",
                "priority": "medium",
                "message": "Mixed traffic test"
            }
            response = client.post("/support/submit", json=form_data)
            return response.status_code == 200

        def send_email():
            email_data = {
                "from_email": "mixed@test.com",
                "subject": "Mixed Test",
                "body": "Mixed test"
            }
            response = client.post("/webhooks/gmail/test", json=email_data)
            return response.status_code == 200

        def send_whatsapp():
            whatsapp_data = {
                "from_phone": "+14155551234",
                "body": "mixed test"
            }
            response = client.post("/webhooks/whatsapp/test", json=whatsapp_data)
            return response.status_code == 200

        def send_health():
            response = client.get("/health")
            return response.status_code == 200

        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = []
            # Web form - 10 requests
            for _ in range(10):
                futures.append(executor.submit(send_form))
            # Email - 5 requests
            for _ in range(5):
                futures.append(executor.submit(send_email))
            # WhatsApp - 5 requests
            for _ in range(5):
                futures.append(executor.submit(send_whatsapp))
            # Health checks - 10 requests
            for _ in range(10):
                futures.append(executor.submit(send_health))

            results = [f.result() for f in futures]

        success_count = sum(1 for r in results if r)

        # Assertions
        assert success_count == 30, f"Expected 30 successes, got {success_count}"


# ============================================================================
# TEST 6: BENCHMARK VALIDATION
# ============================================================================

class TestBenchmarkValidation:
    """Test benchmark validation."""

    def test_benchmark_validator(self):
        """Test that benchmark validator works correctly."""
        from benchmarks import BenchmarkValidator

        validator = BenchmarkValidator()

        # Sample results
        sample_results = {
            "web_form": {
                "total": 100,
                "success": 99,
                "failed": 1,
                "p95_ms": 2500,
                "rps": 15
            },
            "health_check": {
                "total": 200,
                "success": 200,
                "failed": 0,
                "p95_ms": 80,
                "rps": 100
            }
        }

        validation = validator.validate_results(sample_results)

        # Check validation structure
        assert "web_form" in validation
        assert "health_check" in validation
        assert "passed" in validation["web_form"]
        assert "details" in validation["web_form"]


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
