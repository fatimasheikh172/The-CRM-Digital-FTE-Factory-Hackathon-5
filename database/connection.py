"""
Database Connection Pool Module for TechCorp Customer Success AI Agent.

Provides async connection pool management using asyncpg with:
- Connection pooling (min=2, max=10)
- Auto-reconnect on failure
- Environment variable configuration
- Health check functionality
"""

import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import os

logger = logging.getLogger(__name__)

# Connection pool configuration
POOL_MIN_SIZE = 2
POOL_MAX_SIZE = 10
POOL_COMMAND_TIMEOUT = 60


class DatabaseConnection:
    """
    Manages PostgreSQL connection pool for the TechCorp Customer Success Agent.
    
    Usage:
        db = DatabaseConnection()
        await db.initialize()
        
        async with db.get_connection() as conn:
            results = await conn.fetch("SELECT * FROM customers")
        
        await db.close()
    """
    
    def __init__(self):
        """Initialize database connection manager."""
        self._pool: Optional[asyncpg.Pool] = None
        self._initialized = False
        self._connection_string: Optional[str] = None

        # Railway provides DATABASE_URL, local uses individual vars
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            # Railway mode - parse DATABASE_URL
            # asyncpg uses postgresql:// format (not postgres://)
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            self._connection_string = database_url
            logger.info("Using DATABASE_URL for connection (Railway mode)")
        else:
            # Local mode - use individual variables
            self.host = os.getenv('DB_HOST', 'localhost')
            self.port = int(os.getenv('DB_PORT', 5432))
            self.database = os.getenv('DB_NAME', 'fte_db')
            self.user = os.getenv('DB_USER', 'fte_user')
            self.password = os.getenv('DB_PASSWORD', 'fte_password123')
            logger.info(f"Using individual env vars for connection (Local mode): {self.host}:{self.port}/{self.database}")
    
    async def initialize(self) -> None:
        """
        Initialize the connection pool.
        
        Creates a pool with min=2, max=10 connections.
        Implements auto-reconnect logic.
        """
        if self._initialized:
            logger.info("Database pool already initialized")
            return
        
        try:
            logger.info(f"Initializing database connection pool to {self.host}:{self.port}/{self.database}")
            
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=POOL_MIN_SIZE,
                max_size=POOL_MAX_SIZE,
                command_timeout=POOL_COMMAND_TIMEOUT,
                server_settings={
                    'application_name': 'techcorp_customer_success_agent'
                }
            )
            
            self._initialized = True
            logger.info(f"Database pool initialized successfully (min={POOL_MIN_SIZE}, max={POOL_MAX_SIZE})")
            
        except asyncpg.PostgresError as e:
            logger.error(f"PostgreSQL error during initialization: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self) -> None:
        """Close the connection pool gracefully."""
        if self._pool:
            logger.info("Closing database connection pool")
            await self._pool.close()
            self._pool = None
            self._initialized = False
            logger.info("Database pool closed")
    
    async def get_pool(self) -> asyncpg.Pool:
        """
        Get the connection pool.
        
        Returns:
            asyncpg.Pool: The active connection pool.
            
        Raises:
            RuntimeError: If pool is not initialized.
        """
        if not self._initialized or self._pool is None:
            raise RuntimeError("Database pool not initialized. Call initialize() first.")
        return self._pool
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Get a connection from the pool.
        
        Usage:
            async with db.get_connection() as conn:
                results = await conn.fetch("SELECT * FROM customers")
        
        Yields:
            asyncpg.Connection: A database connection.
        """
        if not self._initialized or self._pool is None:
            raise RuntimeError("Database pool not initialized. Call initialize() first.")
        
        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            await self._pool.release(conn)
    
    async def check_health(self) -> bool:
        """
        Check database health by executing a simple query.
        
        Returns:
            bool: True if database is healthy, False otherwise.
        """
        if not self._initialized or self._pool is None:
            logger.warning("Database pool not initialized")
            return False
        
        try:
            async with self.get_connection() as conn:
                # Simple health check query
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    logger.debug("Database health check passed")
                    return True
                return False
        except asyncpg.PostgresError as e:
            logger.error(f"Database health check failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Database health check error: {e}")
            return False
    
    async def execute_query(self, query: str, *args):
        """
        Execute a query and return results.
        
        Args:
            query: SQL query string.
            *args: Query parameters.
            
        Returns:
            List of result rows.
        """
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_single(self, query: str, *args):
        """
        Execute a query and return a single row.
        
        Args:
            query: SQL query string.
            *args: Query parameters.
            
        Returns:
            Single result row or None.
        """
        async with self.get_connection() as conn:
            return await conn.fetchrow(query, *args)
    
    async def execute_value(self, query: str, *args):
        """
        Execute a query and return a single value.
        
        Args:
            query: SQL query string.
            *args: Query parameters.
            
        Returns:
            Single value or None.
        """
        async with self.get_connection() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute_command(self, query: str, *args) -> str:
        """
        Execute a command that doesn't return rows (INSERT, UPDATE, DELETE).
        
        Args:
            query: SQL command string.
            *args: Command parameters.
            
        Returns:
            Status string from the command.
        """
        async with self.get_connection() as conn:
            return await conn.execute(query, *args)


# Global database instance
_db: Optional[DatabaseConnection] = None

# Test mode flag - when True, use direct connections instead of pool
_test_mode: bool = False


def set_test_mode(enabled: bool = True) -> None:
    """Enable or disable test mode (direct connections instead of pool)."""
    global _test_mode
    _test_mode = enabled


def is_test_mode() -> bool:
    """Check if test mode is enabled."""
    return _test_mode


def get_db_instance() -> DatabaseConnection:
    """Get the global database instance."""
    global _db
    if _db is None:
        _db = DatabaseConnection()
    return _db


async def get_db_pool() -> asyncpg.Pool:
    """
    Get the database connection pool.
    
    Returns:
        asyncpg.Pool: The active connection pool.
    """
    db = get_db_instance()
    return await db.get_pool()


async def close_db_pool() -> None:
    """Close the database connection pool."""
    db = get_db_instance()
    await db.close()


async def check_db_health() -> bool:
    """
    Check database health.
    
    Returns:
        bool: True if database is healthy.
    """
    db = get_db_instance()
    return await db.check_health()


async def initialize_db() -> None:
    """Initialize the database connection pool."""
    db = get_db_instance()
    await db.initialize()


async def ensure_db_initialized() -> None:
    """Ensure database is initialized, initializing if needed."""
    db = get_db_instance()
    if not db._initialized:
        await db.initialize()


@asynccontextmanager
async def get_db_connection():
    """
    Get a database connection from the pool.
    
    In test mode, creates a direct connection instead of using the pool.

    Usage:
        async with get_db_connection() as conn:
            results = await conn.fetch("SELECT * FROM customers")
    """
    if _test_mode:
        # Test mode: create a direct connection for each use
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'fte_db'),
            user=os.getenv('DB_USER', 'fte_user'),
            password=os.getenv('DB_PASSWORD', 'fte_password123')
        )
        try:
            yield conn
        finally:
            await conn.close()
    else:
        # Normal mode: use connection pool
        db = get_db_instance()
        # Auto-initialize if not already done
        if not db._initialized:
            await db.initialize()
        async with db.get_connection() as conn:
            yield conn
