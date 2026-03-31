"""
Pytest configuration and fixtures for TechCorp Customer Success AI Agent tests.

This module sets up test mode for database connections.
In test mode, each test gets its own direct database connection.
"""

import pytest
import os


def pytest_configure(config):
    """Enable test mode for database connections."""
    # Enable test mode - each test gets its own direct connection
    from database.connection import set_test_mode
    set_test_mode(True)
    
    # Set environment variables for test database connection
    os.environ.setdefault('DB_HOST', 'localhost')
    os.environ.setdefault('DB_PORT', '5433')
    os.environ.setdefault('DB_NAME', 'fte_db')
    os.environ.setdefault('DB_USER', 'fte_user')
    os.environ.setdefault('DB_PASSWORD', 'fte_password123')
