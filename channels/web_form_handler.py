"""
Web Form Handler for TechCorp Customer Success AI Agent.

Provides FastAPI endpoints for website support form integration.
This is a REAL implementation (not simulation).
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator

from channels.base_channel import BaseChannel


# ============================================================================
# Pydantic Models
# ============================================================================

class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SupportCategory(str, Enum):
    GENERAL = "General"
    TECHNICAL = "Technical"
    BILLING = "Billing"
    BUG_REPORT = "Bug Report"
    FEEDBACK = "Feedback"
    ACCOUNT = "Account"
    API = "API"


class SupportFormSubmission(BaseModel):
    """Web form submission model."""
    name: str = Field(..., min_length=2, max_length=100, description="Customer name")
    email: EmailStr = Field(..., description="Customer email address")
    subject: str = Field(..., min_length=5, max_length=200, description="Subject line")
    category: SupportCategory = Field(..., description="Support category")
    priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM, description="Priority level")
    message: str = Field(..., min_length=10, max_length=5000, description="Message content")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v):
        if not v.strip():
            raise ValueError('Subject cannot be empty')
        return v.strip()
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()


class SupportFormResponse(BaseModel):
    """Web form submission response model."""
    ticket_id: str
    message: str
    estimated_response_time: str
    status: str = "submitted"


class TicketStatusResponse(BaseModel):
    """Ticket status response model."""
    ticket_id: str
    status: str
    subject: str
    category: str
    priority: str
    created_at: str
    updated_at: str
    messages: List[Dict[str, Any]]


class CategoryInfo(BaseModel):
    """Category information model."""
    value: str
    label: str
    description: str


# ============================================================================
# Web Form Handler Class
# ============================================================================

class WebFormHandler(BaseChannel):
    """
    Handler for Web Form channel integration.
    
    Features:
    - FastAPI router with support endpoints
    - Form validation with Pydantic models
    - Database integration for ticket storage
    - Format responses for web form context
    
    Usage:
        handler = WebFormHandler()
        router = handler.get_router()
        # Include router in your FastAPI app
        # app.include_router(router, prefix="/api")
    """
    
    channel_name = "web_form"
    
    # Valid categories with descriptions
    CATEGORIES = [
        CategoryInfo(value="General", label="General Inquiry", description="General questions about our products"),
        CategoryInfo(value="Technical", label="Technical Support", description="Technical issues and troubleshooting"),
        CategoryInfo(value="Billing", label="Billing & Payments", description="Billing questions and payment issues"),
        CategoryInfo(value="Bug Report", label="Bug Report", description="Report a bug or issue"),
        CategoryInfo(value="Feedback", label="Feedback", description="Share your feedback or suggestions"),
        CategoryInfo(value="Account", label="Account Issues", description="Account access and settings"),
        CategoryInfo(value="API", label="API Support", description="API documentation and integration help"),
    ]
    
    # Response time estimates by priority
    RESPONSE_TIMES = {
        "low": "24-48 hours",
        "medium": "12-24 hours",
        "high": "2-4 hours"
    }
    
    def __init__(self, db_connection=None):
        """
        Initialize Web Form handler.
        
        Args:
            db_connection: Optional database connection for ticket storage.
        """
        self.db_connection = db_connection
        self.router = self._create_router()
    
    def _create_router(self) -> APIRouter:
        """Create FastAPI router with support endpoints."""
        router = APIRouter(prefix="/support", tags=["support"])
        
        @router.post("/submit", response_model=SupportFormResponse)
        async def submit_form(submission: SupportFormSubmission):
            """Submit a support form."""
            return await self.handle_submission(submission)
        
        @router.get("/ticket/{ticket_id}", response_model=TicketStatusResponse)
        async def get_ticket(ticket_id: str):
            """Get ticket status by ID."""
            return await self.get_ticket_status(ticket_id)
        
        @router.get("/categories", response_model=List[CategoryInfo])
        async def get_categories():
            """Get list of valid support categories."""
            return self.CATEGORIES
        
        return router
    
    def get_router(self) -> APIRouter:
        """
        Get the FastAPI router for this handler.
        
        Returns:
            FastAPI APIRouter with support endpoints.
        """
        return self.router
    
    def normalize_message(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize web form submission to standard format.
        
        Args:
            raw_message: Raw form submission data.
            
        Returns:
            Normalized message dictionary.
        """
        return {
            "channel": self.channel_name,
            "customer_email": raw_message.get('email'),
            "customer_phone": None,
            "customer_name": raw_message.get('name'),
            "subject": raw_message.get('subject'),
            "content": self._clean_text(raw_message.get('message', raw_message.get('body', ''))),
            "channel_message_id": raw_message.get('ticket_id', self._generate_message_id("WEB")),
            "received_at": raw_message.get('created_at', self._get_timestamp()),
            "metadata": {
                "category": raw_message.get('category'),
                "priority": raw_message.get('priority', 'medium'),
                "form_type": "support"
            }
        }
    
    def format_response(self, response_text: str, customer_data: Dict[str, Any]) -> str:
        """
        Format response for web form (semi-formal, structured).
        
        Args:
            response_text: Base response from agent.
            customer_data: Customer info including ticket_id.
            
        Returns:
            Formatted response (under 300 words).
        """
        name = customer_data.get('name') or customer_data.get('customer_name', '')
        ticket_id = customer_data.get('ticket_id')
        
        parts = []
        
        # Greeting
        if name:
            parts.append(f"Hello {name},")
        else:
            parts.append("Hello,")
        
        parts.append("")
        
        # Ticket reference if available
        if ticket_id:
            parts.append(f"Regarding your ticket #{ticket_id}:")
            parts.append("")
        
        # Response body (trim if too long)
        words = response_text.split()
        if len(words) > 300:
            response_text = ' '.join(words[:300]) + "..."
        
        parts.append(response_text)
        parts.append("")
        
        # Closing
        parts.append("If you have any further questions, please don't hesitate to reach out.")
        parts.append("")
        parts.append("Best regards,")
        parts.append("TechCorp Support Team")
        
        return '\n'.join(parts)
    
    def validate_incoming(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validate incoming form submission.
        
        Args:
            raw_data: Raw form data.
            
        Returns:
            True if valid.
        """
        # Required fields
        required = ['name', 'email', 'subject', 'message']
        for field in required:
            if not raw_data.get(field):
                return False
        
        # Email must be valid
        email = raw_data.get('email', '')
        if '@' not in email or '.' not in email.split('@')[-1]:
            return False
        
        # Message must have minimum length
        if len(raw_data.get('message', '')) < 10:
            return False
        
        return True
    
    async def handle_submission(self, submission: SupportFormSubmission) -> SupportFormResponse:
        """
        Handle a support form submission.

        Args:
            submission: Validated form submission.

        Returns:
            Response with ticket ID.
        """
        # Generate ticket ID
        ticket_id = self._generate_ticket_id()

        # Create normalized message
        normalized = {
            'name': submission.name,
            'email': submission.email,
            'subject': submission.subject,
            'category': submission.category.value,
            'priority': submission.priority.value,
            'message': submission.message,
            'ticket_id': ticket_id,
            'created_at': self._get_timestamp()
        }

        # Save to database
        await self._save_ticket_to_db(normalized)

        # Get estimated response time
        response_time = self.RESPONSE_TIMES.get(submission.priority.value, "24 hours")

        return SupportFormResponse(
            ticket_id=ticket_id,
            message="Thank you for contacting TechCorp Support. We've received your request.",
            estimated_response_time=response_time,
            status="submitted"
        )
    
    async def get_ticket_status(self, ticket_id: str) -> TicketStatusResponse:
        """
        Get ticket status by ID.

        Args:
            ticket_id: Ticket ID to look up.

        Returns:
            Ticket status information.

        Raises:
            HTTPException: If ticket not found.
        """
        ticket = await self._get_ticket_from_db(ticket_id)
        if ticket:
            return self._format_ticket_response(ticket)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    
    def process_submission(self, form_data: SupportFormSubmission) -> Dict[str, Any]:
        """
        Process form submission and return normalized format.
        
        Args:
            form_data: Validated form submission.
            
        Returns:
            Normalized message dictionary.
        """
        normalized = self.normalize_message({
            'name': form_data.name,
            'email': form_data.email,
            'subject': form_data.subject,
            'message': form_data.message,
            'category': form_data.category.value,
            'priority': form_data.priority.value
        })
        return normalized
    
    def _generate_ticket_id(self) -> str:
        """Generate a unique ticket ID."""
        import uuid
        return f"TKT-{uuid.uuid4().hex[:8].upper()}"

    async def _save_ticket_to_db(self, ticket_data: Dict[str, Any]) -> Optional[str]:
        """
        Save ticket to database.

        Args:
            ticket_data: Ticket data to save.
            
        Returns:
            The UUID of the created ticket, or None if failed.
        """
        from database.connection import get_db_connection
        from database.queries import create_customer, create_conversation
        
        conn = None
        try:
            async with get_db_connection() as conn:
                # Step 1: Get or create customer
                customer = await conn.fetchrow(
                    "SELECT id FROM customers WHERE email = $1",
                    ticket_data['email']
                )
                
                if not customer:
                    # Create new customer
                    customer_row = await conn.fetchrow(
                        """
                        INSERT INTO customers (email, name, metadata)
                        VALUES ($1, $2, $3)
                        RETURNING id
                        """,
                        ticket_data['email'],
                        ticket_data.get('name'),
                        json.dumps({"source": "web_form"})
                    )
                    customer_id = str(customer_row['id'])
                else:
                    customer_id = str(customer['id'])
                
                # Step 2: Create conversation
                conv_row = await conn.fetchrow(
                    """
                    INSERT INTO conversations (customer_id, initial_channel, current_channel, status, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                    """,
                    customer_id,
                    'web_form',
                    'web_form',
                    'active',
                    json.dumps({"ticket_id": ticket_data['ticket_id']})
                )
                conversation_id = str(conv_row['id'])
                
                # Step 3: Create ticket with custom ticket_id in metadata
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
                    'web_form',
                    ticket_data.get('category', 'General'),
                    ticket_data.get('priority', 'medium'),
                    'open',
                    ticket_data.get('subject', ''),
                    json.dumps({
                        "custom_ticket_id": ticket_data['ticket_id'],
                        "form_type": "support"
                    })
                )
                
                # Step 4: Store the incoming message
                await conn.execute(
                    """
                    INSERT INTO messages (
                        conversation_id, channel, direction, role, content, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    conversation_id,
                    'web_form',
                    'inbound',
                    'customer',
                    ticket_data.get('message', ''),
                    json.dumps({"source": "web_form"})
                )
                
                return str(ticket_row['id'])
                
        except Exception as e:
            logger.error(f"Error saving ticket to DB: {e}")
            return None

    async def _get_ticket_from_db(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Get ticket from database by custom ticket ID.

        Args:
            ticket_id: Custom ticket ID (e.g., TKT-19DED44D).
            
        Returns:
            Ticket data or None.
        """
        from database.connection import get_db_connection
        
        try:
            async with get_db_connection() as conn:
                # Search by custom_ticket_id in metadata
                row = await conn.fetchrow(
                    """
                    SELECT 
                        t.id as ticket_uuid,
                        t.status,
                        t.subject,
                        t.category,
                        t.priority,
                        t.created_at,
                        t.updated_at,
                        t.metadata->>'custom_ticket_id' as custom_ticket_id,
                        c.id as conversation_id,
                        cust.email as customer_email,
                        cust.name as customer_name
                    FROM tickets t
                    JOIN conversations c ON t.conversation_id = c.id
                    JOIN customers cust ON t.customer_id = cust.id
                    WHERE t.metadata->>'custom_ticket_id' = $1
                    """,
                    ticket_id
                )
                
                if not row:
                    return None
                
                # Get messages for this ticket
                messages = await conn.fetch(
                    """
                    SELECT role, content, channel, created_at
                    FROM messages
                    WHERE conversation_id = $1
                    ORDER BY created_at ASC
                    """,
                    row['conversation_id']
                )
                
                return {
                    'id': row['custom_ticket_id'],
                    'status': row['status'],
                    'subject': row['subject'] or '',
                    'category': row['category'] or 'General',
                    'priority': row['priority'] or 'medium',
                    'created_at': row['created_at'].isoformat() if row['created_at'] else '',
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else '',
                    'customer_email': row['customer_email'],
                    'customer_name': row['customer_name'],
                    'messages': [dict(m) for m in messages]
                }
                
        except Exception as e:
            logger.error(f"Error getting ticket from DB: {e}")
            return None

    def _format_ticket_response(self, ticket: Dict[str, Any]) -> TicketStatusResponse:
        """
        Format ticket data for API response.
        
        Args:
            ticket: Ticket data from database.
            
        Returns:
            Formatted ticket response.
        """
        return TicketStatusResponse(
            ticket_id=ticket.get('id', ''),
            status=ticket.get('status', 'open'),
            subject=ticket.get('subject', ''),
            category=ticket.get('category', 'General'),
            priority=ticket.get('priority', 'medium'),
            created_at=ticket.get('created_at', ''),
            updated_at=ticket.get('updated_at', ''),
            messages=ticket.get('messages', [])
        )


# ============================================================================
# FastAPI App Factory
# ============================================================================

def create_support_api() -> Any:
    """
    Create a FastAPI app with support endpoints.
    
    Returns:
        FastAPI application instance.
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(
        title="TechCorp Support API",
        description="API for TechCorp Customer Support web form",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Create handler and include router
    handler = WebFormHandler()
    app.include_router(handler.get_router())
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "techcorp-support-api"}
    
    return app


# Convenience function for quick access
def create_web_form_handler() -> WebFormHandler:
    """
    Create a Web Form handler instance.
    
    Returns:
        WebFormHandler instance.
    """
    return WebFormHandler()
