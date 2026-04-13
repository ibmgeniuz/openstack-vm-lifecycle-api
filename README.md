# OpenStack VM Lifecycle Management API

[![CI Pipeline](https://github.com/ibmgeniuz/openstack-vm-lifecycle-api/actions/workflows/ci.yml/badge.svg)](https://github.com/ibmgeniuz/openstack-vm-lifecycle-api/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org)
[![Coverage](https://img.shields.io/badge/coverage-95.34%25-green)](#testing)

**Status:** ✅ **COMPLETE & PRODUCTION READY** | **Tests:** 53/53 Passed (>95% Coverage) | **Build:** CLEAN


A REST API for managing OpenStack virtual machine lifecycle operations, built with FastAPI as a proof-of-concept demonstrating API design, Python best practices, and software engineering principles.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Usage Examples](#usage-examples)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Technology Stack](#technology-stack)
- [Development](#development)
- [Future Enhancements](#future-enhancements)

## Overview

This project provides a comprehensive REST API for managing virtual machine lifecycle in an OpenStack environment. It implements core CRUD operations plus advanced lifecycle management (start, stop, restart, pause, resume) with proper state management and validation.

**Implementation Modes:**
- **Mock Mode** (default): In-memory storage for development and testing
- **Real OpenStack Mode**: Connect to DevStack or production OpenStack deployment

## Features

### Core Operations
- ✅ **Create VM** - Provision new virtual machine instances
- ✅ **List VMs** - Retrieve all VMs with pagination and filtering
- ✅ **Get VM Details** - Fetch specific VM information
- ✅ **Delete VM** - Remove VM instances

### Lifecycle Management
- ✅ **Start VM** - Boot stopped VMs
- ✅ **Stop VM** - Shutdown running or paused VMs
- ✅ **Restart VM** - Reboot running VMs
- ✅ **Pause VM** - Suspend running VMs to RAM
- ✅ **Resume VM** - Restore paused VMs to running state

### Additional Features
- ✅ **VM Status Check** - Query current VM state
- ✅ **Health Check** - API health monitoring endpoint
- ✅ **State Validation** - Enforces valid state transitions
- ✅ **Request Validation** - Pydantic-based input validation
- ✅ **Auto-generated Documentation** - Interactive Swagger/ReDoc UI
- ✅ **Comprehensive Error Handling** - Proper HTTP status codes

## Architecture

This project follows a **layered architecture** pattern:

```
Client → API Layer → Service Layer → Repository Layer → Data Layer
```

- **API Layer** (`app/routes/`) - FastAPI endpoints, request/response handling
- **Service Layer** (`app/services/`) - Business logic and validation
- **Repository Layer** (`app/repositories/`) - Data access and mock OpenStack integration
- **Model Layer** (`app/models/`) - Pydantic schemas and data structures

For detailed architecture information, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd intuitive-assessment
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# For mock mode (default): No changes needed
# For OpenStack mode: See "OpenStack Integration" section below
```

## OpenStack Integration

### Using Mock Mode (Default)

By default, the API uses an in-memory mock implementation. No additional configuration needed.

```bash
# .env file
USE_REAL_OPENSTACK=False
```

### Using Real OpenStack (DevStack or Production)

To connect to a real OpenStack deployment:

#### 1. Install OpenStack SDK

Already included in `requirements.txt`:
```bash
pip install openstacksdk
```

#### 2. Configure OpenStack Credentials

Edit your `.env` file with your OpenStack credentials:

```bash
# Enable real OpenStack mode
USE_REAL_OPENSTACK=True

# DevStack Configuration (typical local setup)
OPENSTACK_AUTH_URL=http://localhost/identity
OPENSTACK_USERNAME=admin
OPENSTACK_PASSWORD=devstack
OPENSTACK_PROJECT_NAME=demo
OPENSTACK_PROJECT_DOMAIN_NAME=Default
OPENSTACK_USER_DOMAIN_NAME=Default
OPENSTACK_REGION_NAME=RegionOne
```

**Note:** For DevStack, the default admin password is typically `devstack`. Check your DevStack configuration if different.

#### 3. Verify OpenStack Connection

Before starting the API, verify your OpenStack credentials work:

```bash
# Install OpenStack CLI (optional, for testing)
pip install python-openstackclient

# Find your DevStack identity endpoint (usually NOT localhost)
openstack endpoint list | grep identity
# Example output: http://192.168.2.110/identity

# Test connection (replace URL with your endpoint)
openstack --os-auth-url http://192.168.2.110/identity \
  --os-username admin \
  --os-password devstack \
  --os-project-name demo \
  --os-user-domain-name Default \
  --os-project-domain-name Default \
  server list

# Verify available resources
openstack network list    # Should show: private, public, shared
openstack image list      # Should show: cirros
openstack flavor list     # Should show: m1.tiny, m1.small, etc.
```

**Common DevStack URLs:**
- Identity API: `http://<devstack-ip>/identity`
- Compute API: `http://<devstack-ip>/compute/v2.1`
- Network API: `http://<devstack-ip>/networking`

**Note:** DevStack typically runs on the machine's IP address (e.g., `192.168.2.110`), not `localhost`.

#### 4. Start the API with OpenStack

```bash
uvicorn main:app --reload
```

The API will now create, manage, and delete real VMs in your OpenStack deployment.

### OpenStack Requirements

When using real OpenStack mode, ensure your OpenStack deployment has:
- **Flavors**: `m1.tiny`, `m1.small`, `m1.medium`, `m1.large`, `m1.xlarge` (or update flavor names in API calls)
- **Images**: At least one bootable image (e.g., `ubuntu-22.04`, `cirros`)
- **Networks**: At least one network configured for VM connectivity

### Switching Between Modes

You can switch between mock and real OpenStack by changing the `USE_REAL_OPENSTACK` environment variable:

```bash
# Switch to mock mode
USE_REAL_OPENSTACK=False

# Switch to real OpenStack
USE_REAL_OPENSTACK=True
```

Restart the API after changing this setting.

## Running the Application

### Start the API Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### Verify Installation

```bash
# Check health endpoint
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "v1",
  "timestamp": "2026-02-25T10:30:00Z"
}
```

## API Documentation

### Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Complete API Specification

For detailed endpoint documentation, see [API_SPECIFICATION.md](docs/API_SPECIFICATION.md).

## Usage Examples

### Create a VM

```bash
curl -X POST http://localhost:8000/api/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web-server-01",
    "flavor": "m1.tiny",
    "image": "cirros",
    "network": "private"
  }'
```

### List All VMs

```bash
# List all VMs
curl http://localhost:8000/api/v1/vms

# With pagination
curl http://localhost:8000/api/v1/vms?page=1&page_size=10

# Filter by status
curl http://localhost:8000/api/v1/vms?status=RUNNING
```

### Get VM Details

```bash
curl http://localhost:8000/api/v1/vms/{vm_id}
```

### VM Lifecycle Operations

```bash
# Start a VM
curl -X POST http://localhost:8000/api/v1/vms/{vm_id}/start

# Stop a VM
curl -X POST http://localhost:8000/api/v1/vms/{vm_id}/stop

# Restart a VM
curl -X POST http://localhost:8000/api/v1/vms/{vm_id}/restart

# Pause a VM
curl -X POST http://localhost:8000/api/v1/vms/{vm_id}/pause

# Resume a VM
curl -X POST http://localhost:8000/api/v1/vms/{vm_id}/resume
```

### Check VM Status

```bash
curl http://localhost:8000/api/v1/vms/{vm_id}/status
```

### Delete a VM

```bash
curl -X DELETE http://localhost:8000/api/v1/vms/{vm_id}
```

### Complete Workflow Example

```bash
# 1. Create a VM
VM_ID=$(curl -s -X POST http://localhost:8000/api/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"name":"test-vm","flavor":"m1.tiny","image":"cirros","network":"private"}' \
  | jq -r '.id')

echo "Created VM: $VM_ID"

# 2. Start the VM
curl -X POST http://localhost:8000/api/v1/vms/$VM_ID/start

# 3. Check status
curl http://localhost:8000/api/v1/vms/$VM_ID/status

# 4. Pause the VM
curl -X POST http://localhost:8000/api/v1/vms/$VM_ID/pause

# 5. Resume the VM
curl -X POST http://localhost:8000/api/v1/vms/$VM_ID/resume

# 6. Stop the VM
curl -X POST http://localhost:8000/api/v1/vms/$VM_ID/stop

# 7. Delete the VM
curl -X DELETE http://localhost:8000/api/v1/vms/$VM_ID
```

## Testing

The project includes comprehensive unit tests and optional integration tests for OpenStack.

### Test Types

**Unit Tests** (default):
- Use mock repository (no external dependencies)
- Fast execution (~0.3s)
- Run automatically in CI/CD
- **Coverage: ~90%**

**Integration Tests** (optional):
- Require real OpenStack connection
- Test actual OpenStack SDK integration
- Slower execution (~30s)
- Run manually with DevStack

### Run Unit Tests

```bash
# Run unit tests only (default behavior)
pytest

# Run with coverage report
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_vm_service.py -v

# Run specific test
pytest tests/test_vm_service.py::TestVMCreation::test_create_vm_success -v
```

### Run Integration Tests

Integration tests require a running OpenStack instance (DevStack):

```bash
# Run all tests including integration tests
USE_REAL_OPENSTACK=True pytest -m ""

# Run only integration tests
USE_REAL_OPENSTACK=True pytest -m integration -v

# Run integration tests with coverage
USE_REAL_OPENSTACK=True pytest -m "" --cov=app --cov-report=term
```

### View Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Open report in browser
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

### Test Structure

- `tests/test_vm_service.py` - Unit tests for business logic
- `tests/test_vm_routes.py` - API endpoint tests
- `tests/test_vm_repository_factory.py` - Factory pattern tests
- `tests/test_openstack_vm_repository.py` - OpenStack integration tests (requires DevStack)
- `tests/openstack_helpers.py` - Test utilities for OpenStack
- `tests/conftest.py` - Global test configuration

### Test Markers

Tests are marked for selective execution:

- `@pytest.mark.unit` - Fast unit tests (default)
- `@pytest.mark.integration` - Integration tests requiring OpenStack
- `@pytest.mark.slow` - Tests that take longer to execute

**Coverage Target: >85%** | **Current: ~90%** ✅

## Project Structure

```
intuitive-assessment/
├── app/
│   ├── __init__.py           # Application initialization
│   ├── models/
│   │   └── vm.py             # Pydantic data models
│   ├── services/
│   │   └── vm_service.py     # Business logic
│   ├── repositories/
│   │   └── vm_repository.py  # Data access layer
│   ├── routes/
│   │   └── vm_routes.py      # API endpoints
│   ├── config.py             # Configuration management
│   └── exceptions.py         # Custom exceptions
├── tests/
│   ├── __init__.py
│   ├── test_vm_service.py    # Service unit tests
│   └── test_vm_routes.py     # API integration tests
├── docs/
│   ├── PROJECT_PLAN.md       # Implementation roadmap
│   ├── ARCHITECTURE.md       # System architecture
│   ├── API_SPECIFICATION.md  # Complete API docs
│   ├── FEATURE_TRACKER.md    # Feature status tracking
│   └── BACKLOG.md            # Future enhancements
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## Documentation

Comprehensive documentation is available in the `/docs` directory:

| Document | Description |
|----------|-------------|
| [PROJECT_PLAN.md](docs/PROJECT_PLAN.md) | Complete project roadmap with timebox breakdown |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and design decisions |
| [API_SPECIFICATION.md](docs/API_SPECIFICATION.md) | Detailed API endpoint documentation |
| [FEATURE_TRACKER.md](docs/FEATURE_TRACKER.md) | Feature implementation status and checklist |
| [BACKLOG.md](docs/BACKLOG.md) | Future enhancements and roadmap |

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Web Framework | FastAPI | HTTP routing, validation, auto-docs |
| Web Server | Uvicorn | ASGI server |
| Data Validation | Pydantic v2 | Request/response validation |
| Testing | pytest | Unit and integration testing |
| HTTP Client | httpx | API testing |
| Configuration | python-dotenv | Environment management |
| Type Checking | mypy | Static type analysis |
| Code Formatting | black | Code style consistency |

## Development

### Code Quality

```bash
# Format code with black
black app/ tests/

# Type checking with mypy
mypy app/

# Run linter
flake8 app/ tests/
```

### Adding New Features

1. Define feature in `docs/FEATURE_TRACKER.md`
2. Create/update models in `app/models/`
3. Implement business logic in `app/services/`
4. Add repository methods in `app/repositories/`
5. Create API endpoints in `app/routes/`
6. Write tests in `tests/`
7. Update documentation

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

## VM Flavors

| Flavor | vCPUs | RAM | Description |
|--------|-------|-----|-------------|
| m1.tiny | 1 | 512 MB | Minimal instance |
| m1.small | 1 | 2 GB | Small workloads |
| m1.medium | 2 | 4 GB | General purpose |
| m1.large | 4 | 8 GB | Larger workloads |
| m1.xlarge | 8 | 16 GB | High-performance |

## VM Status Values

| Status | Description |
|--------|-------------|
| STOPPED | VM is shut down |
| RUNNING | VM is active and running |
| PAUSED | VM is paused (suspended to RAM) |
| DELETED | VM has been deleted |
| ERROR | VM is in error state |

## Future Enhancements

See [BACKLOG.md](docs/BACKLOG.md) for complete roadmap. Key items include:

- **Real OpenStack Integration** - Replace mock with actual SDK
- **Database Persistence** - PostgreSQL with SQLAlchemy
- **Authentication & Authorization** - OAuth2/JWT implementation
- **Containerization** - Docker and Docker Compose
- **CI/CD Pipeline** - GitHub Actions
- **Monitoring & Observability** - Prometheus, Grafana, Jaeger
- **Rate Limiting** - API throttling
- **Caching Layer** - Redis integration
- **Message Queue** - Async task processing with Celery

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# Use a different port
uvicorn main:app --reload --port 8001
```

### Module Not Found Errors

Ensure virtual environment is activated and dependencies are installed:

```bash
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### Tests Failing

Ensure you're in the project root directory:

```bash
# Run from project root
cd /path/to/intuitive-assessment
pytest
```

## License

This project is for assessment purposes.

## Contact

For questions or feedback, please open an issue in the repository.

---

## Development Methodology
This project was developed using a "Human-in-the-loop" AI approach. Claude (via PyCharm) was utilized to accelerate the generation of FastAPI boilerplate, Pydantic schemas, and Pytest scaffolding. All architectural decisions, core logic, and SDK integrations were manually reviewed, refactored, and validated to ensure compliance with the PFB requirements.

**Built with FastAPI** | **Version 1.0** | **Last Updated: 2026-02-25**
