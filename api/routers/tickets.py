"""
Tickets Router for TechCorp Customer Success AI Agent.

Handles ticket management operations:
- List tickets
- Get ticket details
- Update ticket status
- Get ticket messages
- Escalate tickets
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from database.queries import (
    get_ticket_by_id,
    create_ticket,
    update_ticket_status,
    get_customer_tickets,
    get_conversation_messages,
)
from database.connection import get_db_connection
import asyncpg

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TicketListItem(BaseModel):
    """Ticket list item model."""
    ticket_id: str
    customer_id: str
    subject: str
    status: str
    priority: str
    channel: str
    created_at: str
    updated_at: str


class TicketDetail(TicketListItem):
    """Ticket detail model with messages."""
    messages: List[Dict[str, Any]] = []
    conversation_id: str = None
    escalated: bool = False


class StatusUpdateRequest(BaseModel):
    """Ticket status update request."""
    status: str
    notes: str = None


class EscalationRequest(BaseModel):
    """Ticket escalation request."""
    reason: str
    urgency: str = "normal"


class EscalationResponse(BaseModel):
    """Escalation confirmation response."""
    status: str
    message: str
    escalation_id: str = None


# ============================================================================
# TICKET ENDPOINTS
# ============================================================================

@router.get("", response_model=List[TicketListItem], tags=["Tickets"])
async def list_tickets(
    status_filter: Optional[str] = Query(None, alias="status"),
    channel: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """
    List all tickets with optional filters.
    
    Args:
        status_filter: Filter by status (open, processing, resolved, escalated).
        channel: Filter by channel (email, whatsapp, web_form).
        priority: Filter by priority (low, medium, high).
        limit: Maximum number of tickets to return (1-100).
        
    Returns:
        List of tickets matching filters.
    """
    try:
        async with get_db_connection() as conn:
            # Build query
            query = """
                SELECT id, customer_id, subject, status, priority, 
                       source_channel as channel, created_at, updated_at
                FROM tickets
                WHERE 1=1
            """
            params = []
            
            if status_filter:
                query += " AND status = $" + str(len(params) + 1)
                params.append(status_filter)
            
            if channel:
                query += " AND source_channel = $" + str(len(params) + 1)
                params.append(channel)
            
            if priority:
                query += " AND priority = $" + str(len(params) + 1)
                params.append(priority)
            
            query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            
            return [
                TicketListItem(
                    ticket_id=str(row["id"]),
                    customer_id=str(row["customer_id"]),
                    subject=row["subject"] or "",
                    status=row["status"],
                    priority=row["priority"] or "medium",
                    channel=row["channel"],
                    created_at=row["created_at"].isoformat() if row["created_at"] else "",
                    updated_at=row["updated_at"].isoformat() if row["updated_at"] else ""
                )
                for row in rows
            ]
            
    except asyncpg.PostgresError as e:
        logger.error(f"Database error listing tickets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )


@router.get("/{ticket_id}", response_model=TicketDetail, tags=["Tickets"])
async def get_ticket(ticket_id: str):
    """
    Get single ticket details.
    
    Returns full ticket information including messages.
    
    Args:
        ticket_id: Ticket UUID.
        
    Returns:
        Ticket details with messages.
        
    Raises:
        HTTPException: If ticket not found.
    """
    try:
        async with get_db_connection() as conn:
            # Get ticket
            row = await conn.fetchrow(
                """
                SELECT id, customer_id, subject, status, priority,
                       source_channel as channel, conversation_id,
                       created_at, updated_at
                FROM tickets
                WHERE id = $1
                """,
                ticket_id
            )
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ticket {ticket_id} not found"
                )
            
            # Get messages
            messages = await get_conversation_messages(str(row["conversation_id"])) if row["conversation_id"] else []
            
            return TicketDetail(
                ticket_id=str(row["id"]),
                customer_id=str(row["customer_id"]),
                subject=row["subject"] or "",
                status=row["status"],
                priority=row["priority"] or "medium",
                channel=row["channel"],
                conversation_id=str(row["conversation_id"]) if row["conversation_id"] else None,
                escalated=False,
                created_at=row["created_at"].isoformat() if row["created_at"] else "",
                updated_at=row["updated_at"].isoformat() if row["updated_at"] else "",
                messages=messages or []
            )
            
    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        logger.error(f"Database error getting ticket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )


@router.patch("/{ticket_id}/status", response_model=TicketDetail, tags=["Tickets"])
async def update_ticket(ticket_id: str, update: StatusUpdateRequest):
    """
    Update ticket status.
    
    Args:
        ticket_id: Ticket UUID.
        update: Status update with optional notes.
        
    Returns:
        Updated ticket details.
        
    Raises:
        HTTPException: If ticket not found or invalid status.
    """
    valid_statuses = ["open", "processing", "resolved", "closed", "escalated"]
    
    if update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    try:
        async with get_db_connection() as conn:
            # Update ticket
            await conn.execute(
                """
                UPDATE tickets
                SET status = $1, updated_at = NOW()
                WHERE id = $2
                """,
                update.status,
                ticket_id
            )
            
            # Verify update
            row = await conn.fetchrow(
                """
                SELECT id, customer_id, subject, status, priority,
                       source_channel as channel, conversation_id,
                       created_at, updated_at
                FROM tickets
                WHERE id = $1
                """,
                ticket_id
            )
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ticket {ticket_id} not found"
                )
            
            # Get messages
            messages = []
            if row["conversation_id"]:
                messages = await get_conversation_messages(str(row["conversation_id"]))
            
            logger.info(f"Ticket {ticket_id} status updated to {update.status}")
            
            return TicketDetail(
                ticket_id=str(row["id"]),
                customer_id=str(row["customer_id"]),
                subject=row["subject"] or "",
                status=row["status"],
                priority=row["priority"] or "medium",
                channel=row["channel"],
                conversation_id=str(row["conversation_id"]) if row["conversation_id"] else None,
                escalated=False,
                created_at=row["created_at"].isoformat() if row["created_at"] else "",
                updated_at=row["updated_at"].isoformat() if row["updated_at"] else "",
                messages=messages or []
            )
            
    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        logger.error(f"Database error updating ticket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )


@router.get("/{ticket_id}/messages", response_model=List[Dict[str, Any]], tags=["Tickets"])
async def get_ticket_messages(ticket_id: str):
    """
    Get all messages for a ticket.
    
    Args:
        ticket_id: Ticket UUID.
        
    Returns:
        List of messages with channel info.
        
    Raises:
        HTTPException: If ticket not found.
    """
    try:
        async with get_db_connection() as conn:
            # Get conversation ID
            row = await conn.fetchrow(
                "SELECT conversation_id FROM tickets WHERE id = $1",
                ticket_id
            )
            
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ticket {ticket_id} not found"
                )
            
            if not row["conversation_id"]:
                return []
            
            # Get messages
            messages = await get_conversation_messages(str(row["conversation_id"]))
            
            return messages or []
            
    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        logger.error(f"Database error getting messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )


@router.post("/{ticket_id}/escalate", response_model=EscalationResponse, tags=["Tickets"])
async def escalate_ticket(ticket_id: str, escalation: EscalationRequest):
    """
    Manually escalate a ticket.
    
    Args:
        ticket_id: Ticket UUID.
        escalation: Escalation details with reason and urgency.
        
    Returns:
        Escalation confirmation.
        
    Raises:
        HTTPException: If ticket not found.
    """
    valid_urgencies = ["normal", "high", "critical"]
    
    if escalation.urgency not in valid_urgencies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid urgency. Must be one of: {valid_urgencies}"
        )
    
    try:
        async with get_db_connection() as conn:
            # Update ticket status
            await conn.execute(
                """
                UPDATE tickets
                SET status = 'escalated', escalated = TRUE, updated_at = NOW()
                WHERE id = $1
                """,
                ticket_id
            )
            
            # Create escalation record
            esc_id = await conn.fetchval(
                """
                INSERT INTO escalations (ticket_id, reason, urgency, status)
                VALUES ($1, $2, $3, 'pending')
                RETURNING id
                """,
                ticket_id,
                escalation.reason,
                escalation.urgency
            )
            
            logger.info(f"Ticket {ticket_id} escalated: {escalation.reason}")
            
            return EscalationResponse(
                status="escalated",
                message=f"Ticket {ticket_id} has been escalated",
                escalation_id=str(esc_id) if esc_id else None
            )
            
    except asyncpg.PostgresError as e:
        logger.error(f"Database error escalating ticket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )
