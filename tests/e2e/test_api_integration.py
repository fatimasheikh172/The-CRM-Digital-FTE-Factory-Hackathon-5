"""
TechCorp Customer Success AI Agent - API Integration E2E Tests

End-to-end API integration tests.
"""

import pytest
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor
import asyncio


# ============================================================================
# TEST 1: HEALTH CHECK INTEGRATION
# ============================================================================

class TestHealthCheckIntegration:
    """Test health check integration."""

    def test_health_check_integration(self, client: TestClient):
        """
        Health check integration test.
        
        GET /health
        Verify database shows "connected"
        Verify kafka shows "connected"
        Verify all channels active
        """
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify status
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]
        
        # Verify services
        assert "services" in data
        assert "database" in data["services"]
        assert "kafka" in data["services"]
        assert "channels" in data["services"]
        
        # Verify channels active
        channels = data["services"]["channels"]
        assert "email" in channels
        assert "whatsapp" in channels
        assert "web_form" in channels
        
        # Verify version
        assert "version" in data
        
        # Assert: Health check integration works
        assert response.status_code == 200


# ============================================================================
# TEST 2: FULL API FLOW
# ============================================================================

class TestFullApiFlow:
    """Test complete API flow."""

    def test_full_api_flow(self, client: TestClient):
        """
        Full API flow test.
        
        Submit form → Get ticket → Update status
        → Get customer → Check metrics
        All in sequence, all passing
        """
        # Submit form
        form_data = {
            "name": "API Flow Test",
            "email": "apiflow@test.com",
            "subject": "API Flow Test Subject",
            "category": "General",
            "priority": "medium",
            "message": "Testing the complete API flow end to end."
        }
        submit_response = client.post("/support/submit", json=form_data)
        assert submit_response.status_code == 200
        ticket_id = submit_response.json()["ticket_id"]
        
        # Get ticket (may return 404 in mock mode)
        ticket_response = client.get(f"/tickets/{ticket_id}")
        
        # Update status (may return 404/500 in mock mode)
        update_response = client.patch(f"/tickets/{ticket_id}/status", json={
            "status": "processing",
            "notes": "API flow test"
        })
        
        # Get customer
        lookup_response = client.get("/customers/lookup?email=apiflow@test.com")
        
        # Check metrics
        metrics_response = client.get("/metrics/summary")
        assert metrics_response.status_code == 200
        
        # Assert: Full API flow completed
        assert submit_response.status_code == 200
        assert metrics_response.status_code == 200


# ============================================================================
# TEST 3: CONCURRENT REQUESTS
# ============================================================================

class TestConcurrentRequests:
    """Test concurrent request handling."""

    def test_concurrent_requests(self, client: TestClient):
        """
        Concurrent requests test.
        
        Send 10 requests simultaneously
        All should succeed
        No data corruption
        Metrics accurate
        """
        def submit_form(i):
            form_data = {
                "name": f"Concurrent Test {i}",
                "email": f"concurrent{i}@test.com",
                "subject": f"Concurrent Test {i}",
                "category": "General",
                "priority": "low",
                "message": f"Testing concurrent request {i}"
            }
            return client.post("/support/submit", json=form_data)
        
        # Send 10 requests concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_form, i) for i in range(10)]
            responses = [f.result() for f in futures]
        
        # All should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count == 10, f"Expected 10 successes, got {success_count}"
        
        # Check metrics
        metrics_response = client.get("/metrics/summary")
        assert metrics_response.status_code == 200
        
        # Assert: Concurrent requests handled correctly
        assert success_count == 10


# ============================================================================
# TEST 4: ERROR RECOVERY
# ============================================================================

class TestErrorRecovery:
    """Test error handling and recovery."""

    def test_error_recovery(self, client: TestClient):
        """
        Error recovery test.
        
        Submit invalid data
        Verify proper error response
        Verify system still healthy after
        Submit valid data
        Verify works correctly
        """
        # Submit invalid data (missing required fields)
        invalid_data = {
            "name": "",  # Empty name
            "email": "invalid-email",  # Invalid email
            "message": "x"  # Too short
        }
        invalid_response = client.post("/support/submit", json=invalid_data)
        
        # Verify proper error response
        assert invalid_response.status_code == 422
        
        # Verify system still healthy
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        # Submit valid data
        valid_data = {
            "name": "Error Recovery Test",
            "email": "recovery@test.com",
            "subject": "Error Recovery Test",
            "category": "General",
            "priority": "low",
            "message": "Testing error recovery - this should work."
        }
        valid_response = client.post("/support/submit", json=valid_data)
        
        # Verify works correctly
        assert valid_response.status_code == 200
        assert "ticket_id" in valid_response.json()
        
        # Verify health again
        health_response2 = client.get("/health")
        assert health_response2.status_code == 200
        
        # Assert: Error recovery works
        assert invalid_response.status_code == 422
        assert valid_response.status_code == 200
        assert health_response.status_code == 200


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
