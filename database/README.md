# Database Setup Guide - TechCorp Customer Success AI Agent

## Quick Start

### Prerequisites
- Docker Desktop must be installed and running
- Python 3.10+ with required packages installed

### Step 1: Start Docker Containers

```bash
docker-compose up -d postgres
```

Wait ~10 seconds for PostgreSQL to initialize.

### Step 2: Run Database Setup

**Option A: Windows Batch File (Recommended)**
```batch
database\setup.bat
```

**Option B: Python Script**
```bash
python database\docker_setup.py
```

**Option C: Manual Docker Commands**
```bash
docker exec fte_postgres psql -U postgres -c "CREATE USER fte_user WITH PASSWORD 'fte_password123';"
docker exec fte_postgres psql -U postgres -c "CREATE DATABASE fte_db OWNER fte_user;"
docker exec fte_postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE fte_db TO fte_user;"
docker exec fte_postgres psql -U fte_user -d fte_db -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
```

### Step 3: Apply Schema

```bash
python database\apply_schema.py
```

Expected output:
```
============================================================
TechCorp Customer Success Agent - Schema Application
============================================================
...
Schema applied successfully!
...
Schema application complete!
Tables: 8
Indexes: 13
============================================================
```

### Step 4: Seed Knowledge Base

```bash
python database\seed_data.py
```

Expected output:
```
============================================================
TechCorp Customer Success Agent - Knowledge Base Seeding
============================================================
...
Knowledge Base Seeding Complete!
  Inserted: X
  Updated:  0
  Skipped:  0
  Total:    X
============================================================
```

### Step 5: Run Tests

```bash
pytest tests\test_database.py -v
```

Expected: 25 tests passing

---

## Troubleshooting

### Error: "role does not exist"

Run the setup script first:
```batch
database\setup.bat
```

### Error: "Docker is not running"

1. Start Docker Desktop
2. Wait for it to fully initialize
3. Run: `docker-compose up -d postgres`

### Error: "connection refused"

1. Check if PostgreSQL container is running:
   ```bash
   docker ps --filter "name=fte_postgres"
   ```
2. If not running, start it:
   ```bash
   docker-compose up -d postgres
   ```

### Error: pytest-asyncio fixture warnings

Ensure you have:
1. `pytest.ini` with `asyncio_mode = auto`
2. Latest pytest-asyncio: `pip install pytest-asyncio --upgrade`

---

## Database Connection Details

| Parameter | Value |
|-----------|-------|
| Host | localhost |
| Port | 5432 |
| Database | fte_db |
| User | fte_user |
| Password | fte_password123 |

---

## Files Created

```
database/
├── schema.sql            # Complete SQL schema
├── connection.py         # Async connection pool
├── queries.py            # All database queries
├── apply_schema.py       # Schema application script
├── seed_data.py          # Knowledge base seeder
├── docker_setup.py       # Docker-based setup script
├── native_setup.py       # Native PostgreSQL setup script
├── setup.bat             # Windows batch setup file
└── migrations/
    └── 001_initial.sql   # Initial migration
```

---

## Schema Summary

### Tables (8)
1. `customers` - Customer records
2. `customer_identifiers` - Cross-channel identifiers
3. `conversations` - Conversation tracking
4. `messages` - Message history
5. `tickets` - Support tickets
6. `knowledge_base` - Product documentation
7. `agent_metrics` - Performance metrics
8. `escalations` - Escalated tickets

### Indexes (13)
- `idx_customers_email`
- `idx_customers_phone`
- `idx_customer_identifiers_value`
- `idx_conversations_customer`
- `idx_conversations_status`
- `idx_conversations_channel`
- `idx_messages_conversation`
- `idx_messages_channel`
- `idx_tickets_status`
- `idx_tickets_channel`
- `idx_tickets_customer`
- `idx_escalations_ticket`
- `idx_agent_metrics_recorded`

---

## Verification

After setup, verify with:

```bash
# Test connection
python database\test_fte_user.py

# Run all tests
pytest tests\test_database.py -v

# Check database directly
docker exec -it fte_postgres psql -U fte_user -d fte_db -c "\dt"
```
