"""
TechCorp Customer Success AI Agent - API Routers

Route modules for different API endpoints.
"""

from api.routers.webhooks import router as webhooks_router
from api.routers.support import router as support_router
from api.routers.tickets import router as tickets_router
from api.routers.customers import router as customers_router
from api.routers.metrics import router as metrics_router

__all__ = [
    "webhooks_router",
    "support_router",
    "tickets_router",
    "customers_router",
    "metrics_router",
]
