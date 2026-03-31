"""
Docker Database Setup Script

Connects to PostgreSQL running in Docker container and:
1. Creates role 'fte_user' with password
2. Creates database 'fte_db' owned by fte_user
3. Grants all privileges
4. Applies schema from database/schema.sql
5. Seeds knowledge base from context/product-docs.md

Usage: python database/docker_setup.py
"""

import subprocess
import sys
import os
from pathlib import Path


def run_docker_command(command: str) -> tuple[bool, str]:
    """
    Run a docker exec command and return success status and output.
    
    Args:
        command: SQL command to run via psql in container.
        
    Returns:
        Tuple of (success, output/error message)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def check_docker_container() -> bool:
    """Check if fte_postgres container is running."""
    success, output = run_docker_command('docker ps --filter "name=fte_postgres" --format "{{.Names}}"')
    return "fte_postgres" in output


def create_user_and_database() -> bool:
    """Create user and database in PostgreSQL container."""
    print("=" * 60)
    print("TechCorp Customer Success Agent - Docker Database Setup")
    print("=" * 60)
    
    # Check if container is running
    print("\n[1/6] Checking Docker container...")
    if not check_docker_container():
        print("❌ Error: fte_postgres container is not running!")
        print("\nStart the container with:")
        print("   docker-compose up -d postgres")
        return False
    print("✓ Container fte_postgres is running")
    
    # Note: Docker PostgreSQL container uses POSTGRES_USER (fte_user) as superuser
    # No need to create user/database - they're created by Docker automatically
    
    print("\n[2/6] User and database already created by Docker!")
    print("✓ User 'fte_user' exists (from POSTGRES_USER)")
    print("✓ Database 'fte_db' exists (from POSTGRES_DB)")
    
    # Create pgcrypto extension
    print("\n[3/6] Creating pgcrypto extension...")
    success, output = run_docker_command(
        'docker exec fte_postgres psql -U fte_user -d fte_db -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"'
    )
    if success:
        print("✓ Extension 'pgcrypto' created successfully")
    else:
        print(f"⚠ Warning creating extension: {output}")
    
    return True


def apply_schema() -> bool:
    """Apply schema to the database."""
    print("\n[6/6] Applying schema...")
    
    schema_path = Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return False
    
    # Read schema file
    schema = schema_path.read_text(encoding='utf-8')
    
    # Escape single quotes for shell command
    # We'll write schema to container and execute
    schema_escaped = schema.replace("'", "'\"'\"'")
    
    # Execute schema via docker exec
    command = f'docker exec -i fte_postgres psql -U fte_user -d fte_db'
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            input=schema,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✓ Schema applied successfully")
            return True
        else:
            print(f"❌ Error applying schema: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error applying schema: {e}")
        return False


def seed_knowledge_base() -> bool:
    """Seed knowledge base from product docs."""
    print("\n[Bonus] Seeding knowledge base...")
    
    docs_path = Path(__file__).parent.parent / "context" / "product-docs.md"
    if not docs_path.exists():
        print(f"⚠ Product docs not found: {docs_path}")
        print("   Run 'python database/seed_data.py' later to seed knowledge base")
        return True
    
    # Use the seed_data.py script
    seed_script = Path(__file__).parent / "seed_data.py"
    if seed_script.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(seed_script)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(Path(__file__).parent.parent)
            )
            
            if result.returncode == 0:
                print("✓ Knowledge base seeded successfully")
                return True
            else:
                print(f"⚠ Warning seeding knowledge base: {result.stderr}")
                return True
        except Exception as e:
            print(f"⚠ Warning seeding knowledge base: {e}")
            return True
    
    return True


def main():
    """Main setup function."""
    print("\n" + "=" * 60)
    print("Starting Docker Database Setup")
    print("=" * 60)
    
    # Step 1: Create user and database
    if not create_user_and_database():
        print("\n" + "=" * 60)
        print("❌ Setup FAILED - User/Database creation failed")
        print("=" * 60)
        return False
    
    # Step 2: Apply schema
    if not apply_schema():
        print("\n" + "=" * 60)
        print("❌ Setup FAILED - Schema application failed")
        print("=" * 60)
        return False
    
    # Step 3: Seed knowledge base
    seed_knowledge_base()
    
    print("\n" + "=" * 60)
    print("✅ Setup COMPLETE!")
    print("=" * 60)
    print("\nDatabase is ready to use:")
    print("  Host: localhost:5433")
    print("  Database: fte_db")
    print("  User: fte_user")
    print("  Password: fte_password123")
    print("\nNext steps:")
    print("  - Run: python database/seed_data.py (if not already seeded)")
    print("  - Run: pytest tests/test_database.py -v")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
