"""
TechCorp Customer Success AI Agent - Main FastAPI Application

Production API service with endpoints for:
- Webhooks (Gmail, WhatsApp)
- Support form submissions
- Ticket management
- Customer lookup
- Performance metrics
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

from api.routers import (
    webhooks_router,
    support_router,
    tickets_router,
    customers_router,
    metrics_router,
)
from api.middleware.logging import RequestLoggingMiddleware
from kafka_client import KafkaHealthCheck, FTEKafkaProducer
from database.connection import initialize_db, close_db_pool, check_db_health
from production.config import AgentConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global Kafka producer
_kafka_producer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    global _kafka_producer
    
    # === STARTUP ===
    logger.info("=" * 60)
    logger.info("TechCorp Customer Success FTE API Starting...")
    logger.info("=" * 60)
    
    # Initialize database
    try:
        await initialize_db()
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Initialize Kafka producer
    try:
        _kafka_producer = FTEKafkaProducer()
        await _kafka_producer.start()
        logger.info("Kafka producer started")
    except Exception as e:
        logger.error(f"Kafka producer initialization failed: {e}")
        _kafka_producer = None
    
    logger.info("TechCorp FTE API Started")
    logger.info("=" * 60)
    
    yield
    
    # === SHUTDOWN ===
    logger.info("Shutting down TechCorp FTE API...")
    
    # Stop Kafka producer
    if _kafka_producer:
        try:
            await _kafka_producer.stop()
            logger.info("Kafka producer stopped")
        except Exception as e:
            logger.error(f"Error stopping Kafka producer: {e}")
    
    # Close database pool
    try:
        await close_db_pool()
        logger.info("Database pool closed")
    except Exception as e:
        logger.error(f"Error closing database pool: {e}")
    
    logger.info("TechCorp FTE API Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="TechCorp Customer Success FTE API",
    description="24/7 AI-powered customer support across email, WhatsApp, and web form channels",
    version="2.6.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(support_router, prefix="/support", tags=["Support"])
app.include_router(tickets_router, prefix="/tickets", tags=["Tickets"])
app.include_router(customers_router, prefix="/customers", tags=["Customers"])
app.include_router(metrics_router, prefix="/metrics", tags=["Metrics"])

# Mount static files
app.mount("/static", StaticFiles(directory="api/static"), name="static")


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information.
    
    Returns API details and available endpoints.
    """
    return {
        "name": "TechCorp Customer Success FTE API",
        "version": "2.6.0",
        "description": "AI-powered customer support platform",
        "channels": ["email", "whatsapp", "web_form"],
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "webhooks": "/webhooks",
            "support": "/support",
            "tickets": "/tickets",
            "customers": "/customers",
            "metrics": "/metrics",
            "web_form": "/support/form"
        }
    }


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns system health status including database, Kafka, and channel status.
    """
    timestamp = datetime.now().isoformat()
    
    # Check database
    db_status = "error"
    try:
        db_healthy = await check_db_health()
        db_status = "connected" if db_healthy else "error"
    except Exception:
        db_status = "error"
    
    # Check Kafka
    kafka_status = "error"
    try:
        kafka_connected = await KafkaHealthCheck.check_connection()
        kafka_status = "connected" if kafka_connected else "error"
    except Exception:
        kafka_status = "error"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": timestamp,
        "version": "2.6.0",
        "services": {
            "database": db_status,
            "kafka": kafka_status,
            "channels": {
                "email": "active",
                "whatsapp": "active",
                "web_form": "active"
            }
        }
    }


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": f"The requested resource '{request.url.path}' was not found",
            "path": request.url.path
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later.",
            "path": request.url.path
        }
    )


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
