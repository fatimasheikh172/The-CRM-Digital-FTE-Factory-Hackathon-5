"""
TechCorp Customer Success AI Agent - Simulation Runner

Simulates real traffic by processing sample tickets through the agent.
Works in mock mode WITHOUT Gemini API key.
"""

import asyncio
import json
import sys
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path so imports work when running from workers/ folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.message_processor import UnifiedMessageProcessor
from workers.queue_manager import MessageQueue, KafkaTopics
from workers.metrics_collector import MetricsCollector


# ============================================================================
# SIMULATION RUNNER
# ============================================================================

class SimulationRunner:
    """
    Runs simulation of message processing through the agent.
    
    Loads sample tickets, processes them through the pipeline,
    and displays results.
    
    Usage:
        runner = SimulationRunner(mock_mode=True)
        await runner.run()
    """
    
    def __init__(self, mock_mode: bool = True):
        """
        Initialize simulation runner.
        
        Args:
            mock_mode: If True, use mock agent (no API key needed).
        """
        self.mock_mode = mock_mode
        self.processor = UnifiedMessageProcessor(mock_mode=mock_mode)
        self.queue = MessageQueue()
        self.metrics = MetricsCollector()
        
        # Results storage
        self.results: List[Dict] = []
        
        # Load sample tickets
        self.tickets = self._load_sample_tickets()
    
    def _load_sample_tickets(self) -> List[Dict]:
        """Load sample tickets from context file."""
        tickets_path = Path(__file__).parent.parent / "context" / "sample-tickets.json"
        
        try:
            with open(tickets_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return default tickets if file not found
            return self._get_default_tickets()
    
    def _get_default_tickets(self) -> List[Dict]:
        """Get default sample tickets."""
        return [
            {
                "id": 1,
                "channel": "email",
                "from": "john@example.com",
                "subject": "Cannot login",
                "message": "I have been trying to login since yesterday but it keeps saying wrong password. Reset email is not arriving.",
                "expected_action": "guide through password reset, check spam folder"
            },
            {
                "id": 2,
                "channel": "whatsapp",
                "from": "+1234567890",
                "message": "hi my app is not working",
                "expected_action": "ask for details, troubleshoot"
            },
            {
                "id": 3,
                "channel": "web_form",
                "from": "sara@business.com",
                "subject": "API rate limit issue",
                "message": "We are hitting rate limits. We need more than 1000 requests per hour.",
                "expected_action": "explain limits, suggest Enterprise plan"
            },
            {
                "id": 4,
                "channel": "email",
                "from": "angry@customer.com",
                "subject": "I WANT A REFUND",
                "message": "Your product has been broken for 3 days! I want my money back NOW!",
                "expected_action": "escalate immediately"
            },
            {
                "id": 5,
                "channel": "whatsapp",
                "from": "+9876543210",
                "message": "how much is pro plan",
                "expected_action": "provide pricing info"
            },
            {
                "id": 6,
                "channel": "web_form",
                "from": "dev@startup.com",
                "subject": "API Documentation",
                "message": "Where is the API documentation? I need to integrate your tool.",
                "expected_action": "provide docs link and API key instructions"
            },
            {
                "id": 7,
                "channel": "email",
                "from": "newuser@gmail.com",
                "subject": "Getting started",
                "message": "I just signed up. How do I invite my team members?",
                "expected_action": "provide getting started steps"
            },
            {
                "id": 8,
                "channel": "whatsapp",
                "from": "+1122334455",
                "message": "I want to talk to a human agent",
                "expected_action": "escalate to human immediately"
            }
        ]
    
    def _ticket_to_message(self, ticket: Dict) -> Dict:
        """
        Convert a ticket to a message format for processing.
        
        Args:
            ticket: Ticket dictionary.
        
        Returns:
            Message dictionary.
        """
        channel = ticket["channel"]
        from_field = ticket["from"]
        
        # Determine email vs phone
        customer_email = from_field if "@" in from_field else ""
        customer_phone = from_field if "@" not in from_field else ""
        
        return {
            "channel": channel,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
            "content": ticket["message"],
            "subject": ticket.get("subject"),
            "metadata": {
                "ticket_id": ticket["id"],
                "expected_action": ticket.get("expected_action", ""),
                "from": from_field
            }
        }
    
    async def run(self) -> Dict:
        """
        Run the simulation.
        
        Returns:
            Summary dictionary.
        """
        print("=" * 70)
        print("TechCorp Customer Success AI Agent - Simulation")
        print("=" * 70)
        print(f"\nMode: {'MOCK (no API key)' if self.mock_mode else 'LIVE (Gemini API)'}")
        print(f"Tickets to process: {len(self.tickets)}")
        print("\n" + "-" * 70)
        
        start_time = time.time()
        
        # Process each ticket
        for i, ticket in enumerate(self.tickets, 1):
            print(f"\n[Ticket {i}/{len(self.tickets)}] Channel: {ticket['channel'].upper()}")
            print(f"  From: {ticket['from']}")
            print(f"  Subject: {ticket.get('subject', 'N/A')}")
            print(f"  Message: {ticket['message'][:60]}...")
            print(f"  Expected: {ticket.get('expected_action', 'N/A')}")
            print()
            
            # Convert to message format
            message = self._ticket_to_message(ticket)
            
            # Process through agent
            result = await self.processor.process_message(
                KafkaTopics.TICKETS_INCOMING,
                message
            )
            
            # Store result
            result["ticket_id"] = ticket["id"]
            result["expected_action"] = ticket.get("expected_action", "")
            self.results.append(result)
            
            # Display result
            self._display_result(result)
        
        # Calculate summary
        total_time = time.time() - start_time
        summary = self._generate_summary(total_time)
        
        # Display summary
        self._display_summary(summary)
        
        return summary
    
    def _display_result(self, result: Dict) -> None:
        """Display processing result."""
        status_icon = "✓" if result["status"] == "success" else "✗"
        print(f"  {status_icon} Status: {result['status']}")
        print(f"  Customer ID: {result['customer_id'][:8] if result['customer_id'] else 'N/A'}...")
        print(f"  Conversation ID: {result['conversation_id'][:8] if result['conversation_id'] else 'N/A'}...")
        print(f"  Escalated: {result['escalated']}")
        print(f"  Latency: {result['latency_ms']}ms")
        
        if result.get("error"):
            print(f"  Error: {result['error']}")
    
    def _generate_summary(self, total_time: float) -> Dict:
        """
        Generate summary statistics.
        
        Args:
            total_time: Total processing time in seconds.
        
        Returns:
            Summary dictionary.
        """
        total = len(self.results)
        successful = sum(1 for r in self.results if r["status"] == "success")
        escalated = sum(1 for r in self.results if r.get("escalated", False))
        
        latencies = [r["latency_ms"] for r in self.results if r["latency_ms"] > 0]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # Channel breakdown
        channel_counts = {}
        for r in self.results:
            channel = r.get("channel", "unknown")
            channel_counts[channel] = channel_counts.get(channel, 0) + 1
        
        return {
            "total_processed": total,
            "successful": successful,
            "failed": total - successful,
            "escalated": escalated,
            "avg_latency_ms": round(avg_latency, 2),
            "total_time_seconds": round(total_time, 2),
            "messages_per_second": round(total / total_time, 2) if total_time > 0 else 0,
            "channel_breakdown": channel_counts
        }
    
    def _display_summary(self, summary: Dict) -> None:
        """Display summary statistics."""
        print("\n" + "=" * 70)
        print("SIMULATION SUMMARY")
        print("=" * 70)
        
        print(f"\n  Total Processed: {summary['total_processed']}")
        print(f"  Successful: {summary['successful']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Escalated: {summary['escalated']}")
        
        print(f"\n  Average Latency: {summary['avg_latency_ms']}ms")
        print(f"  Total Time: {summary['total_time_seconds']}s")
        print(f"  Throughput: {summary['messages_per_second']} msg/s")
        
        print(f"\n  Channel Breakdown:")
        for channel, count in summary["channel_breakdown"].items():
            print(f"    - {channel}: {count}")
        
        print("\n" + "=" * 70)


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

async def run_simulation(mock_mode: bool = True) -> Dict:
    """
    Run the simulation (convenience function).
    
    Args:
        mock_mode: Use mock agent (no API key).
    
    Returns:
        Summary dictionary.
    """
    runner = SimulationRunner(mock_mode=mock_mode)
    return await runner.run()


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run the simulation."""
    summary = await run_simulation(mock_mode=True)
    return summary


if __name__ == "__main__":
    asyncio.run(main())
