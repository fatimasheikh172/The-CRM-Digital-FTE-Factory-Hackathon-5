"""
TechCorp Customer Success AI Agent - Main Locust Configuration

Import all user types for load testing.
"""

from locust import HttpUser, task, between, events

# Import scenario user types
from load_tests.scenarios.web_form_user import WebFormUser
from load_tests.scenarios.email_user import EmailUser
from load_tests.scenarios.whatsapp_user import WhatsAppUser


class HealthCheckUser(HttpUser):
    """
    Simulates health check monitoring traffic.
    
    Weight: 1 (lowest priority traffic)
    Wait time: 10-30 seconds between checks
    """
    weight = 1
    wait_time = between(10, 30)
    
    @task
    def check_health(self):
        """Check API health endpoint."""
        self.client.get("/health")
    
    @task
    def check_summary_metrics(self):
        """Check summary metrics endpoint."""
        self.client.get("/metrics/summary")


# ============================================================================
# EVENT HANDLERS
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("=" * 60)
    print("TechCorp Customer Success FTE - Load Test Starting")
    print("=" * 60)
    print(f"Target: {environment.host}")
    print(f"Users: WebForm(3), Email(2), WhatsApp(2), Health(1)")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("")
    print("=" * 60)
    print("Load Test Complete")
    print("=" * 60)
    
    # Print statistics
    stats = environment.stats
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {(stats.total.num_failures / max(stats.total.num_requests, 1)) * 100:.2f}%")
    print(f"Avg Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Requests/sec: {stats.total.current_rps:.2f}")
    print("=" * 60)
