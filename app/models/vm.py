"""
VM Data Models

Pydantic models for VM operations including requests, responses, and enums.
"""

from datetime import datetime
from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class VMStatus(str, Enum):
    """VM status enumeration"""

    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DELETED = "DELETED"
    ERROR = "ERROR"


class VMFlavor(str, Enum):
    """VM flavor (instance type) enumeration"""

    TINY = "m1.tiny"  # 1 vCPU, 512 MB RAM
    SMALL = "m1.small"  # 1 vCPU, 2 GB RAM
    MEDIUM = "m1.medium"  # 2 vCPU, 4 GB RAM
    LARGE = "m1.large"  # 4 vCPU, 8 GB RAM
    XLARGE = "m1.xlarge"  # 8 vCPU, 16 GB RAM


class VMCreateRequest(BaseModel):
    """Request model for creating a new VM"""

    name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="VM instance name",
        examples=["web-server-01"],
    )
    flavor: VMFlavor = Field(
        ..., description="Instance type/flavor", examples=["m1.medium"]
    )
    image: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="OS image name",
        examples=["ubuntu-22.04"],
    )
    network: str = Field(
        default="private",
        description="Network name",
        examples=["private", "public", "shared"],
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate VM name contains only allowed characters"""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "VM name must contain only alphanumeric characters, hyphens, and underscores"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "web-server-01",
                "flavor": "m1.tiny",
                "image": "cirros",
                "network": "private",
            }
        }
    }


class VMResponse(BaseModel):
    """Response model for VM operations"""

    id: UUID = Field(..., description="VM unique identifier")
    name: str = Field(..., description="VM instance name")
    flavor: str = Field(..., description="Instance type/flavor")
    image: str = Field(..., description="OS image name")
    status: VMStatus = Field(..., description="Current VM status")
    ip_address: str = Field(..., description="Assigned IP address")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "name": "web-server-01",
                "flavor": "m1.tiny",
                "image": "cirros",
                "status": "RUNNING",
                "ip_address": "192.168.1.100",
                "created_at": "2026-02-25T10:30:00Z",
                "updated_at": "2026-02-25T10:35:00Z",
            }
        }
    }


class VMListResponse(BaseModel):
    """Response model for listing VMs with pagination"""

    items: List[VMResponse] = Field(..., description="List of VMs")
    total: int = Field(..., description="Total number of VMs")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {
                        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                        "name": "web-server-01",
                        "flavor": "m1.tiny",
                        "image": "cirros",
                        "status": "RUNNING",
                        "ip_address": "192.168.1.100",
                        "created_at": "2026-02-25T10:30:00Z",
                        "updated_at": "2026-02-25T10:35:00Z",
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10,
            }
        }
    }


class VMStatusResponse(BaseModel):
    """Response model for VM status check"""

    vm_id: UUID = Field(..., description="VM unique identifier")
    status: VMStatus = Field(..., description="Current VM status")
    updated_at: datetime = Field(..., description="Last status update timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "vm_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "status": "RUNNING",
                "updated_at": "2026-02-25T10:35:00Z",
            }
        }
    }


class HealthResponse(BaseModel):
    """Response model for health check"""

    status: str = Field(..., description="API health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current server timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "v1",
                "timestamp": "2026-02-25T10:30:00Z",
            }
        }
    }
