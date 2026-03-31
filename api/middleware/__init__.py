"""
TechCorp Customer Success AI Agent - API Middleware

Custom middleware for request logging and error handling.
"""

from api.middleware.logging import RequestLoggingMiddleware

__all__ = ["RequestLoggingMiddleware"]
