"""
Customers Router for TechCorp Customer Success AI Agent.

Handles customer lookup and information retrieval:
- Lookup by email or phone
- Get customer details
- Get customer conversations
- Get customer tickets
"""

import json
import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, EmailStr

from database.queries import (
    find_customer_by_email,
    find_customer_by_phone,
    get_customer_history,
    get_customer_tickets,
)
from database.connection import get_db_connection
import asyncpg

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


def _parse_metadata(metadata) -> dict:
    """Parse metadata field which may be a JSON string or dict."""
    if metadata is None:
        return {}
    if isinstance(metadata, dict):
        return metadata
    if isinstance(metadata, str):
        try:
            return json.loads(metadata)
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CustomerInfo(BaseModel):
    """Basic customer information."""
    customer_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    created_at: Optional[str] = None


class CustomerDetail(CustomerInfo):
    """Detailed customer information with stats."""
    total_conversations: int = 0
    total_tickets: int = 0
    first_channel: Optional[str] = None
    last_contact: Optional[str] = None


class ConversationSummary(BaseModel):
    """Conversation summary."""
    conversation_id: str
    channel: str
    status: str
    started_at: str
    message_count: int = 0


class TicketSummary(BaseModel):
    """Ticket summary."""
    ticket_id: str
    subject: str
    status: str
    channel: str
    created_at: str


class CustomerLookupResponse(BaseModel):
    """Customer lookup response."""
    customer: CustomerDetail
    conversations: List[ConversationSummary] = []
    recent_tickets: List[TicketSummary] = []


# ============================================================================
# CUSTOMER ENDPOINTS
# ============================================================================

@router.get("/lookup", response_model=CustomerLookupResponse, tags=["Customers"])
async def lookup_customer(
    email: Optional[EmailStr] = Query(None),
    phone: Optional[str] = Query(None)
):
    """
    Find customer by email or phone.
    
    Returns customer details with conversation history and recent tickets.
    
    Args:
        email: Customer email address.
        phone: Customer phone number.
        
    Returns:
        Customer information with conversations and tickets.
        
    Raises:
        HTTPException: If customer not found.
    """
    if not email and not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or phone parameter is required"
        )
    
    try:
        async with get_db_connection() as conn:
            # Find customer
            customer = None
            
            if email:
                customer = await find_customer_by_email(email)
            
            if not customer and phone:
                customer = await find_customer_by_phone(phone)
            
            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Customer not found"
                )
            
            # Get customer stats
            conversations = await get_customer_history(str(customer["id"]))
            tickets = await get_customer_tickets(str(customer["id"]))
            
            # Parse metadata (may be JSON string from DB)
            metadata = _parse_metadata(customer.get("metadata"))
            
            # Format response
            customer_detail = CustomerDetail(
                customer_id=str(customer["id"]),
                email=customer.get("email"),
                phone=customer.get("phone"),
                name=customer.get("name"),
                created_at=customer["created_at"].isoformat() if customer.get("created_at") else None,
                total_conversations=len(conversations) if conversations else 0,
                total_tickets=len(tickets) if tickets else 0,
                first_channel=metadata.get("first_channel"),
                last_contact=None  # Would need additional query
            )
            
            # Format conversations
            conv_summaries = []
            if conversations:
                for conv in conversations[:10]:  # Limit to 10
                    conv_summaries.append(ConversationSummary(
                        conversation_id=str(conv["id"]),
                        channel=conv.get("initial_channel", "unknown"),
                        status=conv.get("status", "unknown"),
                        started_at=conv["started_at"].isoformat() if conv.get("started_at") else "",
                        message_count=conv.get("message_count", 0)
                    ))
            
            # Format tickets
            ticket_summaries = []
            if tickets:
                for ticket in tickets[:10]:  # Limit to 10
                    ticket_summaries.append(TicketSummary(
                        ticket_id=str(ticket["id"]),
                        subject=ticket.get("subject", ""),
                        status=ticket.get("status", "open"),
                        channel=ticket.get("source_channel", "unknown"),
                        created_at=ticket["created_at"].isoformat() if ticket.get("created_at") else ""
                    ))
            
            return CustomerLookupResponse(
                customer=customer_detail,
                conversations=conv_summaries,
                recent_tickets=ticket_summaries
            )
            
    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        logger.error(f"Database error looking up customer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )


@router.get("/{customer_id}", response_model=CustomerDetail, tags=["Customers"])
async def get_customer(customer_id: str):
    """
    Get customer details.
    
    Returns customer information with statistics.
    
    Args:
        customer_id: Customer UUID.
        
    Returns:
        Customer details with stats.
        
    Raises:
        HTTPException: If customer not found.
    """
    try:
        async with get_db_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, email, phone, name, created_at, metadata
                FROM customers
                WHERE id = $1
                """,
                customer_id
            )
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer {customer_id} not found"
                )
            
            # Get counts
            conv_count = await conn.fetchval(
                "SELECT COUNT(*) FROM conversations WHERE customer_id = $1",
                customer_id
            )
            
            ticket_count = await conn.fetchval(
                "SELECT COUNT(*) FROM tickets WHERE customer_id = $1",
                customer_id
            )
            
            # Parse metadata (may be JSON string from DB)
            metadata = _parse_metadata(row.get("metadata"))
            
            return CustomerDetail(
                customer_id=str(row["id"]),
                email=row.get("email"),
                phone=row.get("phone"),
                name=row.get("name"),
                created_at=row["created_at"].isoformat() if row.get("created_at") else None,
                total_conversations=conv_count or 0,
                total_tickets=ticket_count or 0,
                first_channel=metadata.get("first_channel"),
                last_contact=None
            )
            
    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        logger.error(f"Database error getting customer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )


@router.get("/{customer_id}/conversations", response_model=List[ConversationSummary], tags=["Customers"])
async def get_customer_conversations(customer_id: str):
    """
    Get all conversations for a customer.
    
    Returns list of conversations across all channels.
    
    Args:
        customer_id: Customer UUID.
        
    Returns:
        List of conversation summaries.
        
    Raises:
        HTTPException: If customer not found.
    """
    try:
        async with get_db_connection() as conn:
            # Verify customer exists
            exists = await conn.fetchval(
                "SELECT 1 FROM customers WHERE id = $1",
                customer_id
            )
            
            if not exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer {customer_id} not found"
                )
            
            # Get conversations
            rows = await conn.fetch(
                """
                SELECT id, initial_channel as channel, status, started_at
                FROM conversations
                WHERE customer_id = $1
                ORDER BY started_at DESC
                """,
                customer_id
            )
            
            return [
                ConversationSummary(
                    conversation_id=str(row["id"]),
                    channel=row["channel"],
                    status=row["status"],
                    started_at=row["started_at"].isoformat() if row["started_at"] else "",
                    message_count=0  # Would need additional query
                )
                for row in rows
            ]
            
    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        logger.error(f"Database error getting conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )


@router.get("/{customer_id}/tickets", response_model=List[TicketSummary], tags=["Customers"])
async def list_customer_tickets(customer_id: str, limit: int = Query(20, ge=1, le=100)):
    """
    Get all tickets for a customer.
    
    Returns list of tickets with status.
    
    Args:
        customer_id: Customer UUID.
        limit: Maximum tickets to return (1-100).
        
    Returns:
        List of ticket summaries.
        
    Raises:
        HTTPException: If customer not found.
    """
    try:
        async with get_db_connection() as conn:
            # Verify customer exists
            exists = await conn.fetchval(
                "SELECT 1 FROM customers WHERE id = $1",
                customer_id
            )
            
            if not exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer {customer_id} not found"
                )
            
            # Get tickets
            rows = await conn.fetch(
                """
                SELECT id, subject, status, source_channel as channel, created_at
                FROM tickets
                WHERE customer_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                customer_id,
                limit
            )
            
            return [
                TicketSummary(
                    ticket_id=str(row["id"]),
                    subject=row["subject"] or "",
                    status=row["status"],
                    channel=row["channel"],
                    created_at=row["created_at"].isoformat() if row["created_at"] else ""
                )
                for row in rows
            ]
            
    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        logger.error(f"Database error getting tickets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )
