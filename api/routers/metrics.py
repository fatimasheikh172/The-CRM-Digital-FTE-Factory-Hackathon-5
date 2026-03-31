"""
Metrics Router for TechCorp Customer Success AI Agent.

Handles performance metrics retrieval:
- Channel performance
- Overall summary
- Sentiment trends
- Kafka topic stats
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from database.connection import get_db_connection
from kafka.admin import KafkaAdminClient
from kafka_client import TOPICS
from production.config import AgentConfig

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ChannelMetrics(BaseModel):
    """Metrics for a single channel."""
    total_conversations: int = 0
    avg_sentiment: float = 0.0
    escalation_rate: float = 0.0
    avg_latency_ms: float = 0.0
    total_messages: int = 0


class ChannelMetricsResponse(BaseModel):
    """Channel metrics response."""
    email: ChannelMetrics = ChannelMetrics()
    whatsapp: ChannelMetrics = ChannelMetrics()
    web_form: ChannelMetrics = ChannelMetrics()


class SummaryMetrics(BaseModel):
    """Overall system summary."""
    total_tickets_today: int = 0
    resolved_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    escalation_rate: float = 0.0
    busiest_channel: str = None


class SentimentDataPoint(BaseModel):
    """Sentiment data point for time series."""
    timestamp: str
    sentiment_score: float
    message_count: int


class SentimentResponse(BaseModel):
    """Sentiment trends response."""
    channel: str
    hours: int
    data: List[SentimentDataPoint] = []
    avg_sentiment: float = 0.0


class KafkaTopicStats(BaseModel):
    """Stats for a single Kafka topic."""
    topic: str
    exists: bool
    partitions: int = 0


class KafkaMetricsResponse(BaseModel):
    """Kafka metrics response."""
    connected: bool
    topics: List[KafkaTopicStats] = []
    total_topics: int = 0


# ============================================================================
# METRICS ENDPOINTS
# ============================================================================

@router.get("/channels", response_model=ChannelMetricsResponse, tags=["Metrics"])
async def get_channel_metrics(hours: int = Query(24, ge=1, le=720)):
    """
    Get performance metrics by channel for the last N hours.
    
    Args:
        hours: Time period in hours (1-720).
        
    Returns:
        Metrics for email, whatsapp, and web_form channels.
    """
    try:
        async with get_db_connection() as conn:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            result = ChannelMetricsResponse()
            
            for channel in ["email", "whatsapp", "web_form"]:
                # Get conversation count
                conv_count = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM conversations
                    WHERE initial_channel = $1 AND started_at > $2
                    """,
                    channel,
                    cutoff
                )
                
                # Get avg sentiment from conversations
                avg_sentiment = await conn.fetchval(
                    """
                    SELECT AVG(sentiment_score) FROM conversations
                    WHERE initial_channel = $1 AND started_at > $2
                      AND sentiment_score IS NOT NULL
                    """,
                    channel,
                    cutoff
                )
                
                # Get escalation rate
                escalated = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM tickets
                    WHERE source_channel = $1 AND created_at > $2 AND status = 'escalated'
                    """,
                    channel,
                    cutoff
                )
                
                total = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM tickets
                    WHERE source_channel = $1 AND created_at > $2
                    """,
                    channel,
                    cutoff
                )
                
                escalation_rate = (escalated / total) if total > 0 else 0.0
                
                # Get avg latency from agent_metrics table
                # Note: agent_metrics uses metric_value column, not latency_ms
                avg_latency = await conn.fetchval(
                    """
                    SELECT AVG(metric_value) FROM agent_metrics
                    WHERE metric_name = 'latency_ms' AND channel = $1 AND recorded_at > $2
                    """,
                    channel,
                    cutoff
                )
                
                # Get total messages
                msg_count = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    WHERE c.initial_channel = $1 AND c.started_at > $2
                    """,
                    channel,
                    cutoff
                )
                
                metrics = ChannelMetrics(
                    total_conversations=conv_count or 0,
                    avg_sentiment=round(avg_sentiment or 0.0, 3),
                    escalation_rate=round(escalation_rate, 3),
                    avg_latency_ms=round(avg_latency or 0.0, 2),
                    total_messages=msg_count or 0
                )
                
                if channel == "email":
                    result.email = metrics
                elif channel == "whatsapp":
                    result.whatsapp = metrics
                else:
                    result.web_form = metrics
            
            return result
            
    except Exception as e:
        logger.error(f"Error getting channel metrics: {e}")
        # Return empty metrics on error
        return ChannelMetricsResponse()


@router.get("/summary", response_model=SummaryMetrics, tags=["Metrics"])
async def get_summary_metrics():
    """
    Get overall system performance summary for today.
    
    Returns:
        Summary metrics including total tickets, resolution rate, etc.
    """
    try:
        async with get_db_connection() as conn:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Total tickets today
            total_today = await conn.fetchval(
                "SELECT COUNT(*) FROM tickets WHERE created_at > $1",
                today
            )
            
            # Resolved rate
            resolved = await conn.fetchval(
                "SELECT COUNT(*) FROM tickets WHERE status = 'resolved' AND created_at > $1",
                today
            )
            resolved_rate = (resolved / total_today) if total_today > 0 else 0.0
            
            # Avg response time from agent_metrics table
            # Note: agent_metrics uses metric_value column, not latency_ms
            avg_response = await conn.fetchval(
                """
                SELECT AVG(metric_value) FROM agent_metrics 
                WHERE metric_name = 'latency_ms' AND recorded_at > $1
                """,
                today
            )
            
            # Escalation rate
            escalated = await conn.fetchval(
                "SELECT COUNT(*) FROM tickets WHERE status = 'escalated' AND created_at > $1",
                today
            )
            escalation_rate = (escalated / total_today) if total_today > 0 else 0.0
            
            # Busiest channel
            busiest = await conn.fetchrow(
                """
                SELECT source_channel as channel, COUNT(*) as count
                FROM tickets
                WHERE created_at > $1
                GROUP BY source_channel
                ORDER BY count DESC
                LIMIT 1
                """,
                today
            )
            
            return SummaryMetrics(
                total_tickets_today=total_today or 0,
                resolved_rate=round(resolved_rate, 3),
                avg_response_time_ms=round(avg_response or 0.0, 2),
                escalation_rate=round(escalation_rate, 3),
                busiest_channel=busiest["channel"] if busiest else None
            )
            
    except Exception as e:
        logger.error(f"Error getting summary metrics: {e}")
        return SummaryMetrics()


@router.get("/sentiment", response_model=SentimentResponse, tags=["Metrics"])
async def get_sentiment_metrics(
    hours: int = Query(24, ge=1, le=168),
    channel: str = Query("all")
):
    """
    Get sentiment trends over time.
    
    Args:
        hours: Time period in hours (1-168).
        channel: Filter by channel or 'all'.
        
    Returns:
        Time-series sentiment data.
    """
    try:
        async with get_db_connection() as conn:
            cutoff = datetime.now() - timedelta(hours=hours)
            
            # Build query
            if channel == "all":
                rows = await conn.fetch(
                    """
                    SELECT DATE_TRUNC('hour', started_at) as hour,
                           AVG(sentiment_score) as avg_sentiment,
                           COUNT(*) as count
                    FROM conversations
                    WHERE started_at > $1 AND sentiment_score IS NOT NULL
                    GROUP BY hour
                    ORDER BY hour
                    """,
                    cutoff
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT DATE_TRUNC('hour', started_at) as hour,
                           AVG(sentiment_score) as avg_sentiment,
                           COUNT(*) as count
                    FROM conversations
                    WHERE started_at > $1 AND initial_channel = $2
                      AND sentiment_score IS NOT NULL
                    GROUP BY hour
                    ORDER BY hour
                    """,
                    cutoff,
                    channel
                )
            
            # Format data
            data_points = [
                SentimentDataPoint(
                    timestamp=row["hour"].isoformat() if row["hour"] else "",
                    sentiment_score=round(row["avg_sentiment"] or 0.0, 3),
                    message_count=row["count"] or 0
                )
                for row in rows
            ]
            
            # Calculate overall average
            overall_avg = sum(d.sentiment_score * d.message_count for d in data_points)
            total_count = sum(d.message_count for d in data_points)
            avg_sentiment = (overall_avg / total_count) if total_count > 0 else 0.0
            
            return SentimentResponse(
                channel=channel,
                hours=hours,
                data=data_points,
                avg_sentiment=round(avg_sentiment, 3)
            )
            
    except Exception as e:
        logger.error(f"Error getting sentiment metrics: {e}")
        return SentimentResponse(channel=channel, hours=hours)


@router.get("/kafka", response_model=KafkaMetricsResponse, tags=["Metrics"])
async def get_kafka_metrics():
    """
    Get Kafka topic statistics.
    
    Returns:
        Kafka connection status and topic information.
    """
    try:
        admin_client = None
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=AgentConfig.KAFKA_BOOTSTRAP_SERVERS,
                client_id='fte-metrics',
                request_timeout_ms=10000
            )
            
            # List topics
            existing_topics = set(admin_client.list_topics())
            
            # Build topic stats
            topic_stats = []
            for topic_name, topic_key in TOPICS.items():
                stats = KafkaTopicStats(
                    topic=topic_key,
                    exists=topic_key in existing_topics,
                    partitions=0
                )
                
                # Get partition count if topic exists
                if topic_key in existing_topics:
                    try:
                        topic_metadata = admin_client.describe_topics([topic_key])
                        if topic_metadata and len(topic_metadata) > 0:
                            stats.partitions = len(topic_metadata[0].partitions)
                    except:
                        pass
                
                topic_stats.append(stats)
            
            admin_client.close()
            
            return KafkaMetricsResponse(
                connected=True,
                topics=topic_stats,
                total_topics=len(topic_stats)
            )
            
        except Exception as e:
            logger.warning(f"Kafka metrics error: {e}")
            if admin_client:
                try:
                    admin_client.close()
                except:
                    pass
            
            # Return disconnected response
            return KafkaMetricsResponse(
                connected=False,
                topics=[
                    KafkaTopicStats(topic=t, exists=False)
                    for t in TOPICS.values()
                ],
                total_topics=len(TOPICS)
            )
            
    except Exception as e:
        logger.error(f"Error getting Kafka metrics: {e}")
        return KafkaMetricsResponse(connected=False, topics=[], total_topics=0)
