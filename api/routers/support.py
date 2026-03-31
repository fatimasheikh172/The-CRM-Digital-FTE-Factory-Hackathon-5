"""
Support Router for TechCorp Customer Success AI Agent.

Handles web form submissions and ticket lookups.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, EmailStr, Field

from channels.web_form_handler import (
    WebFormHandler,
    SupportFormSubmission,
    SupportFormResponse,
    TicketStatusResponse,
    CategoryInfo,
)
from kafka_client import FTEKafkaProducer, TOPICS
from production.config import AgentConfig
from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize handler
web_form_handler = WebFormHandler()


# ============================================================================
# CHAT API MODELS
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat API request model."""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    customer_name: str = Field(..., min_length=1, max_length=100, description="Customer name")
    customer_email: EmailStr = Field(..., description="Customer email")
    channel: str = Field(default="web_form", description="Channel type")
    conversation_history: List[ChatMessage] = Field(default=[], description="Previous messages")


class ChatResponse(BaseModel):
    """Chat API response model."""
    response: str = Field(..., description="AI response text")
    ticket_id: str = Field(..., description="Ticket ID")
    escalated: bool = Field(default=False, description="Whether escalated to human")
    escalation_reason: Optional[str] = Field(default=None, description="Reason for escalation")
    sentiment: str = Field(default="neutral", description="Message sentiment")
    suggested_actions: List[str] = Field(default=[], description="Suggested follow-up actions")


# ============================================================================
# WEB FORM ENDPOINTS
# ============================================================================

@router.post("/submit", response_model=SupportFormResponse, tags=["Support Form"])
async def submit_form(submission: SupportFormSubmission):
    """
    Submit a support form.

    Validates the form submission, saves to database, publishes to Kafka, and returns
    a ticket confirmation.

    Args:
        submission: Validated form submission with name, email, subject, etc.

    Returns:
        Ticket confirmation with ID and estimated response time.
    """
    try:
        # Generate ticket ID and save to database
        ticket_id = web_form_handler._generate_ticket_id()

        # Create normalized message for database and Kafka
        normalized = {
            "channel": "web_form",
            "customer_email": submission.email,
            "customer_name": submission.name,
            "subject": submission.subject,
            "content": submission.message,
            "metadata": {
                "category": submission.category.value,
                "priority": submission.priority.value,
                "ticket_id": ticket_id,
                "form_type": "support"
            }
        }

        # Save to database first
        await web_form_handler._save_ticket_to_db({
            'name': submission.name,
            'email': submission.email,
            'subject': submission.subject,
            'category': submission.category.value,
            'priority': submission.priority.value,
            'message': submission.message,
            'ticket_id': ticket_id,
        })

        # Publish to Kafka
        producer = FTEKafkaProducer()
        await producer.start()

        await producer.publish(TOPICS["tickets_incoming"], normalized)

        await producer.stop()

        # Get response time
        response_time = web_form_handler.RESPONSE_TIMES.get(
            submission.priority.value, "24 hours"
        )

        logger.info(f"Support form submitted: {ticket_id} from {submission.email}")

        return SupportFormResponse(
            ticket_id=ticket_id,
            message="Thank you for contacting TechCorp Support. We've received your request.",
            estimated_response_time=response_time,
            status="submitted"
        )

    except Exception as e:
        logger.error(f"Support form submission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting form: {str(e)}"
        )


@router.get("/ticket/{ticket_id}", response_model=TicketStatusResponse, tags=["Support Form"])
async def get_ticket(ticket_id: str):
    """
    Get ticket status by ID.

    Looks up ticket in database and returns status with messages.

    Args:
        ticket_id: Ticket ID to look up (e.g., TKT-19DED44D).

    Returns:
        Ticket status information with messages.

    Raises:
        HTTPException: If ticket not found.
    """
    try:
        # Get ticket from database using handler
        ticket = await web_form_handler.get_ticket_status(ticket_id)
        return ticket

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get ticket error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving ticket: {str(e)}"
        )


@router.get("/categories", response_model=List[CategoryInfo], tags=["Support Form"])
async def get_categories():
    """
    Get list of valid support categories.
    
    Returns all available categories for the support form.
    
    Returns:
        List of category information objects.
    """
    return web_form_handler.CATEGORIES


@router.get("/form", response_class=HTMLResponse, tags=["Support Form"])
async def get_support_form():
    """
    Serve the web support form HTML page.
    
    Returns static HTML with React form for customer submissions.
    
    Returns:
        HTML page with support form.
    """
    try:
        return FileResponse("api/static/index.html")
    except FileNotFoundError:
        # Return simple HTML form if file not found
        return HTMLResponse(content=get_simple_form_html())


# ============================================================================
# CHAT ENDPOINT
# ============================================================================

@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(request: ChatRequest):
    """
    Real-time AI chat for website users.
    
    Processes customer messages through Gemini AI and returns structured responses.
    Creates tickets automatically and handles escalation detection.
    
    Args:
        request: Chat request with message, customer info, and conversation history.
    
    Returns:
        Chat response with AI answer, ticket ID, escalation status, and sentiment.
    """
    try:
        # Generate ticket ID for this conversation
        ticket_id = web_form_handler._generate_ticket_id()
        
        # Build the prompt for Gemini
        system_prompt = CUSTOMER_SUCCESS_SYSTEM_PROMPT
        
        # Build conversation context
        conversation_context = ""
        if request.conversation_history:
            conversation_context = "\n\nConversation History:\n"
            for msg in request.conversation_history[-5:]:  # Last 5 messages
                role = "Customer" if msg.role == "user" else "Assistant"
                conversation_context += f"{role}: {msg.content}\n"
        
        # Build full prompt
        full_prompt = f"""{system_prompt}

Current Conversation:
Channel: {request.channel}
Customer: {request.customer_name} <{request.customer_email}>
Ticket ID: {ticket_id}
{conversation_context}
Customer Message: {request.message}

Please provide a helpful response following the system instructions. Format your response clearly and concisely for web form channel (max 300 words)."""

        # Call Gemini AI
        ai_response = ""
        escalated = False
        escalation_reason = None
        sentiment = "neutral"
        
        if AgentConfig.GEMINI_API_KEY:
            # Use real Gemini API
            try:
                from google import genai
                
                client = genai.Client(api_key=AgentConfig.GEMINI_API_KEY)
                
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model="gemini-1.5-flash",
                    contents=full_prompt
                )
                
                ai_response = response.text if hasattr(response, 'text') else str(response)
                logger.info("Gemini AI response received successfully")
            except Exception as api_error:
                logger.warning(f"Gemini API error, falling back to mock response: {api_error}")
                ai_response = _generate_mock_response(request.message, ticket_id)
        else:
            # Mock mode - generate simulated response
            ai_response = _generate_mock_response(request.message, ticket_id)
        
        # Check for escalation keywords
        message_lower = request.message.lower()
        escalation_keywords = ['lawyer', 'legal', 'sue', 'refund', 'money back', 'human agent', 'speak to human', 'real person']
        
        for keyword in escalation_keywords:
            if keyword in message_lower:
                escalated = True
                escalation_reason = f"escalation_keyword_detected:{keyword}"
                break
        
        # Determine sentiment based on message content
        sentiment = _analyze_sentiment(request.message)
        
        # Generate suggested actions
        suggested_actions = []
        if escalated:
            suggested_actions.append("Escalate to human agent")
            suggested_actions.append("Priority review required")
        else:
            suggested_actions.append("Close ticket")
            if "?" in request.message:
                suggested_actions.append("Ask follow-up")
        
        # Save conversation to database
        try:
            await _save_chat_to_db(
                ticket_id=ticket_id,
                customer_name=request.customer_name,
                customer_email=request.customer_email,
                message=request.message,
                response=ai_response,
                channel=request.channel,
                escalated=escalated
            )
        except Exception as db_error:
            logger.warning(f"Failed to save chat to database: {db_error}")
            # Continue anyway - don't fail the response
        
        logger.info(f"Chat processed: {ticket_id} from {request.customer_email}")
        
        return ChatResponse(
            response=ai_response,
            ticket_id=ticket_id,
            escalated=escalated,
            escalation_reason=escalation_reason,
            sentiment=sentiment,
            suggested_actions=suggested_actions
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat: {str(e)}"
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _generate_mock_response(message: str, ticket_id: str) -> str:
    """Generate a mock response when API key is not available."""
    message_lower = message.lower()
    
    if "password" in message_lower and "reset" in message_lower:
        return """To reset your password:

1. Go to the login page
2. Click "Forgot Password"
3. Enter your email address
4. Check your email for the reset link
5. Click the link and create a new password

The reset link expires in 24 hours. If you don't receive the email, check your spam folder.

Need further assistance? Reply to this message."""
    
    elif "refund" in message_lower:
        return """I understand you're requesting a refund. Let me help you with this.

Our refund policy allows for:
- Full refund within 30 days of purchase
- Pro-rated refund after 30 days
- No refund for downloadable products after access

To process your refund, I need to escalate this to our billing team. They will contact you within 24 hours.

Is there anything else I can help you with today?"""
    
    elif "api" in message_lower and ("rate" in message_lower or "limit" in message_lower):
        return """Our API rate limits are:

- Free tier: 100 requests/hour
- Basic plan: 1,000 requests/hour
- Pro plan: 10,000 requests/hour
- Enterprise: Custom limits

If you exceed your limit, you'll receive a 429 error. Wait until the next hour window or upgrade your plan.

Need help with API integration? Check our docs at docs.techcorp.com"""
    
    else:
        return f"""Thank you for contacting TechCorp Support.

I've received your message: "{message[:100]}..."

Your ticket ID is {ticket_id}. Our team will review your inquiry and respond within 24 hours.

For urgent matters, please call our support line at 1-800-TECHCORP.

Best regards,
TechCorp Support Team"""


def _analyze_sentiment(message: str) -> str:
    """Simple sentiment analysis based on keywords."""
    message_lower = message.lower()
    
    positive_words = ['great', 'excellent', 'amazing', 'love', 'thank', 'happy', 'pleased', 'awesome']
    negative_words = ['terrible', 'awful', 'hate', 'angry', 'frustrated', 'disappointed', 'worst', 'useless']
    urgent_words = ['urgent', 'asap', 'immediately', 'emergency', 'right now']
    
    pos_count = sum(1 for word in positive_words if word in message_lower)
    neg_count = sum(1 for word in negative_words if word in message_lower)
    urg_count = sum(1 for word in urgent_words if word in message_lower)
    
    if neg_count > 0 or urg_count > 1:
        return "negative"
    elif pos_count > 0:
        return "positive"
    else:
        return "neutral"


async def _save_chat_to_db(
    ticket_id: str,
    customer_name: str,
    customer_email: str,
    message: str,
    response: str,
    channel: str,
    escalated: bool
) -> Optional[str]:
    """Save chat conversation to database."""
    from database.connection import get_db_connection
    import json
    
    conn = None
    try:
        async with get_db_connection() as conn:
            # Get or create customer
            customer = await conn.fetchrow(
                "SELECT id FROM customers WHERE email = $1",
                customer_email
            )
            
            if not customer:
                customer_row = await conn.fetchrow(
                    """
                    INSERT INTO customers (email, name, metadata)
                    VALUES ($1, $2, $3)
                    RETURNING id
                    """,
                    customer_email,
                    customer_name,
                    json.dumps({"source": "chat"})
                )
                customer_id = str(customer_row['id'])
            else:
                customer_id = str(customer['id'])
            
            # Create conversation
            conv_row = await conn.fetchrow(
                """
                INSERT INTO conversations (customer_id, initial_channel, current_channel, status, metadata)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                customer_id,
                channel,
                channel,
                'active' if not escalated else 'escalated',
                json.dumps({"ticket_id": ticket_id})
            )
            conversation_id = str(conv_row['id'])
            
            # Create ticket
            ticket_row = await conn.fetchrow(
                """
                INSERT INTO tickets (
                    conversation_id, customer_id, source_channel, category,
                    priority, status, subject, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                """,
                conversation_id,
                customer_id,
                channel,
                'General',
                'high' if escalated else 'medium',
                'escalated' if escalated else 'open',
                message[:100],
                json.dumps({
                    "custom_ticket_id": ticket_id,
                    "form_type": "chat",
                    "escalated": escalated
                })
            )
            
            # Store customer message
            await conn.execute(
                """
                INSERT INTO messages (
                    conversation_id, channel, direction, role, content, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                conversation_id,
                channel,
                'inbound',
                'customer',
                message,
                json.dumps({"source": "chat"})
            )
            
            # Store AI response
            await conn.execute(
                """
                INSERT INTO messages (
                    conversation_id, channel, direction, role, content, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                conversation_id,
                channel,
                'outbound',
                'assistant',
                response,
                json.dumps({"source": "gemini_ai"})
            )
            
            return str(ticket_row['id'])
            
    except Exception as e:
        logger.error(f"Error saving chat to DB: {e}")
        return None


# ============================================================================
# SIMPLE HTML FORM (fallback)
# ============================================================================

def get_simple_form_html() -> str:
    """Return a simple HTML form for testing."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TechCorp Support Form</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 4px; margin-bottom: 15px; }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 4px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <h1>Contact TechCorp Support</h1>
    <div id="message"></div>
    <form id="supportForm">
        <div class="form-group">
            <label for="name">Name *</label>
            <input type="text" id="name" name="name" required minlength="2" maxlength="100">
        </div>
        <div class="form-group">
            <label for="email">Email *</label>
            <input type="email" id="email" name="email" required>
        </div>
        <div class="form-group">
            <label for="subject">Subject *</label>
            <input type="text" id="subject" name="subject" required minlength="5" maxlength="200">
        </div>
        <div class="form-group">
            <label for="category">Category</label>
            <select id="category" name="category">
                <option value="General">General Inquiry</option>
                <option value="Technical">Technical Support</option>
                <option value="Billing">Billing & Payments</option>
                <option value="Bug Report">Bug Report</option>
                <option value="Feedback">Feedback</option>
                <option value="Account">Account Issues</option>
                <option value="API">API Support</option>
            </select>
        </div>
        <div class="form-group">
            <label for="priority">Priority</label>
            <select id="priority" name="priority">
                <option value="low">Low</option>
                <option value="medium" selected>Medium</option>
                <option value="high">High</option>
            </select>
        </div>
        <div class="form-group">
            <label for="message">Message *</label>
            <textarea id="message" name="message" rows="5" required minlength="10" maxlength="5000"></textarea>
        </div>
        <button type="submit">Submit Request</button>
    </form>
    <script>
        document.getElementById('supportForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const data = {
                name: form.name.value,
                email: form.email.value,
                subject: form.subject.value,
                category: form.category.value,
                priority: form.priority.value,
                message: form.message.value
            };
            try {
                const response = await fetch('/support/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                if (response.ok) {
                    document.getElementById('message').innerHTML = 
                        '<div class="success">Ticket submitted! ID: ' + result.ticket_id + 
                        '<br>Estimated response: ' + result.estimated_response_time + '</div>';
                    form.reset();
                } else {
                    document.getElementById('message').innerHTML = 
                        '<div class="error">Error: ' + result.detail + '</div>';
                }
            } catch (error) {
                document.getElementById('message').innerHTML = 
                    '<div class="error">Submission failed: ' + error.message + '</div>';
            }
        });
    </script>
</body>
</html>
"""
