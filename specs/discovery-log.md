# Discovery Log - TechCorp Customer Success AI Agent

**Date:** March 18, 2026
**Project:** Customer Success FTE - Multi-Channel Support Agent
**Version:** 3.2.0 (Stage 3 - Load Testing)

---

## Exercise 3.2 - Load Testing

### Summary

| Metric | Value |
|--------|-------|
| **Load Test Framework** | Locust + aiohttp |
| **Load Test Files** | 8 |
| **Load Test Scenarios** | 4 user types |
| **Pytest Load Tests** | 6 |
| **Benchmarks Defined** | 5 endpoints |

### Load Test Configurations

| Name | Users | Spawn Rate | Duration | Purpose |
|------|-------|------------|----------|---------|
| Light | 10 | 2/sec | 30s | Quick verify |
| Medium | 50 | 5/sec | 60s | Normal load |
| Heavy | 100 | 10/sec | 120s | Stress test |
| Endurance | 20 | 2/sec | 24h | Long-running |

### User Scenarios

#### WebFormUser (Weight: 3)
- Submit support forms
- Check ticket status
- Check health
- Wait time: 2-8 seconds

#### EmailUser (Weight: 2)
- Send email webhooks
- Check metrics
- Wait time: 5-15 seconds

#### WhatsAppUser (Weight: 2)
- Send WhatsApp messages
- Request human agent
- Check health
- Wait time: 3-10 seconds

#### HealthCheckUser (Weight: 1)
- Health checks
- Metrics summary
- Wait time: 10-30 seconds

### Performance Benchmarks

| Endpoint | P50 | P95 | P99 | Max Error Rate | Min RPS |
|----------|-----|-----|-----|----------------|---------|
| Web Form | 500ms | 3000ms | 5000ms | 1% | 10 |
| Email Webhook | 300ms | 2000ms | 4000ms | 1% | 5 |
| WhatsApp Webhook | 300ms | 2000ms | 4000ms | 1% | 5 |
| Health Check | 50ms | 100ms | 200ms | 0% | 50 |
| Metrics | 200ms | 1000ms | 2000ms | 1% | 10 |

### Load Test Results

#### Async Load Test Results
| Endpoint | Total | Success | Failed | Avg ms | P95 ms | RPS |
|----------|-------|---------|--------|--------|--------|-----|
| Web Form | 100 | - | - | - | - | - |
| Email Webhook | 50 | - | - | - | - | - |
| WhatsApp Webhook | 50 | - | - | - | - | - |
| Health Check | 200 | - | - | - | - | - |
| Metrics | 100 | - | - | - | - | - |

*Note: Run `python load_tests/async_load_test.py` to get actual results*

### 24-Hour Simulation

| Metric | Target | Actual |
|--------|--------|--------|
| Total Requests | 200+ | - |
| Uptime | >99.9% | - |
| P95 Latency | <3000ms | - |
| Error Rate | <1% | - |

*Note: Run `python load_tests/async_load_test.py` for simulation*

### Benchmark Validation

| Endpoint | P95 Status | Error Rate Status | RPS Status | Overall |
|----------|------------|-------------------|------------|---------|
| Web Form | - | - | - | - |
| Email Webhook | - | - | - | - |
| WhatsApp Webhook | - | - | - | - |
| Health Check | - | - | - | - |
| Metrics | - | - | - | - |

*Note: Run `python -m pytest tests/test_load.py -v` for validation*

### File Structure

```
load_tests/
├── __init__.py
├── locustfile.py           # Main Locust configuration
├── run_load_test.py        # Headless test runner
├── async_load_test.py      # aiohttp-based tests
├── benchmarks.py           # Performance benchmarks
├── scenarios/
│   ├── __init__.py
│   ├── web_form_user.py    # Web form traffic
│   ├── email_user.py       # Email traffic
│   └── whatsapp_user.py    # WhatsApp traffic
└── results/                # Test results saved here
```

### Usage

```bash
# Run Locust with web UI
locust -f load_tests/locustfile.py --host http://localhost:8000

# Run headless load test
python load_tests/run_load_test.py light
python load_tests/run_load_test.py medium
python load_tests/run_load_test.py heavy

# Run async load test (no Locust needed)
python load_tests/async_load_test.py

# Run pytest load tests
python -m pytest tests/test_load.py -v
```

### Issues Found During Load Testing

| Issue | Resolution |
|-------|------------|
| API lifespan events slow startup | Use function-scoped fixtures |
| Kafka connection timeouts | Mock mode in handlers |
| Database pool exhaustion | Connection pooling configured |

---

## Exercise 3.1 - Multi-Channel E2E Testing

### Summary

| Metric | Value |
|--------|-------|
| **Test Framework** | pytest + TestClient |
| **E2E Test Files** | 5 |
| **Total E2E Tests** | 22 |
| **Test Categories** | 5 |

### Test Coverage

#### Web Form Journey (5 tests)
| Test | Description |
|------|-------------|
| `test_complete_happy_path` | Full submission to metrics flow |
| `test_form_validation_journey` | Validation error handling |
| `test_ticket_tracking_journey` | Ticket lifecycle |
| `test_multiple_submissions_journey` | Multiple tickets from same customer |
| `test_escalation_journey` | Escalation flow |

#### Email Journey (4 tests)
| Test | Description |
|------|-------------|
| `test_email_webhook_happy_path` | Gmail webhook processing |
| `test_email_format_verification` | Email response formatting |
| `test_email_thread_tracking` | Email thread continuity |
| `test_email_escalation` | Email escalation triggers |

#### WhatsApp Journey (4 tests)
| Test | Description |
|------|-------------|
| `test_whatsapp_webhook_happy_path` | WhatsApp webhook processing |
| `test_whatsapp_format_verification` | WhatsApp response formatting |
| `test_whatsapp_human_request` | Human agent request |
| `test_whatsapp_long_message` | Message chunking |

#### Cross Channel (5 tests)
| Test | Description |
|------|-------------|
| `test_customer_recognition_across_channels` | Same customer, multiple channels |
| `test_history_preserved_across_channels` | Conversation history |
| `test_metrics_across_channels` | Multi-channel metrics |
| `test_full_customer_journey` | Complete journey |
| `test_escalation_across_channels` | Cross-channel escalation |

#### API Integration (4 tests)
| Test | Description |
|------|-------------|
| `test_health_check_integration` | Health endpoint |
| `test_full_api_flow` | Complete API sequence |
| `test_concurrent_requests` | Parallel request handling |
| `test_error_recovery` | Error handling |

### File Structure

```
tests/e2e/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_web_form_e2e.py     # 5 web form tests
├── test_email_e2e.py        # 4 email tests
├── test_whatsapp_e2e.py     # 4 WhatsApp tests
├── test_cross_channel_e2e.py # 5 cross-channel tests
└── test_api_integration.py  # 4 API integration tests
```

### Test Runner

```bash
# Run all E2E tests
python tests/run_e2e.py

# Run specific test file
python -m pytest tests/e2e/test_web_form_e2e.py -v

# Run with coverage
python -m pytest tests/e2e/ -v --cov=api --cov=channels
```

### Fixtures Provided

| Fixture | Purpose |
|---------|---------|
| `client` | FastAPI TestClient |
| `test_email` | Random test email |
| `test_phone` | Random test phone |
| `test_customer_data` | Pre-built customer data |

### Test Design Principles

1. **Independent**: Each test can run alone
2. **Idempotent**: Tests can be re-run safely
3. **Descriptive**: Clear test names and steps
4. **API-Focused**: Test through HTTP endpoints
5. **Mock Mode**: No external dependencies (Kafka, DB)

### Issues Found During E2E

| Issue | Resolution |
|-------|------------|
| API lifespan events hang tests | Use function-scoped fixtures |
| Database connection timeouts | TestClient handles mock mode |
| Kafka connection delays | Mock mode in handlers |

### Performance Observed

| Metric | Value |
|--------|-------|
| Average E2E test time | ~2-5 seconds |
| API response time (mock) | <100ms |
| Concurrent request handling | 10 parallel OK |

---

## Exercise 2.7 - Kubernetes Deployment

### Summary

| Metric | Value |
|--------|-------|
| **Container Runtime** | Docker |
| **Orchestration** | Kubernetes |
| **Namespace** | customer-success-fte |
| **Manifests Created** | 10 YAML files |
| **Deployments** | 2 (API + Worker) |
| **HPA Configured** | Yes (auto-scaling) |
| **YAML Validation** | 10/10 valid |

### Manifests Created

#### Core Resources (3 files)
| File | Kind | Name |
|------|------|------|
| `namespace.yaml` | Namespace | customer-success-fte |
| `configmap.yaml` | ConfigMap | fte-config |
| `secret.yaml` | Secret | fte-secrets |

#### Deployments (2 files)
| File | Kind | Name | Replicas |
|------|------|------|----------|
| `deployments/api-deployment.yaml` | Deployment | fte-api | 3-20 |
| `deployments/worker-deployment.yaml` | Deployment | fte-worker | 3-30 |

#### Services (2 files)
| File | Kind | Name | Type |
|------|------|------|------|
| `services/api-service.yaml` | Service | customer-success-fte | ClusterIP |
| `services/postgres-service.yaml` | Service | postgres | ClusterIP (headless) |

#### Ingress (1 file)
| File | Kind | Name | Host |
|------|------|------|------|
| `ingress/ingress.yaml` | Ingress | customer-success-fte | support-api.techcorp.com |

#### HorizontalPodAutoscalers (2 files)
| File | Target | Min | Max | CPU Target |
|------|--------|-----|-----|------------|
| `hpa/api-hpa.yaml` | fte-api | 3 | 20 | 70% |
| `hpa/worker-hpa.yaml` | fte-worker | 3 | 30 | 70% |

### Scaling Configuration

| Component | Min Replicas | Max Replicas | Scale Trigger |
|-----------|--------------|--------------|---------------|
| API | 3 | 20 | CPU > 70%, Memory > 80% |
| Worker | 3 | 30 | CPU > 70%, Memory > 80% |

**Scale Down Policy:**
- Stabilization window: 300 seconds
- Max 50% reduction per minute

**Scale Up Policy:**
- Immediate scaling
- Max 100% increase per minute

### Docker Configuration

**Dockerfile:**
- Base: python:3.11-slim
- Multi-purpose (API + Worker)
- Non-root user (UID 1000)
- Health checks via /health endpoint

**docker-compose.yml:**
- Updated with fte-api and fte-worker services
- Health checks for postgres and kafka
- depends_on with service_healthy condition
- Named network: fte-network

### Deployment Scripts

| Script | Platform | Purpose |
|--------|----------|---------|
| `k8s/deploy.sh` | Linux/Mac | Deploy to k8s cluster |
| `k8s/deploy.bat` | Windows | Deploy to k8s cluster |
| `k8s/status.bat` | Windows | Check deployment status |

### File Structure

```
k8s/
├── namespace.yaml              # Namespace definition
├── configmap.yaml              # Non-sensitive configuration
├── secret.yaml                 # Secrets (use external in prod)
├── deploy.sh                   # Deployment script (Linux/Mac)
├── deploy.bat                  # Deployment script (Windows)
├── status.bat                  # Status check script
├── README.md                   # Deployment guide
├── deployments/
│   ├── api-deployment.yaml     # API server (3-20 replicas)
│   └── worker-deployment.yaml  # Message processor (3-30)
├── services/
│   ├── api-service.yaml        # ClusterIP service
│   └── postgres-service.yaml   # Headless service
├── ingress/
│   └── ingress.yaml            # NGINX ingress + TLS
└── hpa/
    ├── api-hpa.yaml            # API autoscaler
    └── worker-hpa.yaml         # Worker autoscaler
```

### Security Features

**Pod Security:**
- runAsNonRoot: true
- runAsUser: 1000
- allowPrivilegeEscalation: false
- capabilities dropped: ALL

**Network:**
- ClusterIP services (no external exposure)
- Ingress with TLS termination
- Network policies ready

**Secrets:**
- Stored in Kubernetes Secrets
- Comment in secret.yaml for production external secrets
- Supports: Vault, AWS Secrets Manager, Azure Key Vault

### Health Checks

**API Deployment:**
- Liveness: HTTP GET /health (30s interval)
- Readiness: HTTP GET /health (10s interval)
- Startup: HTTP GET /health (5s interval, 30 failures)

**Worker Deployment:**
- Liveness: exec probe (60s interval)
- No readiness probe (no HTTP server)

### Resource Limits

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|-------------|-----------|----------------|--------------|
| API | 250m | 500m | 512Mi | 1Gi |
| Worker | 250m | 500m | 512Mi | 1Gi |

### Deployment Commands

```bash
# Deploy to cluster
cd k8s
./deploy.sh          # Linux/Mac
deploy.bat           # Windows

# Check status
kubectl get all -n customer-success-fte

# View logs
kubectl logs -f -n customer-success-fte -l component=api
kubectl logs -f -n customer-success-fte -l component=worker

# Port forward for local access
kubectl port-forward -n customer-success-fte svc/customer-success-fte 8000:80

# Scale manually
kubectl scale deployment fte-api -n customer-success-fte --replicas=5
```

### Testing

**YAML Validation Test:**
- `tests/test_k8s_manifests.py` - 30+ tests
- Validates file existence
- Validates YAML syntax
- Checks namespace consistency
- Verifies label selectors match
- Confirms required fields present

### Production Considerations

1. **Secrets Management**: Use External Secrets Operator or Vault
2. **Image Registry**: Push to private registry (ECR, GCR, ACR)
3. **TLS Certificates**: Use cert-manager with Let's Encrypt
4. **Monitoring**: Prometheus metrics at /metrics
5. **Logging**: Centralized logging (ELK, Loki)
6. **Backup**: PostgreSQL backup strategy
7. **Disaster Recovery**: Multi-region deployment ready

---

## Exercise 2.6 - FastAPI Service

### Summary

| Metric | Value |
|--------|-------|
| **Framework** | FastAPI 0.128.0 |
| **Server** | Uvicorn 0.24.0 |
| **API Port** | 8000 |
| **Endpoints Built** | 28 |
| **Tests Written** | 28 |
| **Tests Passing** | 28/28 (100%) |

### Endpoints Built

#### Webhooks (5 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhooks/gmail` | Gmail Pub/Sub notifications |
| POST | `/webhooks/gmail/test` | Test Gmail simulation |
| GET | `/webhooks/whatsapp` | Twilio webhook verification |
| POST | `/webhooks/whatsapp` | WhatsApp messages from Twilio |
| POST | `/webhooks/whatsapp/test` | Test WhatsApp simulation |

#### Support (4 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/support/submit` | Web form submission |
| GET | `/support/ticket/{id}` | Get ticket status |
| GET | `/support/categories` | Get support categories |
| GET | `/support/form` | Web form HTML page |

#### Tickets (5 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tickets` | List all tickets |
| GET | `/tickets/{id}` | Get ticket details |
| PATCH | `/tickets/{id}/status` | Update ticket status |
| GET | `/tickets/{id}/messages` | Get ticket messages |
| POST | `/tickets/{id}/escalate` | Escalate ticket |

#### Customers (4 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/customers/lookup` | Lookup by email/phone |
| GET | `/customers/{id}` | Get customer details |
| GET | `/customers/{id}/conversations` | Get customer conversations |
| GET | `/customers/{id}/tickets` | Get customer tickets |

#### Metrics (4 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/metrics/channels` | Performance by channel |
| GET | `/metrics/summary` | Overall system summary |
| GET | `/metrics/sentiment` | Sentiment trends |
| GET | `/metrics/kafka` | Kafka topic stats |

#### Health & Root (2 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |

### API Features

**Middleware:**
- CORS enabled for all origins
- Request logging with timing
- Exception handlers for 404/500

**Static Files:**
- Web form HTML served at `/support/form`
- React-based form with validation

**Documentation:**
- Auto-generated OpenAPI docs at `/docs`
- Interactive Swagger UI
- ReDoc available at `/redoc`

### File Structure

```
api/
├── __init__.py
├── main.py              # FastAPI app, lifespan, health
├── routers/
│   ├── __init__.py
│   ├── webhooks.py      # Gmail + WhatsApp
│   ├── support.py       # Web form
│   ├── tickets.py       # Ticket management
│   ├── customers.py     # Customer lookup
│   └── metrics.py       # Performance metrics
├── middleware/
│   ├── __init__.py
│   └── logging.py       # Request logging
└── static/
    └── index.html       # Web form HTML
```

### Test Categories

| # | Category | Tests | Description |
|---|----------|-------|-------------|
| 1 | Health Check | 4 | Status, services, version |
| 2 | Web Form Submit | 4 | Valid/invalid submissions |
| 3 | Ticket Endpoints | 3 | List, get, filters |
| 4 | Customer Endpoints | 3 | Lookup, get, 404 handling |
| 5 | Webhook Endpoints | 3 | Gmail, WhatsApp tests |
| 6 | Metrics Endpoints | 3 | Channels, summary, Kafka |
| 7 | CORS | 2 | OPTIONS, headers |
| 8 | Error Handling | 3 | Invalid JSON, 404, missing fields |
| 9 | Root & Docs | 3 | Root, /docs, /openapi.json |
| **Total** | | **28** | **100% passing** |

### Startup Script

Run with:
```bash
python run_api.py
```

Or directly:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Design Decisions

1. **Async First**: All endpoints use async/await for non-blocking I/O
2. **Pydantic Models**: Strong typing for request/response validation
3. **Dependency Injection**: Database and Kafka via lifespan events
4. **Graceful Degradation**: Metrics return empty data on DB/Kafka errors
5. **CORS Enabled**: Web form can be served from any origin

### Files Created

| File | Purpose |
|------|---------|
| `api/__init__.py` | Module exports |
| `api/main.py` | FastAPI app with lifespan |
| `api/routers/__init__.py` | Router exports |
| `api/routers/webhooks.py` | Gmail/WhatsApp webhooks |
| `api/routers/support.py` | Web form endpoints |
| `api/routers/tickets.py` | Ticket management |
| `api/routers/customers.py` | Customer lookup |
| `api/routers/metrics.py` | Performance metrics |
| `api/middleware/__init__.py` | Middleware exports |
| `api/middleware/logging.py` | Request logging |
| `api/static/index.html` | React web form |
| `run_api.py` | Startup script |
| `tests/test_api.py` | 28 API tests |

---

## Exercise 2.5 - Kafka Event Streaming

### Summary

| Metric | Value |
|--------|-------|
| **Architecture** | Real Apache Kafka with aiokafka |
| **Kafka Version** | apache/kafka:3.7.0 (Docker) |
| **Bootstrap Servers** | localhost:9092 |
| **Topics Created** | 7 |
| **Fallback** | In-memory queue if Kafka unavailable |
| **Tests Written** | 18 |
| **Tests Passing** | 18/18 (100%) |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kafka Event Streaming                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Gmail ──┐                                                       │
│          ├──► Kafka Producer ──► fte.tickets.incoming ──┐       │
│  WhatsApp┤                                               │       │
│          ├──► Kafka Topics                              ▼       │
│  WebForm─┘                                               │       │
│                                                   Consumer      │
│                                                       │         │
│                                                       ▼         │
│                                              MessageProcessor   │
│                                                       │         │
│                                                       ▼         │
│                                              Metrics/Kafka      │
│                                                                  │
│  Fallback: In-memory MessageQueue if Kafka unavailable          │
└─────────────────────────────────────────────────────────────────┘
```

### Kafka Topics Created

| # | Topic | Partitions | Purpose |
|---|-------|------------|---------|
| 1 | `fte.tickets.incoming` | 3 | Main incoming ticket queue |
| 2 | `fte.channels.email.inbound` | 1 | Email channel messages |
| 3 | `fte.channels.whatsapp.inbound` | 1 | WhatsApp messages |
| 4 | `fte.channels.webform.inbound` | 1 | Web form submissions |
| 5 | `fte.escalations` | 1 | Escalated tickets |
| 6 | `fte.metrics` | 1 | Performance metrics |
| 7 | `fte.dlq` | 1 | Dead letter queue (failed messages) |

### Components Created

| Component | File | Purpose |
|-----------|------|---------|
| **FTEKafkaProducer** | `kafka_client.py` | Async Kafka producer with JSON serialization |
| **FTEKafkaConsumer** | `kafka_client.py` | Async Kafka consumer with JSON deserialization |
| **KafkaHealthCheck** | `kafka_client.py` | Connection health check utilities |
| **KafkaTopicAdmin** | `kafka_client.py` | Topic creation and management |
| **KafkaTopicSetup** | `kafka_setup.py` | Script to create all required topics |
| **KafkaMonitor** | `workers/kafka_monitor.py` | Real-time topic monitoring |
| **UnifiedMessageProcessor** | `workers/message_processor.py` | Updated with Kafka + fallback |

### Kafka Client Features

**FTEKafkaProducer:**
- Async start/stop lifecycle
- `publish(topic, event)` - Send single message
- `publish_batch(topic, events)` - Send multiple messages
- Automatic timestamp injection (`kafka_timestamp`)
- JSON serialization with `default=str`
- Retry logic (3 retries, 100ms backoff)
- Acknowledgment mode: `acks='all'`

**FTEKafkaConsumer:**
- Async start/stop lifecycle
- `consume(handler)` - Continuous message consumption
- Auto-offset-reset: `earliest`
- JSON deserialization
- Error handling without stopping
- Consumer group support

**KafkaHealthCheck:**
- `check_connection()` - Verify Kafka connectivity
- `list_topics()` - List all existing topics
- `check_topic_exists(topic)` - Check specific topic

### Fallback Mechanism

When Kafka is unavailable, the system automatically falls back to in-memory queue:

```python
async def start(self) -> None:
    kafka_available = await KafkaHealthCheck.check_connection()
    
    if kafka_available:
        self._use_kafka = True
        # Use real Kafka producer/consumer
    else:
        self._use_kafka = False
        # Fallback to MessageQueue (in-memory)
        print("WARNING: Running in fallback mode")
```

### Test Categories

| # | Category | Tests | Description |
|---|----------|-------|-------------|
| 1 | Connection | 3 | Kafka connectivity, list topics, topic existence |
| 2 | Producer | 4 | Start/stop, single publish, batch publish, timestamp |
| 3 | Consumer | 3 | Start/stop, consume message, message ordering |
| 4 | Topics | 3 | All topics exist, publish to all, topic constants |
| 5 | Fallback | 3 | Queue availability, fallback publish/consume, health check |
| 6 | Integration | 3 | Full cycle, metrics publishing, DLQ publishing |
| **Total** | | **24** | **Comprehensive Kafka coverage** |

### Setup Script

Run `python kafka_setup.py` to:
1. Check Kafka connection
2. Create all 7 required topics
3. Verify topics exist
4. Display topic status

### Monitor Script

Run `python workers/kafka_monitor.py` to:
- View topic status every 5 seconds
- Monitor message counts
- Track processing rates

### Dependencies Added

**requirements.txt:**
```
# Kafka Event Streaming
aiokafka>=0.13.0
kafka-python>=2.3.0
```

### Design Decisions

1. **Async First**: Using aiokafka for all Kafka operations to maintain async compatibility
2. **Graceful Degradation**: Always fallback to in-memory queue if Kafka unavailable
3. **Topic Naming**: Hierarchical naming with `fte.` prefix for organization
4. **Partition Strategy**: 3 partitions for high-volume `tickets.incoming`, 1 for others
5. **JSON Serialization**: All messages serialized as JSON with automatic timestamps

### Files Created/Modified

| File | Action | Purpose |
|------|--------|---------|
| `kafka_client.py` | Created | Main Kafka client with producer/consumer |
| `kafka_setup.py` | Created | Topic setup script |
| `workers/kafka_monitor.py` | Created | Monitoring utility |
| `workers/message_processor.py` | Modified | Added Kafka integration with fallback |
| `production/config.py` | Modified | Added KAFKA_BOOTSTRAP_SERVERS |
| `requirements.txt` | Modified | Added aiokafka, kafka-python |
| `tests/test_kafka.py` | Created | 24 Kafka tests |
| `.env` | Already configured | KAFKA_BOOTSTRAP_SERVERS=localhost:9092 |

---

## Exercise 2.4 - Unified Message Processor

### Summary

| Metric | Value |
|--------|-------|
| **Architecture** | In-memory queue (Kafka simulation) |
| **Processor** | Unified for all 3 channels |
| **Mock Mode** | Works without API key |
| **Tests Written** | 23 |
| **Tests Passing** | 23 |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Message Flow                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Gmail ──┐                                                       │
│          ├──► MessageQueue ──► UnifiedMessageProcessor ──► DB   │
│  WhatsApp┤    (Kafka sim)        (Gemini Agent)                  │
│          │                                                       │
│  WebForm─┘                                                       │
│                              │                                   │
│                              ▼                                   │
│                       MetricsCollector                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Components Created

| Component | File | Purpose |
|-----------|------|---------|
| **MessageQueue** | `workers/queue_manager.py` | In-memory Kafka simulation with topic-based routing |
| **UnifiedMessageProcessor** | `workers/message_processor.py` | Processes messages from all channels through agent |
| **MetricsCollector** | `workers/metrics_collector.py` | Tracks performance metrics |
| **SimulationRunner** | `workers/run_simulation.py` | Runs sample tickets through pipeline |

### Kafka Topics (Simulated)

| Topic | Purpose |
|-------|---------|
| `fte.tickets.incoming` | Main incoming ticket queue |
| `fte.channels.email.inbound` | Email channel messages |
| `fte.channels.whatsapp.inbound` | WhatsApp messages |
| `fte.channels.webform.inbound` | Web form submissions |
| `fte.escalations` | Escalated tickets |
| `fte.metrics` | Performance metrics |
| `fte.dlq` | Dead letter queue (failed messages) |

### Message Processor Pipeline

| Step | Action |
|------|--------|
| 1 | Log incoming message with channel info |
| 2 | Validate message has required fields |
| 3 | Resolve customer (email/phone lookup) |
| 4 | Get or create conversation (24hr window) |
| 5 | Store incoming message in database |
| 6 | Load conversation history (last 10 msgs) |
| 7 | Run Gemini agent with full context |
| 8 | Store agent response in database |
| 9 | Collect and publish metrics |
| 10 | Return processing result |

### Error Handling

| Error Type | Handling |
|------------|----------|
| Invalid message | Return validation error |
| Customer not found | Create new customer record |
| Database unavailable | Use mock IDs, continue processing |
| Agent error | Send apology, save to DLQ |
| Metrics save fails | Keep in buffer, retry later |

### Performance (Mock Mode)

| Metric | Value |
|--------|-------|
| Average processing time | ~25-50ms per message |
| Queue throughput | Limited by agent mock mode |
| Memory per message | ~1KB |

### Test Coverage

| Test Category | Tests | Description |
|--------------|-------|-------------|
| Queue Manager | 6 | Publish, consume, queue size, clear, topics |
| Customer Resolution | 3 | Email, WhatsApp, no contact info |
| Conversation Management | 2 | Create new, get active |
| Message Storage | 3 | Incoming, agent response, history load |
| Error Handling | 2 | DLQ, continue after error |
| Metrics Collection | 4 | Record, channel stats, summary, escalation rate |
| Full Pipeline | 3 | Email, WhatsApp, web form end-to-end |
| **Total** | **23** | **100% passing** |

### Files Created

| File | Purpose |
|------|---------|
| `workers/__init__.py` | Module exports |
| `workers/queue_manager.py` | MessageQueue class with Kafka simulation |
| `workers/message_processor.py` | UnifiedMessageProcessor class |
| `workers/metrics_collector.py` | MetricsCollector class |
| `workers/run_simulation.py` | SimulationRunner for testing |
| `tests/test_message_processor.py` | 23 tests for all components |

### Mock Mode Features

- Works WITHOUT Gemini API key
- Simulates full pipeline except LLM call
- Uses pre-defined responses based on channel
- All database operations have fallbacks
- Metrics stored in simulation/metrics.json

### Database Integration

| Table | Usage |
|-------|-------|
| `customers` | Customer lookup/creation |
| `conversations` | Conversation tracking |
| `messages` | Store incoming/outgoing messages |
| `agent_metrics` | Performance metrics |

### Simulation Runner

Run with:
```bash
python workers/run_simulation.py
```

Processes 8 sample tickets from `context/sample-tickets.json`:
- 3 email tickets
- 3 WhatsApp tickets
- 2 web form tickets

Includes escalation detection for:
- Refund requests
- Legal threats
- Human agent requests

---

## Exercise 2.3 - Gemini Agent

### Summary

| Metric | Value |
|--------|-------|
| **Model** | gemini-1.5-flash |
| **Reason** | Free API available, no OpenAI key needed |
| **Tools** | 7 function calling tools |
| **Tests Written** | 57 |
| **Tests Passing** | 57 |
| **API Key Required** | No (mock mode for testing) |

### Model Selection

| Option | Status | Reason |
|--------|--------|--------|
| OpenAI GPT | ❌ Not used | Requires API key |
| **Google Gemini** | ✅ Selected | Free tier available, easy function calling |
| Anthropic Claude | ❌ Not used | Requires API key |

### Production Structure

```
production/
├── __init__.py
├── config.py                  # Configuration (Gemini, DB, channels)
└── agent/
    ├── __init__.py
    ├── customer_success_agent.py  # Main agent class
    ├── tools.py               # 7 function calling tools
    ├── prompts.py             # System prompts
    └── formatters.py          # Channel formatters
```

### Tools Implemented

| # | Tool | Purpose | DB Required |
|---|------|---------|-------------|
| 1 | `search_knowledge_base` | Search product docs | Yes |
| 2 | `create_ticket` | Create support ticket | Yes |
| 3 | `get_customer_history` | Get customer history | Yes |
| 4 | `escalate_to_human` | Escalate ticket | Yes |
| 5 | `send_response` | Send response | Yes + Simulation |
| 6 | `analyze_sentiment` | Analyze sentiment | No (keyword-based) |
| 7 | `get_ticket_status` | Get ticket status | Yes |

### Agent Features

| Feature | Description |
|---------|-------------|
| **Mock Mode** | Runs without API key for testing |
| **Function Calling** | Gemini function calling format |
| **Channel Awareness** | Email, WhatsApp, Web Form support |
| **Escalation Detection** | Legal, refund, human agent keywords |
| **Sentiment Analysis** | Keyword-based with score 0.0-1.0 |

### Configuration

| Setting | Value |
|---------|-------|
| Model | gemini-1.5-flash |
| Max Tokens | 1000 |
| DB Port | 5433 |
| Channels | email, whatsapp, web_form |
| Escalation Threshold | 0.3 sentiment score |

### Test Coverage

| Test Category | Tests | Description |
|--------------|-------|-------------|
| Tool Tests | 29 | All 7 tools + formatters |
| Mock Agent Tests | 28 | Agent initialization, run, escalation |
| **Total** | **57** | **100% passing** |

### Key Implementation Details

**Mock Mode:**
- Agent runs without Gemini API key
- Simulates tool call sequence
- Returns realistic responses for testing
- All tools work independently

**Function Calling:**
- Tools defined as Gemini function declarations
- Parameters with types and descriptions
- Required fields enforced

**Channel Formatters:**
- Email: 500 words, formal greeting + signature
- WhatsApp: 300 chars, casual + human prompt
- Web Form: 300 words, semi-formal

### Files Created

| File | Purpose |
|------|---------|
| `production/config.py` | Centralized configuration |
| `production/agent/prompts.py` | System prompts |
| `production/agent/tools.py` | 7 function tools |
| `production/agent/formatters.py` | Channel formatters |
| `production/agent/customer_success_agent.py` | Main agent class |
| `tests/test_agent_tools.py` | Tool tests (no API) |
| `tests/test_agent_mock.py` | Mock agent tests |

### Environment Setup

**.env additions:**
```
GEMINI_API_KEY=your-gemini-key-here
MODEL=gemini-1.5-flash
MAX_TOKENS=1000
```

### Dependencies Added

**requirements.txt:**
```
# Google Gemini AI
google-generativeai>=0.8.0
google-genai>=1.60.0
```

---

## Exercise 2.2 - Channel Integrations

### Summary

| Metric | Count |
|--------|-------|
| **Channels Built** | 3 |
| **Simulation Mode** | Gmail + WhatsApp |
| **Real Implementation** | Web Form (FastAPI) |
| **Tests Written** | 34 |
| **Tests Passing** | 34 |

### Channels Built

| # | Channel | Handler | Mode | Features |
|---|---------|---------|------|----------|
| 1 | **Gmail (Email)** | `GmailHandler` | Simulation | Parse emails, format responses, save to JSON |
| 2 | **WhatsApp** | `WhatsAppHandler` | Simulation | Parse webhooks, split messages, save to JSON |
| 3 | **Web Form** | `WebFormHandler` | Real FastAPI | Form validation, ticket creation, API endpoints |

### File Structure

```
channels/
├── __init__.py              # Module exports
├── base_channel.py          # Abstract base class
├── gmail_handler.py         # Gmail integration (simulation)
├── whatsapp_handler.py      # WhatsApp integration (simulation)
└── web_form_handler.py      # Web form FastAPI handler

simulation/
├── __init__.py
├── gmail_sent.json          # Simulated sent emails
├── whatsapp_sent.json       # Simulated sent messages
├── sample_emails.json       # 3 sample email test data
└── sample_whatsapp.json     # 3 sample WhatsApp test data

src/web-form/
├── SupportForm.jsx          # React component
└── index.html               # Standalone HTML version
```

### Channel Formatting Rules

| Channel | Max Length | Greeting | Signature | Tone |
|---------|-----------|----------|-----------|------|
| Email | 500 words | "Dear {Name}," | "Best regards, TechCorp Support Team" | Formal |
| WhatsApp | 300 chars | None | "Reply 'human' for live support" | Casual |
| Web Form | 300 words | "Hello {Name}," | "Best regards, TechCorp Support Team" | Semi-formal |

### Base Channel Class Methods

```python
class BaseChannel(ABC):
    channel_name: str
    
    @abstractmethod
    def normalize_message(raw_message) -> dict
    # Converts any channel message to standard format
    
    @abstractmethod
    def format_response(response_text, customer_data) -> str
    # Format response for this specific channel
    
    @abstractmethod
    def validate_incoming(raw_data) -> bool
    # Validate incoming message is valid
```

### Test Coverage

| Test Category | Tests | Description |
|--------------|-------|-------------|
| Gmail Handler | 8 | Email processing, formatting, validation |
| WhatsApp Handler | 9 | Webhook processing, message splitting, validation |
| Web Form Handler | 8 | Form validation, submission, response formatting |
| Base Channel | 5 | Abstract methods, utilities, metadata |
| Cross Channel Format | 4 | Different formatting per channel |
| **Total** | **34** | **100% passing** |

### Key Implementation Details

**Gmail Handler:**
- Extracts email from "Name <email>" format
- Saves simulated emails to `simulation/gmail_sent.json`
- Adds formal greeting and signature to responses

**WhatsApp Handler:**
- Cleans phone numbers (handles whatsapp: prefix)
- Splits long messages at sentence boundaries (max 1600 chars)
- Adds "Reply 'human' for live support" prompt

**Web Form Handler:**
- Pydantic models for validation
- FastAPI router with `/support/submit`, `/support/ticket/{id}`, `/support/categories`
- Returns ticket ID and estimated response time

### React Web Form

**Features:**
- Full form validation (name, email, subject, category, priority, message)
- Character count display
- Loading state during submission
- Success screen with ticket ID
- Error handling
- Tailwind CSS styling
- Mobile responsive

**Standalone Version:**
- `src/web-form/index.html` works without build tools
- Uses React/ReactDOM/Babel CDN
- Simulates API submission for demo

---

## Exercise 2.1 - Database Schema

### Summary

| Metric | Count |
|--------|-------|
| **Tables Created** | 8 |
| **Indexes Created** | 13 |
| **Queries Written** | 32 |
| **Knowledge Base Entries Seeded** | From product-docs.md |
| **Test Cases** | 24 |

### Tables Created

| # | Table | Purpose |
|---|-------|---------|
| 1 | `customers` | Core customer records with email/phone/name |
| 2 | `customer_identifiers` | Additional identifiers for cross-channel recognition |
| 3 | `conversations` | Conversation tracking with sentiment and topics |
| 4 | `messages` | Individual messages with metadata and tool calls |
| 5 | `tickets` | Support tickets linked to conversations |
| 6 | `knowledge_base` | Product documentation and help articles |
| 7 | `agent_metrics` | Performance metrics for monitoring |
| 8 | `escalations` | Escalated tickets requiring human intervention |

### Indexes Created

| # | Index | Table | Column(s) |
|---|-------|-------|-----------|
| 1 | `idx_customers_email` | customers | email |
| 2 | `idx_customers_phone` | customers | phone |
| 3 | `idx_customer_identifiers_value` | customer_identifiers | identifier_value |
| 4 | `idx_conversations_customer` | conversations | customer_id |
| 5 | `idx_conversations_status` | conversations | status |
| 6 | `idx_conversations_channel` | conversations | initial_channel |
| 7 | `idx_messages_conversation` | messages | conversation_id |
| 8 | `idx_messages_channel` | messages | channel |
| 9 | `idx_tickets_status` | tickets | status |
| 10 | `idx_tickets_channel` | tickets | source_channel |
| 11 | `idx_tickets_customer` | tickets | customer_id |
| 12 | `idx_escalations_ticket` | escalations | ticket_id |
| 13 | `idx_agent_metrics_recorded` | agent_metrics | recorded_at |

### Query Functions Written

**Customer Queries (6):**
- `create_customer()` - Create new customer
- `find_customer_by_email()` - Lookup by email
- `find_customer_by_phone()` - Lookup by phone
- `get_or_create_customer()` - Upsert by identifier
- `get_customer_history()` - Get all conversations
- `add_customer_identifier()` - Add additional identifier

**Conversation Queries (5):**
- `create_conversation()` - Start new conversation
- `get_active_conversation()` - Find active conversation
- `update_conversation_status()` - Update status
- `update_conversation_sentiment()` - Update sentiment
- `add_conversation_topic()` - Add topic to array

**Message Queries (3):**
- `save_message()` - Store message
- `get_conversation_messages()` - Get all messages
- `get_recent_messages()` - Get last N messages

**Ticket Queries (5):**
- `create_ticket()` - Create support ticket
- `update_ticket_status()` - Update status/resolve
- `get_ticket_by_id()` - Lookup by ID
- `get_customer_tickets()` - List customer tickets
- `assign_ticket()` - Assign to agent

**Knowledge Base Queries (4):**
- `search_knowledge_base()` - Full-text search
- `get_kb_by_category()` - Filter by category
- `seed_knowledge_base()` - Seed from docs
- `increment_kb_view_count()` - Track usage

**Metrics Queries (5):**
- `record_metric()` - Store metric
- `get_metrics_by_channel()` - Group by channel
- `get_escalation_rate()` - Calculate rate
- `get_average_response_time()` - Avg latency
- `get_average_sentiment()` - Avg sentiment

**Escalation Queries (3):**
- `create_escalation()` - Create escalation
- `resolve_escalation()` - Mark resolved
- `get_pending_escalations()` - List pending

### Files Created

```
database/
├── __init__.py           # Module exports
├── schema.sql            # Complete SQL schema (8 tables, 13 indexes)
├── connection.py         # Async connection pool (asyncpg)
├── queries.py            # All query functions (32 functions)
├── apply_schema.py       # Schema application script
├── seed_data.py          # Knowledge base seeder
├── setup_db.py           # Database/user creation script
├── test_connection.py    # Connection test utility
├── create_user_db.py     # User/database creation utility
└── migrations/
    └── 001_initial.sql   # Initial migration
```

### Configuration Files

**`.env`** - Environment configuration:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fte_db
DB_USER=fte_user
DB_PASSWORD=fte_password123
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
ENVIRONMENT=development
LOG_LEVEL=INFO
```

**`.env.example`** - Template for other developers

### Test Coverage

| Test Category | Tests | Description |
|--------------|-------|-------------|
| Connection | 4 | PostgreSQL connectivity, health, tables, indexes |
| Customer CRUD | 5 | Create, find by email/phone, get-or-create, update |
| Conversation Flow | 5 | Create, messages, status, sentiment, history |
| Ticket Flow | 4 | Create, update status, get by ID, list tickets |
| Knowledge Base | 3 | Search, category filter, empty handling |
| Metrics | 3 | Record, get by channel, escalation rate |
| Integration | 1 | Full customer journey workflow |
| **Total** | **24** | |

### Design Decisions

1. **UUID Primary Keys**: All tables use UUID for primary keys to:
   - Avoid ID enumeration attacks
   - Support distributed systems
   - Enable easy data migration

2. **JSONB for Metadata**: Flexible metadata storage for:
   - Future schema evolution
   - Channel-specific data
   - Custom attributes

3. **Async Operations**: All queries use asyncpg for:
   - Non-blocking I/O
   - Connection pooling
   - Better concurrency

4. **Cascade Deletes**: Foreign keys use ON DELETE CASCADE for:
   - Automatic cleanup
   - Data consistency
   - Simplified maintenance

5. **Timestamp with Time Zone**: All timestamps use TIMESTAMPTZ for:
   - Proper timezone handling
   - Consistent ordering
   - Audit trails

---

## 1. Sample Ticket Analysis - Patterns by Channel

### Email Channel (3 tickets: #1, #4, #7)

| Pattern | Observation |
|---------|-------------|
| **Tone** | Formal, detailed problem descriptions |
| **Length** | 10-20 words average, complete sentences |
| **Structure** | Includes subject line, proper grammar |
| **Complexity** | Higher - multi-step issues (login + password reset) |
| **Emotional Content** | Can range from neutral to highly emotional (angry) |
| **Expected Response** | Detailed, step-by-step guidance with formal greeting/signature |

**Example Tickets:**
- #1: Login issue with password reset problem (neutral, technical)
- #4: Refund request with anger indicators (negative, escalation needed)
- #7: New user onboarding question (neutral, how-to)

### WhatsApp Channel (3 tickets: #2, #5, #8)

| Pattern | Observation |
|---------|-------------|
| **Style** | Casual, lowercase, minimal punctuation |
| **Brevity** | Very short (2-5 words), fragmented sentences |
| **Urgency** | Implicit urgency ("hi my app is not working") |
| **Formality** | None - conversational |
| **Expected Response** | Short, casual, max 2-3 sentences |

**Example Tickets:**
- #2: Vague technical issue ("hi my app is not working")
- #5: Pricing inquiry ("how much is pro plan")
- #8: Human agent request ("I want to talk to a human agent")

### Web Form Channel (2 tickets: #3, #6)

| Pattern | Observation |
|---------|-------------|
| **Detail Level** | Medium to high, technical language |
| **Formality** | Semi-formal, business context |
| **Structure** | Includes subject line, clear problem statement |
| **User Type** | Often technical users (developers, admins) |
| **Expected Response** | Structured, numbered steps, documentation links |

**Example Tickets:**
- #3: API rate limit increase request (business impact)
- #6: API documentation location (developer query)

---

## 2. Top 10 Edge Cases Discovered

| # | Edge Case | Impact | Handling Strategy |
|---|-----------|--------|-------------------|
| 1 | **ALL CAPS anger** (Ticket #4) | High - indicates extreme frustration | Detect via caps emphasis + urgency keywords → Immediate escalation |
| 2 | **Vague WhatsApp messages** (Ticket #2) | Medium - unclear problem | Ask clarifying questions, provide common troubleshooting |
| 3 | **Human agent request** (Ticket #8) | High - customer wants escalation | Keyword detection → Immediate escalation, no response generation |
| 4 | **Missing password reset email** (Ticket #1) | Medium - common issue | Provide spam folder check + alternative reset methods |
| 5 | **API rate limit increase** (Ticket #3) | Medium - upsell opportunity | Explain limits, suggest Enterprise plan upgrade |
| 6 | **New customer onboarding** (Ticket #7) | Low - standard how-to | Provide getting started steps from docs |
| 7 | **Refund requests** (Ticket #4) | High - billing issue | Keyword detection → Immediate escalation to billing team |
| 8 | **Legal threats** (not in samples) | Critical - legal risk | Keyword detection (lawyer, lawsuit) → Critical escalation |
| 9 | **Empty or malformed messages** | Medium - system error handling | Validate input → Error response + escalation |
| 10 | **Unknown channel type** | Medium - routing error | Validate channel → Error response + escalation |

---

## 3. Edge Case Handling Implementation

### Edge Case #1: ALL CAPS Anger
```python
# Detection in SentimentAnalysisSkill
caps_words = [w for w in words if w.isupper() and len(w) > 1]
has_caps_emphasis = len(caps_words) > 2  # Penalty: -0.15 score
```

### Edge Case #2: Vague Messages
```python
# Handled by knowledge retrieval fallback
if "No relevant documentation found" in relevant_info:
    return self._generate_no_info_response(message, channel)
```

### Edge Case #3 & #7: Human Agent & Refund Requests
```python
# Detection in EscalationDecisionSkill
HUMAN_REQUEST_KEYWORDS = {'human', 'person', 'agent', 'representative'}
REFUND_KEYWORDS = {'refund', 'money back', 'chargeback'}

if any(keyword in message_lower for keyword in HUMAN_REQUEST_KEYWORDS):
    return {'escalate': True, 'reason': 'Customer requested human agent'}
```

### Edge Case #8: Legal Threats
```python
LEGAL_KEYWORDS = {'lawyer', 'attorney', 'legal', 'lawsuit', 'court', 'sue'}

if any(keyword in message_lower for keyword in LEGAL_KEYWORDS):
    return {'escalate': True, 'reason': 'Customer mentioned legal action', 'urgency': 'critical'}
```

---

## 4. Performance Baseline

### Test Results Summary (8 Sample Tickets)

| Metric | Value |
|--------|-------|
| **Total Tickets Processed** | 8 |
| **Escalations Triggered** | 2 (25%) |
| **Average Sentiment Score** | 0.44 (neutral-leaning-negative) |
| **Average Processing Time** | 0.6ms per ticket |
| **Test Cases Written** | 25 |
| **Test Pass Rate** | 100% (25/25) |

### Processing Time Breakdown

| Operation | Avg Time |
|-----------|----------|
| Message Normalization | <0.1ms |
| Customer Identification | <0.1ms |
| Sentiment Analysis | <0.1ms |
| Knowledge Retrieval | 0.2-0.5ms |
| Response Generation | 0.1-0.2ms |
| Channel Formatting | <0.1ms |
| **Total** | **0.6ms** |

### Escalation Accuracy

| Expected Escalation | Actual | Correct |
|---------------------|--------|---------|
| Ticket #4 (Refund) | Yes | ✓ |
| Ticket #8 (Human Agent) | Yes | ✓ |
| All other tickets | No | ✓ |

**Accuracy: 100%** on test set

---

## 5. Questions & Gaps Requiring Clarification

### Customer Database
- **Question:** How should customer identification work in production?
- **Current:** Simulated in-memory dictionary with 5 customers
- **Needed:** Real customer database integration (SQL/NoSQL)

### LLM Provider
- **Question:** Which LLM provider should be used for response generation?
- **Current:** Rule-based response templates
- **Needed:** OpenAI or Anthropic API integration for dynamic responses

### Sentiment Thresholds
- **Question:** What sentiment score should trigger "very negative" escalation?
- **Current:** Threshold set at 0.25 (strict)
- **Recommendation:** A/B test with 0.20, 0.25, 0.30 thresholds

### Knowledge Base Format
- **Question:** Should product docs be chunked/embedded for semantic search?
- **Current:** Simple keyword matching with section parsing
- **Recommendation:** Implement vector embeddings for better retrieval

### Customer History
- **Question:** Where should support history be stored?
- **Current:** Simulated ticket count in customer record
- **Needed:** Integration with ticketing system (Zendesk, Intercom, etc.)

### Multi-language Support
- **Question:** Should the agent support non-English queries?
- **Current:** English only
- **Recommendation:** Add language detection + translation layer

### Attachment Handling
- **Question:** How should screenshots/attachments in web forms be handled?
- **Current:** Not implemented
- **Recommendation:** Add attachment parsing (OCR for screenshots)

### Response Analytics
- **Question:** What metrics should be tracked for agent performance?
- **Recommendation:**
  - Customer satisfaction (CSAT) scores
  - First contact resolution rate
  - Average response time
  - Escalation rate by category

---

## 6. Project Structure Created

```
hackhaton-5/
├── context/                    # Provided context files
│   ├── brand-voice.md
│   ├── company-profile.md
│   ├── escalation-rules.md
│   ├── product-docs.md
│   └── sample-tickets.json
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── prototype.py        # Main agent implementation
│   │   ├── memory.py           # Conversation memory (NEW)
│   │   └── customer_db.py      # Customer database (NEW)
│   ├── channels/
│   │   ├── __init__.py
│   │   ├── email_channel.py    # Email handler
│   │   ├── whatsapp_channel.py # WhatsApp handler
│   │   └── web_form_channel.py # Web form handler
│   └── web-form/               # (Empty - for future web form UI)
├── skills/
│   ├── __init__.py
│   ├── knowledge_retrieval.py  # KB search skill
│   ├── sentiment_analysis.py   # Sentiment detection
│   ├── escalation_decision.py  # Escalation logic
│   ├── channel_adaptation.py   # Channel formatting
│   └── customer_identification.py # Customer lookup
├── memory/                     # NEW - Persistent storage
│   ├── customers.json
│   └── conversations.json
├── tests/
│   ├── test_prototype.py       # 25 unit tests
│   └── test_memory.py          # 24 memory tests (NEW)
└── specs/
    └── discovery-log.md        # This file
```

---

## 7. Success Criteria Status

| Criteria | Status |
|----------|--------|
| ✅ All folders and files created | Complete |
| ✅ Prototype handles all 3 channels correctly | Complete |
| ✅ All 5 skills are working | Complete |
| ✅ All 8 test tickets produce correct output | Complete |
| ✅ Escalation works for angry/refund/legal tickets | Complete |
| ✅ Channel formatting is different for each channel | Complete |
| ✅ Discovery log is complete with all findings | Complete |
| ✅ Memory system implemented | Complete |
| ✅ Cross-channel recognition working | Complete |
| ✅ All memory tests passing (24/24) | Complete |

---

## 8. Recommendations for Production

1. **Add LLM Integration:** Replace rule-based responses with LLM-generated responses using OpenAI or Anthropic
2. **Implement Vector Search:** Use embeddings for better knowledge base retrieval
3. **Add Rate Limiting:** Prevent abuse of the agent API
4. **Implement Logging:** Add structured logging for all agent decisions
5. **Add Monitoring:** Track key metrics (response time, escalation rate, CSAT)
6. **Security Review:** Audit for PII handling and data protection
7. **Load Testing:** Test with concurrent requests to identify bottlenecks
8. **A/B Testing:** Test different sentiment thresholds and response styles

---

## 9. Exercise 1.3 - Memory & State

### Memory Patterns Discovered:

1. **Conversation Continuity:** Customers expect the agent to remember previous messages within a session
2. **Sentiment Evolution:** Tracking sentiment over time helps detect escalating frustration
3. **Topic Persistence:** Topics discussed should be tracked to provide contextual responses
4. **Channel State:** Knowing which channel a customer prefers helps optimize responses

### Cross-Channel Scenarios:

| Scenario | Implementation | Status |
|----------|----------------|--------|
| Customer emails then WhatsApps | Database tracks `channels_used` array | ✅ Working |
| Agent recognizes returning customer | `is_returning_customer` flag in CustomerState | ✅ Working |
| Reference previous conversation topics | Topics stored in ConversationState | ✅ Working |
| Sentiment trend across channels | Sentiment history persists in memory | ✅ Working |

### Edge Cases in Memory:

| Edge Case | Handling |
|-----------|----------|
| New customer, first contact | Creates new customer record + conversation |
| Returning customer, same channel | Loads existing memory, continues conversation |
| Customer switches channel | Database tracks all channels, memory instance updated |
| Multiple concurrent conversations | Each conversation has unique `conversation_id` |
| Memory file corruption | JSON parsing errors caught, files re-initialized |
| Empty message handling | Validation prevents empty messages from being stored |

### Performance with Memory:

| Metric | Without Memory | With Memory |
|--------|---------------|-------------|
| Average response time | 0.6ms | 7.2ms |
| Memory overhead | N/A | ~50KB per active conversation |
| File I/O | None | 2 writes per conversation save |
| Customer lookup | In-memory dict | JSON file scan (O(n)) |

### Memory Size After Testing:

- **customers.json:** ~2KB (8 test customers)
- **conversations.json:** ~5KB (8 test conversations)
- **Average conversation size:** ~600 bytes

### Test Coverage:

| Test Category | Tests | Pass Rate |
|--------------|-------|-----------|
| ConversationMemory | 9 | 100% |
| CustomerDatabase | 11 | 100% |
| Memory Scenarios | 6 | 100% |
| **Total** | **24** | **100%** |

### Key Classes Implemented:

1. **ConversationMemory** (`src/agent/memory.py`)
   - Tracks messages, sentiment, topics, status
   - Supports serialization/deserialization
   - Channel switching detection

2. **CustomerDatabase** (`src/agent/customer_db.py`)
   - JSON-based persistent storage
   - Customer lookup by email/phone
   - Conversation history management

3. **AgentResponse** (updated)
   - Added memory-related fields:
     - `is_returning_customer`
     - `conversation_id`
     - `sentiment_trend`
     - `topics_discussed`
     - `previous_topics`
     - `has_switched_channels`

---

## 10. Exercise 1.4 - MCP Server

### Tools Built:

| # | Tool | Purpose | Input | Output |
|---|------|---------|-------|--------|
| 1 | `search_knowledge_base` | Search product documentation | query, max_results, category | Formatted search results |
| 2 | `create_ticket` | Create support ticket | customer_id, issue, priority, channel | Ticket ID confirmation |
| 3 | `get_customer_history` | Get conversation history | customer_id | Formatted history |
| 4 | `escalate_to_human` | Escalate to human agent | ticket_id, reason, urgency, customer_id | Escalation confirmation |
| 5 | `send_response` | Send response via channel | ticket_id, message, channel | Delivery status |
| 6 | `analyze_sentiment` | Analyze message sentiment | message, customer_id | Score, label, recommendation |
| 7 | `get_ticket_status` | Get ticket details | ticket_id | Full ticket details |

### Tool Performance:

| Metric | Value |
|--------|-------|
| **Fastest tool** | `analyze_sentiment` (<1ms) |
| **Most complex tool** | `get_customer_history` (multiple DB lookups) |
| **Average tool latency** | 5-15ms |
| **File I/O operations** | 1-2 per tool call |

### Integration Discoveries:

1. **Tool Chaining Works**: Tools can be chained together in journeys (create → send → status)
2. **State Persistence**: Tickets and escalations persist across tool calls via JSON files
3. **Error Handling**: All tools handle errors gracefully with informative messages
4. **Channel Formatting**: `send_response` properly formats per channel using ChannelAdaptationSkill
5. **Sentiment Recommendations**: `analyze_sentiment` provides actionable recommendations based on score

### Edge Cases in Tools:

| Edge Case | Tool | Handling |
|-----------|------|----------|
| Non-existent ticket | `get_ticket_status`, `escalate_to_human`, `send_response` | Returns helpful error message |
| Invalid priority/channel | `create_ticket` | Validates and returns error |
| No search results | `search_knowledge_base` | Returns helpful "no results" message |
| New customer | `get_customer_history` | Returns "No history found" message |
| Invalid urgency | `escalate_to_human` | Validates and returns error |

### Memory Files Created:

| File | Purpose | Initial State |
|------|---------|---------------|
| `memory/tickets.json` | Store support tickets | `[]` |
| `memory/escalations.json` | Store escalations | `[]` |

### Test Coverage:

| Test Category | Tests | Pass Rate |
|--------------|-------|-----------|
| MCP Tool Tests | 20 | 100% |
| Integration Journeys | 3 | 100% |
| **Total MCP Tests** | **23** | **100%** |

### Journey Tests Summary:

| Journey | Channel | Scenario | Result |
|---------|---------|----------|--------|
| Journey 1 | Email | Happy path resolution | ✅ Pass |
| Journey 2 | WhatsApp | Refund escalation | ✅ Pass |
| Journey 3 | Email + WhatsApp | Cross-channel support | ✅ Pass |

### Total Project Test Coverage:

| Component | Tests | Pass Rate |
|-----------|-------|-----------|
| Prototype Tests | 25 | 100% |
| Memory Tests | 24 | 100% |
| MCP Tests | 23 | 100% |
| **Grand Total** | **72** | **100%** |

### MCP Server Usage:

```python
# Example: Using MCP tools
from src.agent.mcp_server import (
    analyze_sentiment,
    create_ticket,
    send_response,
    get_ticket_status
)

# Analyze customer message
sentiment = analyze_sentiment("I need help with login")

# Create ticket
ticket = create_ticket(
    customer_id="user@example.com",
    issue="Cannot login",
    priority="medium",
    channel="email"
)

# Send response
send_response(
    ticket_id="TKT-ABC123",
    message="Here's how to reset your password...",
    channel="email"
)

# Check status
status = get_ticket_status("TKT-ABC123")
```

### Production Considerations:

1. **Real Channel Integration**: Replace simulated sending with real Gmail/Twilio APIs
2. **Database Backend**: Replace JSON files with PostgreSQL/MongoDB
3. **Authentication**: Add API key authentication for MCP server
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Logging**: Add structured logging for all tool calls
6. **Monitoring**: Track tool usage metrics and latency

---

## 11. Exercise 1.5 - Skills Manifest & Manager

### Skills Pipeline Order:

The skills execute in this specific order for every customer message:

```
1. customer_identification → 2. sentiment_analysis → 3. knowledge_retrieval 
                              ↓
4. escalation_decision → 5. channel_adaptation → Final Response
```

**Why this order:**

| Order | Skill | Rationale |
|-------|-------|-----------|
| 1 | **Customer Identification** | Must know WHO the customer is before accessing history or personalizing responses |
| 2 | **Sentiment Analysis** | Sentiment affects ALL downstream decisions (escalation threshold, response tone) |
| 3 | **Knowledge Retrieval** | Need relevant content before generating response |
| 4 | **Escalation Decision** | Must decide escalation BEFORE formatting (different responses for escalated tickets) |
| 5 | **Channel Adaptation** | Final formatting step before delivery to customer |

### Performance Measurements:

| Skill | Avg Response Time | Accuracy Rate |
|-------|-------------------|---------------|
| knowledge_retrieval | 0.67ms | 100% |
| sentiment_analysis | 0.07ms | 100% |
| escalation_decision | 0.04ms | 100% |
| channel_adaptation | 0.84ms | 100% |
| customer_identification | 0.05ms | 100% |

**Fastest skill:** escalation_decision (0.04ms)  
**Slowest skill:** channel_adaptation (0.84ms) - due to string formatting operations  
**Total pipeline time:** ~1.67ms (sum of all skills)

### Stage 1 Complete Summary:

| Metric | Count |
|--------|-------|
| **Total files created** | 20+ |
| **Total tests written** | 102 |
| **Total tests passing** | 102 (100%) |
| **Edge cases documented** | 12 |

### Files Created in Stage 1:

**Core Agent:**
- `src/agent/prototype.py` - Main agent implementation
- `src/agent/mcp_server.py` - MCP server with 7 tools
- `src/agent/memory.py` - Conversation memory system
- `src/agent/customer_db.py` - Customer database

**Skills:**
- `skills/knowledge_retrieval.py` - KB search
- `skills/sentiment_analysis.py` - Sentiment detection
- `skills/escalation_decision.py` - Escalation logic
- `skills/channel_adaptation.py` - Channel formatting
- `skills/customer_identification.py` - Customer lookup
- `skills/skills_manifest.json` - Skill definitions (NEW)
- `skills/skills_manager.py` - Pipeline manager (NEW)

**Channels:**
- `src/channels/email_channel.py`
- `src/channels/whatsapp_channel.py`
- `src/channels/web_form_channel.py`

**Tests:**
- `tests/test_prototype.py` - 25 tests
- `tests/test_memory.py` - 24 tests
- `tests/test_mcp_server.py` - 20 tests
- `tests/test_mcp_integration.py` - 3 journey tests
- `tests/test_skills_manager.py` - 30 tests (NEW)

**Specifications:**
- `specs/discovery-log.md` - This document
- `specs/customer-success-fte-spec.md` - Final spec (NEW)

**Context & Memory:**
- `context/*.md` - Provided context files
- `memory/*.json` - Persistent storage

### Final Incubation Checklist:

| Deliverable | Status |
|-------------|--------|
| ✅ Working prototype handling queries from any channel | Complete |
| ✅ Discovery log with all patterns documented | Complete |
| ✅ MCP server with 7 tools | Complete |
| ✅ All 5 agent skills defined and tested | Complete |
| ✅ Skills manifest created | Complete |
| ✅ Skills manager with pipeline working | Complete |
| ✅ Edge cases documented (minimum 10) | 12 documented |
| ✅ Escalation rules crystallized | Complete |
| ✅ Channel-specific response templates | Complete |
| ✅ Performance baseline measured | Complete |
| ✅ Final spec document created | Complete |
| ✅ All tests passing | 102/102 (100%) |

### GRAND TOTAL:

| Category | Count |
|----------|-------|
| **Total Tests** | 102 |
| **Pass Rate** | 100% |
| **Skills** | 5 |
| **MCP Tools** | 7 |
| **Channels** | 3 |
| **Edge Cases** | 12 |

---

**Stage 1 Status:** ✅ COMPLETE  
**Next Phase:** Stage 2 - Production Readiness