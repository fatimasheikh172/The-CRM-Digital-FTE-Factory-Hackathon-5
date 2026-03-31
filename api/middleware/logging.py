"""
Request Logging Middleware for TechCorp Customer Success AI Agent.

Logs every request with:
- Method, path, status code
- Processing time
- Client IP
"""

import time
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests.
    
    Usage:
        app.add_middleware(RequestLoggingMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log details.
        
        Args:
            request: FastAPI request object.
            call_next: Next middleware/handler in chain.
            
        Returns:
            Response object.
        """
        # Record start time
        start_time = time.time()
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Get request details
        method = request.method
        path = request.url.path
        
        # Log request start
        logger.info(f"REQUEST: {method} {path} from {client_ip}")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"RESPONSE: {method} {path} - Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"ERROR: {method} {path} - {type(e).__name__}: {str(e)} - "
                f"Time: {process_time:.3f}s"
            )
            raise
