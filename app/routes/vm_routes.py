"""
VM API Routes

FastAPI endpoints for VM lifecycle management.
"""

import logging
from typing import Optional, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status, Depends

from app.config import settings
from app.exceptions import (
    VMNotFoundException,
    InvalidStateTransitionException,
    VMAlreadyExistsException,
    VMException,
)
from app.models.vm import (
    VMCreateRequest,
    VMResponse,
    VMListResponse,
    VMStatusResponse,
    HealthResponse,
)
from app.repositories.vm_repository_factory import get_vm_repository
from app.services.vm_service import VMService
from app.utils.helpers import get_datetime_now

logger = logging.getLogger(__name__)

# Create router with API versioning
router = APIRouter(
    prefix=f"/api/{settings.api_version}", tags=["VM Lifecycle Management"]
)

# Dependency injection for service
# Repository is created via factory (mock or real OpenStack based on config)
_repository: Optional[Any] = None
_service: Optional[VMService] = None


def get_vm_service() -> VMService:
    """
    Dependency to get VM service instance.

    Creates repository via factory pattern - will use mock or real OpenStack
    based on USE_REAL_OPENSTACK configuration.
    """
    global _repository, _service
    if _service is None:
        _repository = get_vm_repository()
        _service = VMService(_repository)
        logger.info(f"VM Service initialized with {type(_repository).__name__}")
    return _service


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check API health and status",
)
async def health_check():
    """API health check endpoint"""
    return HealthResponse(
        status="healthy", version=settings.api_version, timestamp=get_datetime_now()
    )


@router.post(
    "/vms",
    response_model=VMResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create VM",
    description="Create a new virtual machine instance",
)
async def create_vm(
    request: VMCreateRequest, service: VMService = Depends(get_vm_service)
):
    """
    Create a new VM instance.

    Args:
        request: VM creation request
        service: VM service (injected)

    Returns:
        Created VM details

    Raises:
        HTTPException: 409 if VM with same name exists, 400 for validation errors
    """
    try:
        vm = service.create_vm(request)
        logger.info(f"API: Created VM {vm.id}")
        return vm
    except VMAlreadyExistsException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except VMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error creating VM: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/vms",
    response_model=VMListResponse,
    status_code=status.HTTP_200_OK,
    summary="List VMs",
    description="List all virtual machines with pagination and filtering",
)
async def list_vms(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(
        None, description="Filter by status (RUNNING, STOPPED, PAUSED)"
    ),
    service: VMService = Depends(get_vm_service),
):
    """
    List all VMs with pagination.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        status: Optional status filter
        service: VM service (injected)

    Returns:
        Paginated list of VMs
    """
    try:
        vms = service.list_vms(page=page, page_size=page_size, status_filter=status)
        logger.info(f"API: Listed VMs (page={page}, total={vms.total})")
        return vms
    except Exception as e:
        logger.error(f"Unexpected error listing VMs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/vms/{vm_id}",
    response_model=VMResponse,
    status_code=status.HTTP_200_OK,
    summary="Get VM Details",
    description="Retrieve details of a specific virtual machine",
)
async def get_vm(vm_id: UUID, service: VMService = Depends(get_vm_service)):
    """
    Get VM details by ID.

    Args:
        vm_id: VM unique identifier
        service: VM service (injected)

    Returns:
        VM details

    Raises:
        HTTPException: 404 if VM not found
    """
    try:
        vm = service.get_vm(vm_id)
        logger.info(f"API: Retrieved VM {vm_id}")
        return vm
    except VMNotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error retrieving VM: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/vms/{vm_id}/status",
    response_model=VMStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get VM Status",
    description="Get current status of a virtual machine",
)
async def get_vm_status(vm_id: UUID, service: VMService = Depends(get_vm_service)):
    """
    Get VM status.

    Args:
        vm_id: VM unique identifier
        service: VM service (injected)

    Returns:
        VM status details

    Raises:
        HTTPException: 404 if VM not found
    """
    try:
        status_info = service.get_vm_status(vm_id)
        logger.info(f"API: Retrieved status for VM {vm_id}")
        return status_info
    except VMNotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error retrieving VM status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/vms/{vm_id}/start",
    response_model=VMResponse,
    status_code=status.HTTP_200_OK,
    summary="Start VM",
    description="Start (boot) a stopped virtual machine",
)
async def start_vm(vm_id: UUID, service: VMService = Depends(get_vm_service)):
    """
    Start a VM.

    Args:
        vm_id: VM unique identifier
        service: VM service (injected)

    Returns:
        Updated VM details

    Raises:
        HTTPException: 404 if VM not found, 409 if invalid state transition
    """
    try:
        vm = service.start_vm(vm_id)
        logger.info(f"API: Started VM {vm_id}")
        return vm
    except (VMNotFoundException, InvalidStateTransitionException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error starting VM: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/vms/{vm_id}/stop",
    response_model=VMResponse,
    status_code=status.HTTP_200_OK,
    summary="Stop VM",
    description="Stop (shutdown) a running or paused virtual machine",
)
async def stop_vm(vm_id: UUID, service: VMService = Depends(get_vm_service)):
    """
    Stop a VM.

    Args:
        vm_id: VM unique identifier
        service: VM service (injected)

    Returns:
        Updated VM details

    Raises:
        HTTPException: 404 if VM not found, 409 if invalid state transition
    """
    try:
        vm = service.stop_vm(vm_id)
        logger.info(f"API: Stopped VM {vm_id}")
        return vm
    except (VMNotFoundException, InvalidStateTransitionException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error stopping VM: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/vms/{vm_id}/restart",
    response_model=VMResponse,
    status_code=status.HTTP_200_OK,
    summary="Restart VM",
    description="Restart (reboot) a running virtual machine",
)
async def restart_vm(vm_id: UUID, service: VMService = Depends(get_vm_service)):
    """
    Restart a VM.

    Args:
        vm_id: VM unique identifier
        service: VM service (injected)

    Returns:
        Updated VM details

    Raises:
        HTTPException: 404 if VM not found, 409 if invalid state transition
    """
    try:
        vm = service.restart_vm(vm_id)
        logger.info(f"API: Restarted VM {vm_id}")
        return vm
    except (VMNotFoundException, InvalidStateTransitionException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error restarting VM: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/vms/{vm_id}/pause",
    response_model=VMResponse,
    status_code=status.HTTP_200_OK,
    summary="Pause VM",
    description="Pause a running virtual machine (suspend to RAM)",
)
async def pause_vm(vm_id: UUID, service: VMService = Depends(get_vm_service)):
    """
    Pause a VM.

    Args:
        vm_id: VM unique identifier
        service: VM service (injected)

    Returns:
        Updated VM details

    Raises:
        HTTPException: 404 if VM not found, 409 if invalid state transition
    """
    try:
        vm = service.pause_vm(vm_id)
        logger.info(f"API: Paused VM {vm_id}")
        return vm
    except (VMNotFoundException, InvalidStateTransitionException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error pausing VM: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/vms/{vm_id}/resume",
    response_model=VMResponse,
    status_code=status.HTTP_200_OK,
    summary="Resume VM",
    description="Resume a paused virtual machine",
)
async def resume_vm(vm_id: UUID, service: VMService = Depends(get_vm_service)):
    """
    Resume a paused VM.

    Args:
        vm_id: VM unique identifier
        service: VM service (injected)

    Returns:
        Updated VM details

    Raises:
        HTTPException: 404 if VM not found, 409 if invalid state transition
    """
    try:
        vm = service.resume_vm(vm_id)
        logger.info(f"API: Resumed VM {vm_id}")
        return vm
    except (VMNotFoundException, InvalidStateTransitionException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error resuming VM: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/vms/{vm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete VM",
    description="Delete a virtual machine instance",
)
async def delete_vm(vm_id: UUID, service: VMService = Depends(get_vm_service)):
    """
    Delete a VM.

    Args:
        vm_id: VM unique identifier
        service: VM service (injected)

    Raises:
        HTTPException: 404 if VM not found
    """
    try:
        service.delete_vm(vm_id)
        logger.info(f"API: Deleted VM {vm_id}")
        return None
    except VMNotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error deleting VM: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
