"""
Native PostgreSQL Setup Script

For systems running PostgreSQL natively (not in Docker).
Creates user, database, applies schema, and seeds knowledge base.

Usage: python database\native_setup.py
"""

import subprocess
import sys
import os
from pathlib import Path


def find_psql():
    """Find psql executable in common locations."""
    common_paths = [
        r"C:\Program Files\PostgreSQL\*\bin\psql.exe",
        r"C:\Program Files (x86)\PostgreSQL\*\bin\psql.exe",
    ]
    
    # Try to find psql in PATH first
    try:
        result = subprocess.run(
            "where psql",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')[0].strip()
    except:
        pass
    
    return None


def run_psql_command(command: str, database: str = "postgres", user: str = "postgres") -> tuple[bool, str]:
    """
    Run a psql command.
    
    Args:
        command: SQL command to run.
        database: Database to connect to.
        user: User to connect as.
        
    Returns:
        Tuple of (success, output/error message)
    """
    psql_path = find_psql()
    
    if psql_path:
        cmd = f'"{psql_path}" -U {user} -d {database} -c "{command}"'
    else:
        # Try without explicit path
        cmd = f'psql -U {user} -d {database} -c "{command}"'
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, 'PGPASSWORD': 'postgres'}
        )
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip() or result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def check_postgres_running() -> bool:
    """Check if PostgreSQL is running on port 5432."""
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 5432))
        sock.close()
        return result == 0
    except:
        return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("TechCorp Customer Success Agent - Native PostgreSQL Setup")
    print("=" * 60)
    
    # Check if PostgreSQL is running
    print("\n[1/6] Checking PostgreSQL...")
    if not check_postgres_running():
        print("❌ PostgreSQL is not running on localhost:5432")
        print("\nPlease start PostgreSQL and try again.")
        return False
    print("✓ PostgreSQL is running on localhost:5432")
    
    # Try to connect and create user
    print("\n[2/6] Creating user 'fte_user'...")
    
    # Try different connection methods
    connection_methods = [
        ("postgres", "postgres", "postgres"),
        ("postgres", "postgres", ""),
        ("localhost", "postgres", "postgres"),
    ]
    
    connected = False
    for host, user, password in connection_methods:
        env = os.environ.copy()
        if password:
            env['PGPASSWORD'] = password
        
        try:
            psql_path = find_psql()
            if psql_path:
                cmd = f'"{psql_path}" -h {host} -U {user} -d postgres -c "SELECT 1"'
            else:
                cmd = f'psql -h {host} -U {user} -d postgres -c "SELECT 1"'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                env=env
            )
            
            if result.returncode == 0:
                print(f"✓ Connected as {user}@{host}")
                connected = True
                
                # Create user
                create_user_cmd = f'"{psql_path}" -h {host} -U {user} -d postgres -c "CREATE USER fte_user WITH PASSWORD \'fte_password123\';"' if psql_path else f'psql -h {host} -U {user} -d postgres -c "CREATE USER fte_user WITH PASSWORD \'fte_password123\';"'
                result = subprocess.run(
                    create_user_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=env
                )
                if "already exists" not in result.stdout.lower() and result.returncode != 0:
                    print(f"⚠ Could not create user: {result.stderr or result.stdout}")
                else:
                    print("✓ User 'fte_user' created or already exists")
                
                # Create database
                create_db_cmd = f'"{psql_path}" -h {host} -U {user} -d postgres -c "CREATE DATABASE fte_db OWNER fte_user;"' if psql_path else f'psql -h {host} -U {user} -d postgres -c "CREATE DATABASE fte_db OWNER fte_user;"'
                result = subprocess.run(
                    create_db_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=env
                )
                if "already exists" not in result.stdout.lower() and result.returncode != 0:
                    print(f"⚠ Could not create database: {result.stderr or result.stdout}")
                else:
                    print("✓ Database 'fte_db' created or already exists")
                
                # Grant privileges
                grant_cmd = f'"{psql_path}" -h {host} -U {user} -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE fte_db TO fte_user;"' if psql_path else f'psql -h {host} -U {user} -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE fte_db TO fte_user;"'
                subprocess.run(grant_cmd, shell=True, capture_output=True, text=True, timeout=10, env=env)
                print("✓ Privileges granted")
                
                break
        except Exception as e:
            continue
    
    if not connected:
        print("\n❌ Could not connect to PostgreSQL as superuser")
        print("\nPlease ensure:")
        print("  1. PostgreSQL is running")
        print("  2. You have superuser access")
        print("  3. pg_hba.conf allows local connections")
        print("\nAlternatively, run manually:")
        print('  psql -U postgres -c "CREATE USER fte_user WITH PASSWORD \'fte_password123\';"')
        print('  psql -U postgres -c "CREATE DATABASE fte_db OWNER fte_user;"')
        return False
    
    print("\n" + "=" * 60)
    print("✅ Native PostgreSQL Setup COMPLETE!")
    print("=" * 60)
    print("\nDatabase connection details:")
    print("  Host: localhost:5432")
    print("  Database: fte_db")
    print("  User: fte_user")
    print("  Password: fte_password123")
    print("\nNext steps:")
    print("  1. Run: python database\\apply_schema.py")
    print("  2. Run: python database\\seed_data.py")
    print("  3. Run: pytest tests\\test_database.py -v")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
