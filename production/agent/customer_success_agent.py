"""
TechCorp Customer Success AI Agent - Main Agent Class

CustomerSuccessAgent class with Google Gemini integration and function calling.
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from google import genai

from production.config import AgentConfig
from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
from production.agent.tools import (
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    escalate_to_human,
    send_response,
    analyze_sentiment,
    get_ticket_status,
    get_gemini_function_declarations
)
from production.agent.formatters import format_response


# ============================================================================
# GEMINI CONFIGURATION
# ============================================================================

def configure_gemini():
    """Configure the Google Gemini API and return client."""
    if AgentConfig.GEMINI_API_KEY:
        return genai.Client(api_key=AgentConfig.GEMINI_API_KEY)
    else:
        # Warning but don't fail - allows testing without API key
        print("Warning: GEMINI_API_KEY not set. Agent will use mock mode.")
        return None


# ============================================================================
# TOOL MAPPING
# ============================================================================

TOOL_FUNCTIONS = {
    "search_knowledge_base": search_knowledge_base,
    "create_ticket": create_ticket,
    "get_customer_history": get_customer_history,
    "escalate_to_human": escalate_to_human,
    "send_response": send_response,
    "analyze_sentiment": analyze_sentiment,
    "get_ticket_status": get_ticket_status,
}


# ============================================================================
# CUSTOMER SUCCESS AGENT
# ============================================================================

class CustomerSuccessAgent:
    """
    Customer Success AI Agent powered by Google Gemini.
    
    Handles customer support queries across email, WhatsApp, and web form channels.
    Uses function calling to interact with database and send responses.
    
    Usage:
        agent = CustomerSuccessAgent()
        result = await agent.run(
            message="I can't login to my account",
            channel="email",
            customer_id="john@example.com"
        )
    """
    
    def __init__(self, mock_mode: bool = False):
        """
        Initialize the Customer Success Agent.
        
        Args:
            mock_mode: If True, use mock Gemini model for testing.
        """
        self.mock_mode = mock_mode or not AgentConfig.GEMINI_API_KEY
        
        if self.mock_mode:
            self.model = None
            self._mock_tool_calls = []
        else:
            configure_gemini()
            self.model = genai.GenerativeModel(
                model_name=AgentConfig.MODEL,
                system_instruction=CUSTOMER_SUCCESS_SYSTEM_PROMPT,
                tools=[{
                    "function_declarations": get_gemini_function_declarations()
                }]
            )
    
    async def run(
        self,
        message: str,
        channel: str,
        customer_id: str,
        customer_email: str = "",
        customer_phone: str = "",
        conversation_history: list = []
    ) -> Dict[str, Any]:
        """
        Process a customer message and generate response.
        
        Args:
            message: Customer message text.
            channel: Channel type (email, whatsapp, web_form).
            customer_id: Customer identifier (email or phone).
            customer_email: Customer email address.
            customer_phone: Customer phone number.
            conversation_history: List of previous messages.
        
        Returns:
            Result dictionary with:
            - output: Final response text
            - tool_calls: List of tools used
            - escalated: Whether ticket was escalated
            - escalation_reason: Reason for escalation if any
            - channel: Channel used
            - processing_time_ms: Processing time in milliseconds
        """
        start_time = time.time()
        tool_calls_log = []
        escalated = False
        escalation_reason = None
        
        try:
            if self.mock_mode:
                # Mock mode - simulate tool calls
                result = await self._run_mock(
                    message, channel, customer_id,
                    customer_email, customer_phone
                )
                tool_calls_log = result.get("tool_calls", [])
                escalated = result.get("escalated", False)
                escalation_reason = result.get("escalation_reason")
                output = result.get("output", "")
            else:
                # Real Gemini mode
                chat = self.model.start_chat(history=conversation_history)
                
                # Build the prompt with context
                prompt = self._build_prompt(
                    message, channel, customer_id,
                    customer_email, customer_phone
                )
                
                # Send message to Gemini
                response = await asyncio.to_thread(
                    chat.send_message,
                    prompt
                )
                
                # Handle function calls in loop
                output = await self._handle_function_calls(
                    response, tool_calls_log,
                    customer_id, customer_email, customer_phone, channel
                )
                
                # Check for escalation
                escalated = any(
                    tc.get("tool") == "escalate_to_human"
                    for tc in tool_calls_log
                )
                if escalated:
                    escalation_reason = "Customer requires human assistance"
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "output": output,
                "tool_calls": tool_calls_log,
                "escalated": escalated,
                "escalation_reason": escalation_reason,
                "channel": channel,
                "processing_time_ms": processing_time_ms
            }
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Return error response
            return {
                "output": f"Error processing request: {str(e)}",
                "tool_calls": tool_calls_log,
                "escalated": True,
                "escalation_reason": f"Error: {str(e)}",
                "channel": channel,
                "processing_time_ms": processing_time_ms
            }
    
    def _build_prompt(
        self,
        message: str,
        channel: str,
        customer_id: str,
        customer_email: str,
        customer_phone: str
    ) -> str:
        """
        Build the prompt for Gemini with context.
        
        Args:
            message: Customer message.
            channel: Channel type.
            customer_id: Customer identifier.
            customer_email: Customer email.
            customer_phone: Customer phone.
        
        Returns:
            Formatted prompt string.
        """
        recipient = customer_email or customer_phone or customer_id
        
        return f"""
Customer Message:
Channel: {channel}
Customer: {recipient}
Message: {message}

Please process this message following the required workflow:
1. Create a ticket
2. Get customer history
3. Analyze sentiment
4. Search knowledge base if needed
5. Escalate if triggers detected
6. Send response

Generate appropriate tool calls and final response.
"""
    
    async def _handle_function_calls(
        self,
        response,
        tool_calls_log: List[Dict],
        customer_id: str,
        customer_email: str,
        customer_phone: str,
        channel: str
    ) -> str:
        """
        Handle Gemini function calls in a loop.
        
        Args:
            response: Initial Gemini response.
            tool_calls_log: List to log tool calls.
            customer_id: Customer identifier.
            customer_email: Customer email.
            customer_phone: Customer phone.
            channel: Channel type.
        
        Returns:
            Final response text.
        """
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Check for function calls in response
            if not hasattr(response, 'candidates') or not response.candidates:
                return response.text if hasattr(response, 'text') else str(response)
            
            candidate = response.candidates[0]
            
            if not hasattr(candidate, 'content') or not candidate.content:
                return response.text if hasattr(response, 'text') else str(response)
            
            parts = candidate.content.parts if hasattr(candidate.content, 'parts') else []
            
            function_call_found = False
            
            for part in parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_call_found = True
                    func_name = part.function_call.name
                    func_args = dict(part.function_call.args)
                    
                    # Log the tool call
                    tool_calls_log.append({
                        "tool": func_name,
                        "arguments": func_args
                    })
                    
                    # Execute the tool function
                    if func_name in TOOL_FUNCTIONS:
                        try:
                            result = await TOOL_FUNCTIONS[func_name](**func_args)
                            
                            # Send result back to Gemini
                            response = await asyncio.to_thread(
                                response.model.start_chat().send_message,
                                f"Function {func_name} returned: {result}"
                            )
                        except Exception as e:
                            response = await asyncio.to_thread(
                                response.model.start_chat().send_message,
                                f"Function {func_name} error: {str(e)}"
                            )
                        break
            
            if not function_call_found:
                # No more function calls, return final text
                return response.text if hasattr(response, 'text') else str(response)
        
        return "Maximum iterations reached"
    
    async def _run_mock(
        self,
        message: str,
        channel: str,
        customer_id: str,
        customer_email: str,
        customer_phone: str
    ) -> Dict[str, Any]:
        """
        Run agent in mock mode (no API key required).
        
        Simulates the tool call sequence for testing.
        
        Args:
            message: Customer message.
            channel: Channel type.
            customer_id: Customer identifier.
            customer_email: Customer email.
            customer_phone: Customer phone.
        
        Returns:
            Mock result dictionary.
        """
        tool_calls_log = []
        escalated = False
        escalation_reason = None
        
        # Simulate tool call sequence
        recipient = customer_email or customer_phone or customer_id
        
        # 1. Create ticket
        ticket_result = await create_ticket(
            customer_id=customer_id,
            issue=message,
            channel=channel
        )
        tool_calls_log.append({"tool": "create_ticket", "result": ticket_result[:100]})
        
        # Extract ticket ID from result
        ticket_id = "TKT-MOCK-1234"
        for line in ticket_result.split('\n'):
            if 'Ticket ID:' in line:
                ticket_id = line.split(':')[1].strip()
                break
        
        # 2. Get customer history
        history_result = await get_customer_history(customer_id=customer_id)
        tool_calls_log.append({"tool": "get_customer_history", "result": history_result[:100]})
        
        # 3. Analyze sentiment
        sentiment_result = await analyze_sentiment(message=message)
        tool_calls_log.append({"tool": "analyze_sentiment", "result": sentiment_result[:100]})
        
        # Check for escalation triggers
        score = 0.5
        for line in sentiment_result.split('\n'):
            if 'Score:' in line:
                try:
                    score = float(line.split(':')[1].strip().split()[0])
                except:
                    pass
        
        # Check message for escalation keywords
        message_lower = message.lower()
        escalation_keywords = ['lawyer', 'legal', 'sue', 'refund', 'money back', 'human agent']
        
        if score < 0.3 or any(kw in message_lower for kw in escalation_keywords):
            # 4. Escalate
            escalation_result = await escalate_to_human(
                ticket_id=ticket_id,
                reason="Customer requires human assistance",
                customer_id=customer_id
            )
            tool_calls_log.append({"tool": "escalate_to_human", "result": escalation_result[:100]})
            escalated = True
            escalation_reason = "Negative sentiment or escalation keywords detected"
            
            # 5. Send escalation response
            response_text = self._get_escalation_response(channel)
        else:
            # 4. Search knowledge base
            kb_result = await search_knowledge_base(query=message)
            tool_calls_log.append({"tool": "search_knowledge_base", "result": kb_result[:100]})
            
            # 5. Generate response
            response_text = self._generate_mock_response(message, channel)
        
        # 6. Send response
        send_result = await send_response(
            ticket_id=ticket_id,
            message=response_text,
            channel=channel,
            customer_email=customer_email,
            customer_phone=customer_phone
        )
        tool_calls_log.append({"tool": "send_response", "result": send_result[:100]})
        
        return {
            "output": response_text,
            "tool_calls": tool_calls_log,
            "escalated": escalated,
            "escalation_reason": escalation_reason
        }
    
    def _get_escalation_response(self, channel: str) -> str:
        """
        Get escalation acknowledgment response.
        
        Args:
            channel: Channel type.
        
        Returns:
            Escalation response text.
        """
        if channel == "whatsapp":
            return "I understand your concern. Let me connect you with a human agent who can better assist you.\n\nReply 'human' for live support"
        elif channel == "email":
            return """Dear Valued Customer,

Thank you for bringing this to our attention. Your message has been escalated to our specialist team. A team member will contact you within 24 hours.

Best regards,
TechCorp Support Team"""
        else:
            return """Hello,

Your request has been escalated to our specialist team. We will contact you via email within 24 hours with a resolution.

Best regards,
TechCorp Support Team"""
    
    def _generate_mock_response(self, message: str, channel: str) -> str:
        """
        Generate a mock response for testing.
        
        Args:
            message: Customer message.
            channel: Channel type.
        
        Returns:
            Response text formatted for channel.
        """
        base_response = (
            "Thank you for contacting TechCorp Support. "
            "I've reviewed your message and I'm here to help. "
            "Based on our product documentation, here's what I recommend..."
        )
        
        return format_response(base_response, channel)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def process_message(
    message: str,
    channel: str,
    customer_id: str,
    customer_email: str = "",
    customer_phone: str = "",
    mock_mode: bool = True
) -> Dict[str, Any]:
    """
    Process a customer message using the agent.
    
    Convenience function for quick testing.
    
    Args:
        message: Customer message.
        channel: Channel type.
        customer_id: Customer identifier.
        customer_email: Customer email.
        customer_phone: Customer phone.
        mock_mode: Use mock mode (no API key).
    
    Returns:
        Result dictionary.
    """
    agent = CustomerSuccessAgent(mock_mode=mock_mode)
    return await agent.run(
        message=message,
        channel=channel,
        customer_id=customer_id,
        customer_email=customer_email,
        customer_phone=customer_phone
    )


def main():
    """Main function to demonstrate the agent."""
    print("=" * 60)
    print("TechCorp Customer Success AI Agent - Gemini Edition")
    print("=" * 60)
    print("\nRunning in mock mode (no API key required for testing)")
    print("\n" + "-" * 60)
    
    # Test cases
    test_cases = [
        {
            "message": "I can't login to my account. Password reset not working.",
            "channel": "email",
            "customer_id": "john@example.com",
            "customer_email": "john@example.com"
        },
        {
            "message": "App keeps crashing",
            "channel": "whatsapp",
            "customer_id": "+14155551234",
            "customer_phone": "+14155551234"
        },
        {
            "message": "I want to speak to a human agent NOW!",
            "channel": "email",
            "customer_id": "angry@example.com",
            "customer_email": "angry@example.com"
        }
    ]
    
    async def run_tests():
        for i, test in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test['channel'].upper()}")
            print(f"Message: {test['message']}")
            print(f"Customer: {test['customer_id']}")
            print()
            
            result = await process_message(
                message=test['message'],
                channel=test['channel'],
                customer_id=test['customer_id'],
                customer_email=test.get('customer_email', ''),
                customer_phone=test.get('customer_phone', ''),
                mock_mode=True
            )
            
            print(f"Output: {result['output'][:200]}...")
            print(f"Escalated: {result['escalated']}")
            print(f"Tool Calls: {len(result['tool_calls'])}")
            print(f"Processing Time: {result['processing_time_ms']}ms")
            print("-" * 60)
    
    asyncio.run(run_tests())


if __name__ == "__main__":
    main()
