"""
TechCorp Customer Success AI Agent - Email Load Scenario

Simulates email webhook traffic.
"""

from locust import HttpUser, task, between, events
import random
import time


EMAIL_SUBJECTS = [
    "Need help with login",
    "Question about billing",
    "API integration issue",
    "Feature request",
    "Bug report",
    "Account access problem",
    "Password reset not working",
    "How to use your product?",
    "Technical support needed",
    "Refund request"
]

EMAIL_BODIES = [
    "Hi, I cannot login to my account. Can you help?",
    "I have a question about my recent invoice.",
    "The API is returning 500 errors.",
    "Would love to see a dark mode feature.",
    "Found a bug in the mobile app.",
    "I'm locked out of my account.",
    "Password reset email not arriving.",
    "Where can I find the documentation?",
    "Need technical assistance urgently.",
    "I'd like to request a refund please."
]


class EmailUser(HttpUser):
    """
    Simulates a user sending email support requests.
    
    Weight: 2 (second most common traffic pattern)
    Wait time: 5-15 seconds between actions
    """
    weight = 2
    wait_time = between(5, 15)
    
    # Track submitted tickets
    submitted_tickets = []
    
    @task(3)
    def send_email_ticket(self):
        """
        Send an email via the Gmail webhook.
        
        Uses random subject and body from predefined lists.
        Verifies 200 response.
        """
        email_data = {
            "from_email": f"email{random.randint(1000, 9999)}@test.com",
            "subject": random.choice(EMAIL_SUBJECTS),
            "body": random.choice(EMAIL_BODIES)
        }
        
        start_time = time.time()
        
        with self.client.post("/webhooks/gmail/test", json=email_data, catch_response=True) as response:
            elapsed = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                response.success()
                try:
                    data = response.json()
                    if "ticket_id" in data:
                        self.submitted_tickets.append(data["ticket_id"])
                except:
                    pass
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def check_metrics(self):
        """
        Check channel metrics.
        """
        with self.client.get("/metrics/channels", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
