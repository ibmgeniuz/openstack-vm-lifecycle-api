# Architecture & Design Documentation

## System Overview

This project implements a REST API for OpenStack VM lifecycle management using a layered architecture pattern. The system is designed as a proof-of-concept that demonstrates API design, Python best practices, and software engineering principles.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│            (HTTP Clients, Browsers, CLI Tools)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Routes (vm_routes.py)                                │  │
│  │  - Request validation (Pydantic)                      │  │
│  │  - Response formatting                                 │  │
│  │  - HTTP status codes                                   │  │
│  │  - OpenAPI documentation                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  VM Service (vm_service.py)                           │  │
│  │  - Business logic                                      │  │
│  │  - Validation rules                                    │  │
│  │  - State transition logic                              │  │
│  │  - Error handling                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Repository Layer                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  VM Repository (vm_repository.py)                     │  │
│  │  - Data access abstraction                            │  │
│  │  - Mock OpenStack SDK integration                     │  │
│  │  - CRUD operations                                     │  │
│  │  - State management                                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  In-Memory Storage (Python Dict)                      │  │
│  │  - Mock VM instances                                   │  │
│  │  - UUID-based indexing                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Layered Architecture

### 1. API Layer (`app/routes/`)
**Responsibility:** HTTP request/response handling

- Defines REST endpoints
- Validates incoming requests using Pydantic models
- Formats responses with proper HTTP status codes
- Handles API versioning (`/api/v1/`)
- Auto-generates OpenAPI/Swagger documentation

**Technologies:**
- FastAPI for routing and dependency injection
- Pydantic for request/response validation

### 2. Service Layer (`app/services/`)
**Responsibility:** Business logic and orchestration

- Implements business rules and workflows
- Validates state transitions (e.g., can't stop a paused VM)
- Coordinates between repositories
- Handles complex operations
- Throws custom exceptions for error cases

**Pattern:** Service Pattern / Business Logic Layer

### 3. Repository Layer (`app/repositories/`)
**Responsibility:** Data access and external service integration

- Abstracts data persistence and retrieval
- Mock implementation of OpenStack SDK
- Manages VM lifecycle states
- Provides CRUD operations
- Would connect to real OpenStack API in production

**Pattern:** Repository Pattern

### 4. Model Layer (`app/models/`)
**Responsibility:** Data structures and validation

- Pydantic schemas for request/response
- Enums for VM states and flavors
- Type definitions
- Data validation rules

**Pattern:** DTO (Data Transfer Objects)

## Design Decisions

### 1. FastAPI Framework Choice

**Decision:** Use FastAPI as the web framework

**Rationale:**
- **Modern & Fast:** Async support, high performance
- **Auto Documentation:** OpenAPI/Swagger docs generated automatically
- **Type Safety:** Built-in Pydantic validation
- **Developer Experience:** Excellent error messages and debugging
- **Industry Standard:** Widely adopted for Python APIs

**Alternatives Considered:**
- Flask: More mature but lacks async and auto-docs
- Django REST Framework: Too heavy for this use case

### 2. Mock OpenStack Integration

**Decision:** Implement mock OpenStack service instead of real integration

**Rationale:**
- **Time Constraint:** Real OpenStack requires infrastructure setup
- **Portability:** Anyone can run the demo without OpenStack access
- **Focus:** Demonstrates API design rather than SDK integration
- **Testing:** Easier to test and validate logic

**Production Path:**
- Replace mock repository with real `openstacksdk` client
- Configuration for OpenStack credentials
- Connection pooling and retry logic

### 3. In-Memory Storage

**Decision:** Use Python dictionary for VM storage

**Rationale:**
- **Simplicity:** No database setup required
- **Timebox:** Faster development within 2-4 hours
- **Proof-of-Concept:** Sufficient for demonstration
- **Stateless:** Resets on restart (acceptable for demo)

**Production Path:**
- PostgreSQL or MySQL for persistence
- Redis for caching
- Database migrations with Alembic

### 4. Layered Architecture Pattern

**Decision:** Separate routes, services, and repositories

**Rationale:**
- **Separation of Concerns:** Each layer has single responsibility
- **Testability:** Easy to unit test each layer independently
- **Maintainability:** Changes in one layer don't affect others
- **Scalability:** Can add features without major refactoring

### 5. API Versioning Strategy

**Decision:** URL-based versioning (`/api/v1/`)

**Rationale:**
- **Explicit:** Version is clear in URL
- **Backwards Compatibility:** Can run v1 and v2 simultaneously
- **Industry Standard:** Common pattern in REST APIs
- **Easy Routing:** FastAPI prefix makes this trivial

**Alternatives Considered:**
- Header-based versioning: Less visible to users
- Query parameter versioning: Not RESTful

### 6. Error Handling Strategy

**Decision:** Custom exception classes with HTTP exception mapping

**Rationale:**
- **Consistency:** All errors follow same format
- **Type Safety:** Specific exception types
- **HTTP Standards:** Proper status codes (404, 400, 409, 500)
- **Debugging:** Clear error messages with context

### 7. Synchronous Implementation

**Decision:** Use async/await patterns throughout

**Rationale:**
- **FastAPI Native:** Framework is async-first
- **Scalability:** Non-blocking I/O for concurrent requests
- **Future-Proof:** Real OpenStack SDK calls would be async
- **Best Practice:** Modern Python API development

## VM Lifecycle State Machine

```
                    ┌──────────┐
                    │  CREATE  │
                    └────┬─────┘
                         │
                         ▼
                    ┌─────────┐
              ┌────▶│ STOPPED │◀────┐
              │     └────┬────┘     │
              │          │          │
            STOP       START      RESTART
              │          │          │
              │     ┌────▼────┐     │
              └─────│ RUNNING │─────┘
                    └────┬────┘
                         │
                    PAUSE│   ▲RESUME
                         │   │
                    ┌────▼───┴┐
                    │  PAUSED │
                    └─────────┘
                         │
                      DELETE
                         │
                         ▼
                    ┌─────────┐
                    │ DELETED │
                    └─────────┘
```

### Valid State Transitions

| Current State | Allowed Actions | Next State |
|---------------|----------------|------------|
| STOPPED       | start          | RUNNING    |
| STOPPED       | delete         | DELETED    |
| RUNNING       | stop           | STOPPED    |
| RUNNING       | restart        | RUNNING    |
| RUNNING       | pause          | PAUSED     |
| RUNNING       | delete         | DELETED    |
| PAUSED        | resume         | RUNNING    |
| PAUSED        | stop           | STOPPED    |
| PAUSED        | delete         | DELETED    |

### Invalid Transitions

- Cannot start a RUNNING VM
- Cannot pause a STOPPED VM
- Cannot resume a RUNNING VM
- Cannot perform any action on DELETED VM

## Data Models

### VM Instance Schema

```python
{
  "id": "uuid-string",
  "name": "my-vm-instance",
  "flavor": "m1.small",
  "image": "ubuntu-22.04",
  "status": "RUNNING",
  "ip_address": "192.168.1.100",
  "created_at": "2026-02-25T10:30:00Z",
  "updated_at": "2026-02-25T10:35:00Z"
}
```

### VM Flavors (Instance Types)

- `m1.tiny` - 1 vCPU, 512 MB RAM
- `m1.small` - 1 vCPU, 2 GB RAM
- `m1.medium` - 2 vCPU, 4 GB RAM
- `m1.large` - 4 vCPU, 8 GB RAM
- `m1.xlarge` - 8 vCPU, 16 GB RAM

### VM Status Enum

```python
class VMStatus(str, Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DELETED = "DELETED"
    ERROR = "ERROR"
```

## Security Considerations

### Current Implementation (POC)
- No authentication or authorization
- No input sanitization beyond Pydantic validation
- No rate limiting
- No API key management

### Production Requirements
- **Authentication:** OAuth2 with JWT tokens
- **Authorization:** Role-based access control (RBAC)
- **Input Validation:** SQL injection prevention, XSS protection
- **Rate Limiting:** Per-user API throttling
- **Audit Logging:** Track all VM operations
- **TLS/HTTPS:** Encrypted communication
- **Secret Management:** Vault for OpenStack credentials

## Performance Considerations

### Current Implementation
- In-memory storage (fast but not scalable)
- Synchronous operations
- No caching layer
- Single-threaded execution

### Production Optimizations
- **Database Connection Pooling:** Reuse connections
- **Redis Caching:** Cache VM status queries
- **Async I/O:** Non-blocking OpenStack API calls
- **Pagination:** Limit result set sizes
- **Background Tasks:** Queue long-running operations (Celery)
- **Load Balancing:** Horizontal scaling with multiple instances

## Scalability Path

### Vertical Scaling
- Increase server resources (CPU, RAM)
- Optimize database queries
- Add connection pooling

### Horizontal Scaling
- Deploy multiple API instances
- Load balancer (NGINX, HAProxy)
- Shared Redis cache
- Centralized database

### Microservices Evolution
```
API Gateway
    ├── VM Management Service (this service)
    ├── Storage Management Service
    ├── Network Management Service
    └── Billing Service
```

## Testing Strategy

### Unit Tests
- Service layer logic
- State transition validation
- Error handling
- Model validation

### Integration Tests
- Full API endpoint testing
- End-to-end workflows
- Error scenario testing

### Test Coverage Target
- Minimum: 80%
- Goal: 90%+

## Configuration Management

### Environment Variables
```
API_VERSION=v1
LOG_LEVEL=INFO
OPENSTACK_AUTH_URL=http://example.com:5000/v3
OPENSTACK_USERNAME=admin
OPENSTACK_PASSWORD=secret
OPENSTACK_PROJECT=demo
```

### Configuration Files
- `.env` - Local development (gitignored)
- `.env.example` - Template for users
- `app/config.py` - Configuration loading

## Logging Strategy

### Log Levels
- **DEBUG:** Detailed information for debugging
- **INFO:** General application flow
- **WARNING:** Warning messages (deprecated features)
- **ERROR:** Error events that might still allow the app to continue
- **CRITICAL:** Serious errors causing app to abort

### Log Format
```json
{
  "timestamp": "2026-02-25T10:30:00Z",
  "level": "INFO",
  "message": "VM created successfully",
  "vm_id": "uuid-string",
  "user": "admin",
  "endpoint": "POST /api/v1/vms"
}
```

## Monitoring & Observability (Future)

- **Metrics:** Prometheus for API metrics
- **Tracing:** Jaeger for distributed tracing
- **Logging:** ELK stack or Loki
- **APM:** Application Performance Monitoring
- **Health Checks:** Kubernetes liveness/readiness probes

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API Framework | FastAPI | HTTP routing, validation |
| Web Server | Uvicorn | ASGI server |
| Validation | Pydantic v2 | Data validation |
| Testing | pytest | Unit/integration tests |
| HTTP Client | httpx | Testing FastAPI |
| Configuration | python-dotenv | Environment management |
| Type Checking | mypy | Static type analysis |
| Code Formatting | black | Code style |

## Future Architecture Enhancements

See **BACKLOG.md** for detailed roadmap:

1. **Real OpenStack Integration** - Replace mock with SDK
2. **Database Layer** - PostgreSQL with SQLAlchemy
3. **Caching Layer** - Redis for performance
4. **Message Queue** - RabbitMQ/Kafka for async tasks
5. **API Gateway** - Kong or Tyk for advanced features
6. **Container Orchestration** - Kubernetes deployment
7. **Service Mesh** - Istio for microservices
8. **GraphQL API** - Alternative to REST

---

**Last Updated:** 2026-02-25
**Version:** 1.0
**Status:** Active Development
