"""
Create Database User and Database using psycopg2
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os


def create_user_and_db():
    """Create user and database using peer authentication."""
    print("=" * 60)
    print("Creating PostgreSQL User and Database")
    print("=" * 60)
    
    # Try connecting with different methods
    connections = [
        # Trust authentication (local)
        {'host': 'localhost', 'database': 'template1'},
        {'host': '/tmp', 'database': 'template1'},
        {'database': 'template1'},  # Unix socket
    ]
    
    conn = None
    for i, config in enumerate(connections):
        print(f"\nTrying connection {i+1}: {config}")
        try:
            conn = psycopg2.connect(**config)
            print(f"✓ Connected successfully!")
            break
        except Exception as e:
            print(f"✗ Failed: {e}")
            conn = None
    
    if not conn:
        print("\n❌ Could not connect to PostgreSQL with any method.")
        print("\nPlease ensure:")
        print("1. PostgreSQL is running")
        print("2. You have permission to connect")
        print("3. pg_hba.conf allows local connections")
        return False
    
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Create user
    print("\nCreating user 'fte_user'...")
    try:
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'fte_user'")
        if cursor.fetchone():
            print("User 'fte_user' already exists.")
        else:
            cursor.execute("CREATE ROLE fte_user WITH LOGIN PASSWORD 'fte_password123'")
            print("User 'fte_user' created.")
    except Exception as e:
        print(f"Error creating user: {e}")
    
    # Create database
    print("\nCreating database 'fte_db'...")
    try:
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'fte_db'")
        if cursor.fetchone():
            print("Database 'fte_db' already exists.")
        else:
            cursor.execute("CREATE DATABASE fte_db OWNER fte_user")
            print("Database 'fte_db' created.")
    except Exception as e:
        print(f"Error creating database: {e}")
    
    # Grant privileges
    print("\nGranting privileges...")
    try:
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE fte_db TO fte_user")
        print("Privileges granted.")
    except Exception as e:
        print(f"Error granting privileges: {e}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("Setup complete! Try running apply_schema.py again.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = create_user_and_db()
    exit(0 if success else 1)
