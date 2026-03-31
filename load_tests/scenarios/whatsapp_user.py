"""
TechCorp Customer Success AI Agent - WhatsApp Load Scenario

Simulates WhatsApp message traffic.
"""

from locust import HttpUser, task, between, events
import random
import time


WHATSAPP_MESSAGES = [
    "hi need help",
    "my app not working",
    "how much is pro plan",
    "I want to talk to human",
    "login issue",
    "billing question",
    "bug report",
    "feature request",
    "password reset",
    "account locked"
]


class WhatsAppUser(HttpUser):
    """
    Simulates a user sending WhatsApp messages.
    
    Weight: 2 (second most common traffic pattern)
    Wait time: 3-10 seconds between actions
    """
    weight = 2
    wait_time = between(3, 10)
    
    # Track submitted tickets
    submitted_tickets = []
    
    @task(3)
    def send_whatsapp_message(self):
        """
        Send a WhatsApp message via the webhook.
        
        Uses random phone number and message.
        Verifies 200 response.
        """
        whatsapp_data = {
            "from_phone": f"+1{random.randint(2000000000, 2999999999)}",
            "body": random.choice(WHATSAPP_MESSAGES)
        }
        
        start_time = time.time()
        
        with self.client.post("/webhooks/whatsapp/test", json=whatsapp_data, catch_response=True) as response:
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
    
    @task(2)
    def send_human_request(self):
        """
        Send a request for human agent.
        
        This should trigger escalation.
        """
        whatsapp_data = {
            "from_phone": f"+1{random.randint(2000000000, 2999999999)}",
            "body": "I need to talk to a human agent please"
        }
        
        with self.client.post("/webhooks/whatsapp/test", json=whatsapp_data, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def check_health(self):
        """
        Check API health.
        """
        self.client.get("/health")
