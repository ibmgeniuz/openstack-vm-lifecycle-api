# API Specification

## Overview

**Base URL:** `http://localhost:8000`
**API Version:** `v1`
**API Prefix:** `/api/v1`

This document provides complete specification for all REST API endpoints in the OpenStack VM Lifecycle Management API.

## Authentication

**Current:** None (POC/Demo)
**Production:** OAuth2 with Bearer token

```http
Authorization: Bearer <token>
```

## Common Response Formats

### Success Response
```json
{
  "id": "uuid",
  "name": "string",
  "flavor": "string",
  "image": "string",
  "status": "RUNNING|STOPPED|PAUSED|DELETED|ERROR",
  "ip_address": "string",
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp"
}
```

### Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

### List Response
```json
{
  "items": [...],
  "total": 0,
  "page": 1,
  "page_size": 10
}
```

## HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request body or parameters |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Invalid state transition |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

---

## Endpoints

## 1. Health Check

### GET `/api/v1/health`

Check API health and status.

**Purpose:** Monitoring and readiness checks

**Request:**
```http
GET /api/v1/health HTTP/1.1
Host: localhost:8000
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "version": "v1",
  "timestamp": "2026-02-25T10:30:00Z"
}
```

**Errors:** None (always returns 200)

---

## 2. Create VM

### POST `/api/v1/vms`

Create a new virtual machine instance.

**Request Body:**
```json
{
  "name": "my-vm-instance",
  "flavor": "m1.small",
  "image": "ubuntu-22.04",
  "network": "default"
}
```

**Request Schema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | VM instance name (3-50 chars) |
| flavor | string | Yes | Instance type (m1.tiny, m1.small, m1.medium, m1.large, m1.xlarge) |
| image | string | Yes | OS image name |
| network | string | No | Network name (default: "default") |

**Response:** `201 Created`
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "name": "my-vm-instance",
  "flavor": "m1.small",
  "image": "ubuntu-22.04",
  "status": "STOPPED",
  "ip_address": "192.168.1.100",
  "created_at": "2026-02-25T10:30:00Z",
  "updated_at": "2026-02-25T10:30:00Z"
}
```

**Errors:**
- `400 Bad Request` - Invalid request body
- `422 Unprocessable Entity` - Validation error (name too short, invalid flavor)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/vms \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web-server-01",
    "flavor": "m1.medium",
    "image": "ubuntu-22.04"
  }'
```

---

## 3. List VMs

### GET `/api/v1/vms`

List all virtual machine instances with pagination.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number (1-indexed) |
| page_size | integer | 10 | Items per page (max: 100) |
| status | string | - | Filter by status (RUNNING, STOPPED, PAUSED) |

**Request:**
```http
GET /api/v1/vms?page=1&page_size=10 HTTP/1.1
Host: localhost:8000
```

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "name": "my-vm-instance",
      "flavor": "m1.small",
      "image": "ubuntu-22.04",
      "status": "RUNNING",
      "ip_address": "192.168.1.100",
      "created_at": "2026-02-25T10:30:00Z",
      "updated_at": "2026-02-25T10:35:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

**Errors:**
- `400 Bad Request` - Invalid query parameters

**Example:**
```bash
# List all VMs
curl http://localhost:8000/api/v1/vms

# Filter by status
curl http://localhost:8000/api/v1/vms?status=RUNNING

# Pagination
curl http://localhost:8000/api/v1/vms?page=2&page_size=20
```

---

## 4. Get VM Details

### GET `/api/v1/vms/{vm_id}`

Retrieve details of a specific virtual machine.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| vm_id | UUID | VM instance identifier |

**Request:**
```http
GET /api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479 HTTP/1.1
Host: localhost:8000
```

**Response:** `200 OK`
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "name": "my-vm-instance",
  "flavor": "m1.small",
  "image": "ubuntu-22.04",
  "status": "RUNNING",
  "ip_address": "192.168.1.100",
  "created_at": "2026-02-25T10:30:00Z",
  "updated_at": "2026-02-25T10:35:00Z"
}
```

**Errors:**
- `404 Not Found` - VM doesn't exist

**Example:**
```bash
curl http://localhost:8000/api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479
```

---

## 5. Get VM Status

### GET `/api/v1/vms/{vm_id}/status`

Get current status of a virtual machine.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| vm_id | UUID | VM instance identifier |

**Request:**
```http
GET /api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479/status HTTP/1.1
Host: localhost:8000
```

**Response:** `200 OK`
```json
{
  "vm_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "RUNNING",
  "updated_at": "2026-02-25T10:35:00Z"
}
```

**Errors:**
- `404 Not Found` - VM doesn't exist

**Example:**
```bash
curl http://localhost:8000/api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479/status
```

---

## 6. Start VM

### POST `/api/v1/vms/{vm_id}/start`

Start (boot) a stopped virtual machine.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| vm_id | UUID | VM instance identifier |

**Request:**
```http
POST /api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479/start HTTP/1.1
Host: localhost:8000
```

**Response:** `200 OK`
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "name": "my-vm-instance",
  "flavor": "m1.small",
  "image": "ubuntu-22.04",
  "status": "RUNNING",
  "ip_address": "192.168.1.100",
  "created_at": "2026-02-25T10:30:00Z",
  "updated_at": "2026-02-25T10:36:00Z"
}
```

**Errors:**
- `404 Not Found` - VM doesn't exist
- `409 Conflict` - VM is already running

**Valid State Transitions:**
- STOPPED → RUNNING ✅
- RUNNING → RUNNING ❌ (409 Conflict)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479/start
```

---

## 7. Stop VM

### POST `/api/v1/vms/{vm_id}/stop`

Stop (shutdown) a running or paused virtual machine.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| vm_id | UUID | VM instance identifier |

**Request:**
```http
POST /api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479/stop HTTP/1.1
Host: localhost:8000
```

**Response:** `200 OK`
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "name": "my-vm-instance",
  "flavor": "m1.small",
  "image": "ubuntu-22.04",
  "status": "STOPPED",
  "ip_address": "192.168.1.100",
  "created_at": "2026-02-25T10:30:00Z",
  "updated_at": "2026-02-25T10:37:00Z"
}
```

**Errors:**
- `404 Not Found` - VM doesn't exist
- `409 Conflict` - VM is already stopped

**Valid State Transitions:**
- RUNNING → STOPPED ✅
- PAUSED → STOPPED ✅
- STOPPED → STOPPED ❌ (409 Conflict)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479/stop
```

---

## 8. Restart VM

### POST `/api/v1/vms/{vm_id}/restart`

Restart (reboot) a running virtual machine.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| vm_id | UUID | VM instance identifier |

**Request:**
```http
POST /api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479/restart HTTP/1.1
Host: localhost:8000
```

**Response:** `200 OK`
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "name": "my-vm-instance",
  "flavor": "m1.small",
  "image": "ubuntu-22.04",
  "status": "RUNNING",
  "ip_address": "192.168.1.100",
  "created_at": "2026-02-25T10:30:00Z",
  "updated_at": "2026-02-25T10:38:00Z"
}
```

**Errors:**
- `404 Not Found` - VM doesn't exist
- `409 Conflict` - VM is not running

**Valid State Transitions:**
- RUNNING → RUNNING (reboots) ✅
- STOPPED → RUNNING ❌ (409 Conflict)
- PAUSED → RUNNING ❌ (409 Conflict)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479/restart
```

---

## 9. Pause VM

### POST `/api/v1/vms/{vm_id}/pause`

Pause a running virtual machine (suspend to RAM).

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| vm_id | UUID | VM instance identifier |

**Request:**
```http
POST /api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479/pause HTTP/1.1
Host: localhost:8000
```

**Response:** `200 OK`
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "name": "my-vm-instance",
  "flavor": "m1.small",
  "image": "ubuntu-22.04",
  "status": "PAUSED",
  "ip_address": "192.168.1.100",
  "created_at": "2026-02-25T10:30:00Z",
  "updated_at": "2026-02-25T10:39:00Z"
}
```

**Errors:**
- `404 Not Found` - VM doesn't exist
- `409 Conflict` - VM is not running

**Valid State Transitions:**
- RUNNING → PAUSED ✅
- STOPPED → PAUSED ❌ (409 Conflict)
- PAUSED → PAUSED ❌ (409 Conflict)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479/pause
```

---

## 10. Resume VM

### POST `/api/v1/vms/{vm_id}/resume`

Resume a paused virtual machine.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| vm_id | UUID | VM instance identifier |

**Request:**
```http
POST /api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479/resume HTTP/1.1
Host: localhost:8000
```

**Response:** `200 OK`
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "name": "my-vm-instance",
  "flavor": "m1.small",
  "image": "ubuntu-22.04",
  "status": "RUNNING",
  "ip_address": "192.168.1.100",
  "created_at": "2026-02-25T10:30:00Z",
  "updated_at": "2026-02-25T10:40:00Z"
}
```

**Errors:**
- `404 Not Found` - VM doesn't exist
- `409 Conflict` - VM is not paused

**Valid State Transitions:**
- PAUSED → RUNNING ✅
- RUNNING → RUNNING ❌ (409 Conflict)
- STOPPED → RUNNING ❌ (409 Conflict)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479/resume
```

---

## 11. Delete VM

### DELETE `/api/v1/vms/{vm_id}`

Delete a virtual machine instance.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| vm_id | UUID | VM instance identifier |

**Request:**
```http
DELETE /api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479 HTTP/1.1
Host: localhost:8000
```

**Response:** `204 No Content`

**Errors:**
- `404 Not Found` - VM doesn't exist

**Notes:**
- Can delete VM in any state (STOPPED, RUNNING, PAUSED)
- Operation is idempotent (deleting already deleted VM returns 404)

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/vms/f47ac10b-58cc-4372-a567-0e02b2c3d479
```

---

## VM Flavors Reference

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

## Complete Workflow Example

```bash
# 1. Create a VM
VM_ID=$(curl -s -X POST http://localhost:8000/api/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"name":"test-vm","flavor":"m1.small","image":"ubuntu-22.04"}' \
  | jq -r '.id')

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

## OpenAPI/Swagger Documentation

Interactive API documentation is automatically generated by FastAPI:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

---

**Last Updated:** 2026-02-25
**API Version:** v1
**Status:** Active Development
