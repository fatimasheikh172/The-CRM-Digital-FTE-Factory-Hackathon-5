"""
Setup Database Script

Creates the database and user if they don't exist.
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os


def setup_database():
    """Create database and user if they don't exist."""
    print("=" * 60)
    print("TechCorp Customer Success Agent - Database Setup")
    print("=" * 60)
    
    # Connect to default postgres database
    try:
        # Try different connection methods
        conn = None
        errors = []
        
        # Method 1: Try with postgres user
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='postgres',
                user='postgres',
                password='postgres'
            )
        except Exception as e:
            errors.append(f"postgres/postgres: {e}")
            
        # Method 2: Try without password
        if not conn:
            try:
                conn = psycopg2.connect(
                    host='localhost',
                    port=5432,
                    database='postgres',
                    user='postgres'
                )
            except Exception as e:
                errors.append(f"postgres (no password): {e}")
        
        # Method 3: Try with fte_password123
        if not conn:
            try:
                conn = psycopg2.connect(
                    host='localhost',
                    port=5432,
                    database='postgres',
                    user='postgres',
                    password='fte_password123'
                )
            except Exception as e:
                errors.append(f"postgres/fte_password123: {e}")
        
        if not conn:
            print("Could not connect to PostgreSQL. Tried:")
            for err in errors:
                print(f"  - {err}")
            print("\nPlease ensure PostgreSQL is running and accessible.")
            return False
        
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("Connected to PostgreSQL successfully!")
        
        # Create user if not exists
        print("\nCreating user 'fte_user'...")
        try:
            cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'fte_user') THEN
                        CREATE ROLE fte_user WITH LOGIN PASSWORD 'fte_password123';
                    END IF;
                END
                $$;
            """)
            print("User 'fte_user' created or already exists.")
        except Exception as e:
            print(f"Note: {e}")
        
        # Create database if not exists
        print("\nCreating database 'fte_db'...")
        try:
            cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'fte_db') THEN
                        CREATE DATABASE fte_db OWNER fte_user;
                    END IF;
                END
                $$;
            """)
            print("Database 'fte_db' created or already exists.")
        except Exception as e:
            print(f"Note: {e}")
        
        # Grant privileges
        print("\nGranting privileges...")
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE fte_db TO fte_user;")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("Database setup complete!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = setup_database()
    exit(0 if success else 1)
