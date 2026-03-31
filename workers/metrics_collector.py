"""
TechCorp Customer Success AI Agent - Metrics Collector

Tracks agent performance metrics and saves to database.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import asyncpg

from production.config import AgentConfig


# ============================================================================
# METRICS COLLECTOR
# ============================================================================

class MetricsCollector:
    """
    Tracks agent performance metrics.
    
    Saves metrics to the agent_metrics table in the database.
    Provides methods for querying stats by channel and time period.
    
    Usage:
        collector = MetricsCollector()
        await collector.record_message_processed(
            channel="email",
            latency_ms=1500,
            escalated=False,
            tool_calls_count=5
        )
        stats = await collector.get_channel_stats()
    """
    
    def __init__(self):
        """Initialize the metrics collector."""
        # In-memory buffer for metrics (batched writes)
        self._buffer: List[Dict] = []
        self._buffer_size = 10  # Flush after N records
        
        # Simulation file for persistence
        self.simulation_file = Path(__file__).parent.parent / "simulation" / "metrics.json"
        self.simulation_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing metrics from simulation file
        self._load_simulation_metrics()
    
    def _load_simulation_metrics(self) -> None:
        """Load metrics from simulation file."""
        if self.simulation_file.exists():
            try:
                with open(self.simulation_file, 'r', encoding='utf-8') as f:
                    self._buffer = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self._buffer = []
    
    def _save_simulation_metrics(self) -> None:
        """Save metrics to simulation file."""
        with open(self.simulation_file, 'w', encoding='utf-8') as f:
            json.dump(self._buffer, f, indent=2, default=str)
    
    async def record_message_processed(
        self,
        channel: str,
        latency_ms: float,
        escalated: bool,
        tool_calls_count: int,
        sentiment_score: Optional[float] = None,
        customer_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Record a processed message metric.
        
        Args:
            channel: Channel type (email, whatsapp, web_form).
            latency_ms: Processing latency in milliseconds.
            escalated: Whether the message was escalated.
            tool_calls_count: Number of tool calls made.
            sentiment_score: Optional sentiment score.
            customer_id: Optional customer ID.
            conversation_id: Optional conversation ID.
        
        Returns:
            Metric record ID.
        """
        metric = {
            "channel": channel,
            "latency_ms": latency_ms,
            "escalated": escalated,
            "tool_calls_count": tool_calls_count,
            "sentiment_score": sentiment_score,
            "customer_id": customer_id,
            "conversation_id": conversation_id,
            "recorded_at": datetime.now().isoformat()
        }
        
        # Add to buffer
        self._buffer.append(metric)
        
        # Save to simulation file
        self._save_simulation_metrics()
        
        # Try to save to database
        try:
            await self._save_to_database(metric)
        except Exception:
            pass  # Keep in buffer if DB unavailable
        
        # Flush buffer if full
        if len(self._buffer) >= self._buffer_size:
            await self._flush_buffer()
        
        return f"metric_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    
    async def _save_to_database(self, metric: Dict) -> None:
        """
        Save a single metric to the database.
        
        Args:
            metric: Metric dictionary.
        """
        conn = None
        try:
            conn = await asyncpg.connect(
                host=AgentConfig.DB_HOST,
                port=AgentConfig.DB_PORT,
                database=AgentConfig.DB_NAME,
                user=AgentConfig.DB_USER,
                password=AgentConfig.DB_PASSWORD
            )
            
            await conn.execute(
                """
                INSERT INTO agent_metrics (
                    channel, latency_ms, escalated, tool_calls_count,
                    sentiment_score, customer_id, conversation_id, recorded_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                metric["channel"],
                metric["latency_ms"],
                metric["escalated"],
                metric["tool_calls_count"],
                metric.get("sentiment_score"),
                metric.get("customer_id"),
                metric.get("conversation_id"),
                metric["recorded_at"]
            )
            
        finally:
            if conn:
                await conn.close()
    
    async def _flush_buffer(self) -> None:
        """Flush buffered metrics to database."""
        if not self._buffer:
            return
        
        conn = None
        try:
            conn = await asyncpg.connect(
                host=AgentConfig.DB_HOST,
                port=AgentConfig.DB_PORT,
                database=AgentConfig.DB_NAME,
                user=AgentConfig.DB_USER,
                password=AgentConfig.DB_PASSWORD
            )
            
            # Batch insert
            for metric in self._buffer:
                try:
                    await conn.execute(
                        """
                        INSERT INTO agent_metrics (
                            channel, latency_ms, escalated, tool_calls_count,
                            sentiment_score, customer_id, conversation_id, recorded_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                        metric["channel"],
                        metric["latency_ms"],
                        metric["escalated"],
                        metric["tool_calls_count"],
                        metric.get("sentiment_score"),
                        metric.get("customer_id"),
                        metric.get("conversation_id"),
                        metric["recorded_at"]
                    )
                except asyncpg.PostgresError:
                    pass  # Keep in buffer on error
            
            # Clear buffer on success
            self._buffer = []
            self._save_simulation_metrics()
            
        except Exception:
            pass  # Keep buffer on connection error
        finally:
            if conn:
                await conn.close()
    
    async def get_channel_stats(self, hours: int = 24) -> Dict[str, Dict]:
        """
        Get stats grouped by channel.
        
        Args:
            hours: Time period in hours (default 24).
        
        Returns:
            Dictionary with channel stats:
            {
                "email": {"total": 10, "avg_latency_ms": 1500, "escalation_rate": 0.2},
                ...
            }
        """
        # Get metrics from buffer and simulation file
        cutoff = datetime.now() - timedelta(hours=hours)
        metrics = [
            m for m in self._buffer
            if datetime.fromisoformat(m["recorded_at"]) > cutoff
        ]
        
        # Also try to get from database
        db_metrics = await self._get_metrics_from_db(hours)
        metrics.extend(db_metrics)
        
        # Group by channel
        channel_data: Dict[str, List] = {}
        for metric in metrics:
            channel = metric["channel"]
            if channel not in channel_data:
                channel_data[channel] = []
            channel_data[channel].append(metric)
        
        # Calculate stats
        stats = {}
        for channel, channel_metrics in channel_data.items():
            total = len(channel_metrics)
            avg_latency = sum(m["latency_ms"] for m in channel_metrics) / total if total > 0 else 0
            escalated = sum(1 for m in channel_metrics if m["escalated"])
            escalation_rate = escalated / total if total > 0 else 0
            
            stats[channel] = {
                "total": total,
                "avg_latency_ms": round(avg_latency, 2),
                "escalation_rate": round(escalation_rate, 2),
                "escalated_count": escalated
            }
        
        return stats
    
    async def _get_metrics_from_db(self, hours: int) -> List[Dict]:
        """
        Get metrics from database.
        
        Args:
            hours: Time period in hours.
        
        Returns:
            List of metric dictionaries.
        """
        conn = None
        try:
            conn = await asyncpg.connect(
                host=AgentConfig.DB_HOST,
                port=AgentConfig.DB_PORT,
                database=AgentConfig.DB_NAME,
                user=AgentConfig.DB_USER,
                password=AgentConfig.DB_PASSWORD
            )
            
            cutoff = datetime.now() - timedelta(hours=hours)
            
            rows = await conn.fetch(
                """
                SELECT channel, latency_ms, escalated, tool_calls_count,
                       sentiment_score, recorded_at
                FROM agent_metrics
                WHERE recorded_at > $1
                """,
                cutoff
            )
            
            return [
                {
                    "channel": row["channel"],
                    "latency_ms": row["latency_ms"],
                    "escalated": row["escalated"],
                    "tool_calls_count": row["tool_calls_count"],
                    "sentiment_score": row["sentiment_score"],
                    "recorded_at": row["recorded_at"].isoformat() if row["recorded_at"] else datetime.now().isoformat()
                }
                for row in rows
            ]
            
        except asyncpg.PostgresError:
            return []
        finally:
            if conn:
                await conn.close()
    
    async def get_performance_summary(self) -> Dict:
        """
        Get overall performance summary.
        
        Returns:
            Dictionary with summary stats:
            - total_messages_processed
            - avg_response_time_ms
            - escalation_rate
            - busiest_channel
        """
        # Get all metrics
        metrics = self._buffer.copy()
        
        # Also try database
        db_metrics = await self._get_metrics_from_db(24 * 30)  # Last 30 days
        metrics.extend(db_metrics)
        
        if not metrics:
            return {
                "total_messages_processed": 0,
                "avg_response_time_ms": 0,
                "escalation_rate": 0,
                "busiest_channel": None
            }
        
        # Calculate summary
        total = len(metrics)
        avg_latency = sum(m["latency_ms"] for m in metrics) / total
        escalated = sum(1 for m in metrics if m["escalated"])
        escalation_rate = escalated / total
        
        # Find busiest channel
        channel_counts = {}
        for m in metrics:
            channel = m["channel"]
            channel_counts[channel] = channel_counts.get(channel, 0) + 1
        
        busiest_channel = max(channel_counts, key=channel_counts.get) if channel_counts else None
        
        return {
            "total_messages_processed": total,
            "avg_response_time_ms": round(avg_latency, 2),
            "escalation_rate": round(escalation_rate, 2),
            "busiest_channel": busiest_channel,
            "channel_breakdown": channel_counts
        }
    
    async def get_escalation_rate(self, hours: int = 24) -> float:
        """
        Get escalation rate for time period.
        
        Args:
            hours: Time period in hours.
        
        Returns:
            Escalation rate (0.0 to 1.0).
        """
        stats = await self.get_channel_stats(hours)
        
        total = sum(s["total"] for s in stats.values())
        escalated = sum(s["escalated_count"] for s in stats.values())
        
        return escalated / total if total > 0 else 0
    
    async def get_average_response_time(self, hours: int = 24) -> float:
        """
        Get average response time for time period.
        
        Args:
            hours: Time period in hours.
        
        Returns:
            Average response time in ms.
        """
        stats = await self.get_channel_stats(hours)
        
        if not stats:
            return 0.0
        
        total_latency = sum(s["avg_latency_ms"] * s["total"] for s in stats.values())
        total_messages = sum(s["total"] for s in stats.values())
        
        return total_latency / total_messages if total_messages > 0 else 0
    
    async def clear_metrics(self, older_than_hours: int = 24) -> int:
        """
        Clear old metrics from database.
        
        Args:
            older_than_hours: Clear metrics older than this.
        
        Returns:
            Number of records cleared.
        """
        conn = None
        try:
            conn = await asyncpg.connect(
                host=AgentConfig.DB_HOST,
                port=AgentConfig.DB_PORT,
                database=AgentConfig.DB_NAME,
                user=AgentConfig.DB_USER,
                password=AgentConfig.DB_PASSWORD
            )
            
            cutoff = datetime.now() - timedelta(hours=older_than_hours)
            
            result = await conn.execute(
                """
                DELETE FROM agent_metrics
                WHERE recorded_at < $1
                """,
                cutoff
            )
            
            # Parse result (e.g., "DELETE 5")
            parts = result.split()
            return int(parts[1]) if len(parts) > 1 else 0
            
        except asyncpg.PostgresError:
            return 0
        finally:
            if conn:
                await conn.close()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_metrics_collector() -> MetricsCollector:
    """
    Create a metrics collector instance.
    
    Returns:
        MetricsCollector instance.
    """
    return MetricsCollector()


# ============================================================================
# MAIN (for testing)
# ============================================================================

async def main():
    """Test the metrics collector."""
    print("=" * 60)
    print("Metrics Collector Test")
    print("=" * 60)
    
    collector = MetricsCollector()
    
    # Record some test metrics
    print("\n1. Recording test metrics...")
    
    test_metrics = [
        {"channel": "email", "latency_ms": 1500, "escalated": False, "tool_calls_count": 5},
        {"channel": "email", "latency_ms": 2000, "escalated": True, "tool_calls_count": 6},
        {"channel": "whatsapp", "latency_ms": 800, "escalated": False, "tool_calls_count": 4},
        {"channel": "whatsapp", "latency_ms": 1200, "escalated": False, "tool_calls_count": 3},
        {"channel": "web_form", "latency_ms": 1800, "escalated": False, "tool_calls_count": 5},
    ]
    
    for m in test_metrics:
        await collector.record_message_processed(**m)
        print(f"   Recorded: {m['channel']} - {m['latency_ms']}ms")
    
    # Get channel stats
    print("\n2. Channel stats:")
    stats = await collector.get_channel_stats()
    for channel, data in stats.items():
        print(f"   {channel}: {data}")
    
    # Get performance summary
    print("\n3. Performance summary:")
    summary = await collector.get_performance_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
