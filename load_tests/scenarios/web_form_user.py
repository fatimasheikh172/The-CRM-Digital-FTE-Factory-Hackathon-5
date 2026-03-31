"""
TechCorp Customer Success AI Agent - Web Form Load Scenario

Simulates web form submission traffic.
"""

from locust import HttpUser, task, between, events
import random
import time


CATEGORIES = ['General', 'Technical', 'Billing', 'Bug Report', 'Feedback', 'Account', 'API']
PRIORITIES = ['low', 'medium', 'high']

MESSAGES = [
    "I need help with my account login",
    "How do I reset my password?",
    "The API is not working correctly",
    "I have a billing question",
    "Your app crashes on mobile",
    "How do I invite team members?",
    "Where is the documentation?",
    "I need help with integration",
    "Can you explain the pricing plans?",
    "I'm experiencing slow performance",
    "How do I export my data?",
    "The search feature is broken",
    "I need assistance with setup",
    "Can I get a refund?",
    "How do I contact support?"
]


class WebFormUser(HttpUser):
    """
    Simulates a user submitting support forms.
    
    Weight: 3 (most common traffic pattern)
    Wait time: 2-8 seconds between actions
    """
    weight = 3
    wait_time = between(2, 8)
    
    # Track submitted tickets for follow-up
    submitted_tickets = []
    
    @task(5)
    def submit_support_form(self):
        """
        Submit a random support form.
        
        Uses random category and message from predefined lists.
        Verifies 200 response and tracks response time.
        """
        form_data = {
            "name": f"Load Test User {random.randint(1000, 9999)}",
            "email": f"loadtest{random.randint(1000, 9999)}@test.com",
            "subject": f"Load Test: {random.choice(MESSAGES)[:50]}",
            "category": random.choice(CATEGORIES),
            "priority": random.choice(PRIORITIES),
            "message": random.choice(MESSAGES)
        }
        
        start_time = time.time()
        
        with self.client.post("/support/submit", json=form_data, catch_response=True) as response:
            elapsed = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                response.success()
                # Track ticket for potential follow-up
                try:
                    data = response.json()
                    if "ticket_id" in data:
                        self.submitted_tickets.append(data["ticket_id"])
                        # Keep only last 10 tickets
                        if len(self.submitted_tickets) > 10:
                            self.submitted_tickets.pop(0)
                except:
                    pass
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def check_ticket_status(self):
        """
        Check status of a previously submitted ticket.
        
        Only runs if we have submitted tickets.
        """
        if not self.submitted_tickets:
            return
        
        ticket_id = random.choice(self.submitted_tickets)
        
        with self.client.get(f"/tickets/{ticket_id}", catch_response=True) as response:
            if response.status_code in [200, 404]:
                # 404 is acceptable in mock mode
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def check_health(self):
        """
        Check API health.
        """
        self.client.get("/health")
