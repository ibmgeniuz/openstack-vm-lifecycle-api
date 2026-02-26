"""
VM Service

Business logic layer for VM operations including state transition validation.
"""

import logging
from typing import Optional
from uuid import UUID

from app.exceptions import (
    VMNotFoundException,
    InvalidStateTransitionException,
    VMAlreadyExistsException,
)
from app.models.vm import (
    VMStatus,
    VMCreateRequest,
    VMResponse,
    VMListResponse,
    VMStatusResponse,
)
from app.repositories.vm_repository import VMRepository

logger = logging.getLogger(__name__)


class VMService:
    """
    Service for VM business logic.

    Handles validation, state transitions, and orchestration of VM operations.
    """

    def __init__(self, repository: VMRepository):
        """
        Initialize VM service.

        Args:
            repository: VM repository instance
        """
        self.repository = repository
        logger.info("VMService initialized")

    def create_vm(self, request: VMCreateRequest) -> VMResponse:
        """
        Create a new VM instance.

        Args:
            request: VM creation request

        Returns:
            Created VM details

        Raises:
            VMAlreadyExistsException: If VM with same name exists
        """
        # Check if VM with same name already exists
        existing_vm = self.repository.get_by_name(request.name)
        if existing_vm:
            logger.warning(f"Attempt to create VM with duplicate name: {request.name}")
            raise VMAlreadyExistsException(request.name)

        vm = self.repository.create(request)
        logger.info(f"VM created successfully: {vm.id}")
        return VMResponse(**vm.to_dict())

    def get_vm(self, vm_id: UUID) -> VMResponse:
        """
        Get VM details by ID.

        Args:
            vm_id: VM unique identifier

        Returns:
            VM details

        Raises:
            VMNotFoundException: If VM not found
        """
        vm = self.repository.get_by_id(vm_id)
        if not vm:
            logger.warning(f"VM not found: {vm_id}")
            raise VMNotFoundException(vm_id)

        return VMResponse(**vm.to_dict())

    def list_vms(
        self, page: int = 1, page_size: int = 10, status_filter: Optional[str] = None
    ) -> VMListResponse:
        """
        List all VMs with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            status_filter: Optional status to filter by

        Returns:
            Paginated list of VMs
        """
        all_vms = self.repository.list_all(status_filter=status_filter)
        total = len(all_vms)

        # Calculate pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_vms = all_vms[start_idx:end_idx]

        vm_responses = [VMResponse(**vm.to_dict()) for vm in page_vms]

        logger.info(f"Listed {len(vm_responses)} VMs (page={page}, total={total})")
        return VMListResponse(
            items=vm_responses, total=total, page=page, page_size=page_size
        )

    def start_vm(self, vm_id: UUID) -> VMResponse:
        """
        Start (boot) a VM.

        Args:
            vm_id: VM unique identifier

        Returns:
            Updated VM details

        Raises:
            VMNotFoundException: If VM not found
            InvalidStateTransitionException: If VM is not in STOPPED state
        """
        vm = self.repository.get_by_id(vm_id)
        if not vm:
            raise VMNotFoundException(vm_id)

        if vm.status != VMStatus.STOPPED:
            logger.warning(
                f"Invalid state transition: Cannot start VM {vm_id} in state {vm.status}"
            )
            raise InvalidStateTransitionException(vm_id, str(vm.status), "start")

        updated_vm = self.repository.update_status(vm_id, VMStatus.RUNNING)
        assert updated_vm is not None, f"VM {vm_id} should exist after status check"
        logger.info(f"VM started successfully: {vm_id}")
        return VMResponse(**updated_vm.to_dict())

    def stop_vm(self, vm_id: UUID) -> VMResponse:
        """
        Stop (shutdown) a VM.

        Args:
            vm_id: VM unique identifier

        Returns:
            Updated VM details

        Raises:
            VMNotFoundException: If VM not found
            InvalidStateTransitionException: If VM is already stopped
        """
        vm = self.repository.get_by_id(vm_id)
        if not vm:
            raise VMNotFoundException(vm_id)

        if vm.status == VMStatus.STOPPED:
            logger.warning(f"Invalid state transition: VM {vm_id} already stopped")
            raise InvalidStateTransitionException(vm_id, str(vm.status), "stop")

        if vm.status not in [VMStatus.RUNNING, VMStatus.PAUSED]:
            logger.warning(
                f"Invalid state transition: Cannot stop VM {vm_id} in state {vm.status}"
            )
            raise InvalidStateTransitionException(vm_id, str(vm.status), "stop")

        updated_vm = self.repository.update_status(vm_id, VMStatus.STOPPED)
        assert updated_vm is not None, f"VM {vm_id} should exist after status check"
        logger.info(f"VM stopped successfully: {vm_id}")
        return VMResponse(**updated_vm.to_dict())

    def restart_vm(self, vm_id: UUID) -> VMResponse:
        """
        Restart (reboot) a VM.

        Args:
            vm_id: VM unique identifier

        Returns:
            Updated VM details

        Raises:
            VMNotFoundException: If VM not found
            InvalidStateTransitionException: If VM is not running
        """
        vm = self.repository.get_by_id(vm_id)
        if not vm:
            raise VMNotFoundException(vm_id)

        if vm.status != VMStatus.RUNNING:
            logger.warning(
                f"Invalid state transition: Cannot restart VM {vm_id} in state {vm.status}"
            )
            raise InvalidStateTransitionException(vm_id, str(vm.status), "restart")

        # Restart keeps the status as RUNNING but updates the timestamp
        updated_vm = self.repository.update_status(vm_id, VMStatus.RUNNING)
        assert updated_vm is not None, f"VM {vm_id} should exist after status check"
        logger.info(f"VM restarted successfully: {vm_id}")
        return VMResponse(**updated_vm.to_dict())

    def pause_vm(self, vm_id: UUID) -> VMResponse:
        """
        Pause a VM (suspend to RAM).

        Args:
            vm_id: VM unique identifier

        Returns:
            Updated VM details

        Raises:
            VMNotFoundException: If VM not found
            InvalidStateTransitionException: If VM is not running
        """
        vm = self.repository.get_by_id(vm_id)
        if not vm:
            raise VMNotFoundException(vm_id)

        if vm.status != VMStatus.RUNNING:
            logger.warning(
                f"Invalid state transition: Cannot pause VM {vm_id} in state {vm.status}"
            )
            raise InvalidStateTransitionException(vm_id, str(vm.status), "pause")

        updated_vm = self.repository.update_status(vm_id, VMStatus.PAUSED)
        assert updated_vm is not None, f"VM {vm_id} should exist after status check"
        logger.info(f"VM paused successfully: {vm_id}")
        return VMResponse(**updated_vm.to_dict())

    def resume_vm(self, vm_id: UUID) -> VMResponse:
        """
        Resume a paused VM.

        Args:
            vm_id: VM unique identifier

        Returns:
            Updated VM details

        Raises:
            VMNotFoundException: If VM not found
            InvalidStateTransitionException: If VM is not paused
        """
        vm = self.repository.get_by_id(vm_id)
        if not vm:
            raise VMNotFoundException(vm_id)

        if vm.status != VMStatus.PAUSED:
            logger.warning(
                f"Invalid state transition: Cannot resume VM {vm_id} in state {vm.status}"
            )
            raise InvalidStateTransitionException(vm_id, str(vm.status), "resume")

        updated_vm = self.repository.update_status(vm_id, VMStatus.RUNNING)
        assert updated_vm is not None, f"VM {vm_id} should exist after status check"
        logger.info(f"VM resumed successfully: {vm_id}")
        return VMResponse(**updated_vm.to_dict())

    def delete_vm(self, vm_id: UUID) -> None:
        """
        Delete a VM.

        Args:
            vm_id: VM unique identifier

        Raises:
            VMNotFoundException: If VM not found
        """
        vm = self.repository.get_by_id(vm_id)
        if not vm:
            raise VMNotFoundException(vm_id)

        self.repository.delete(vm_id)
        logger.info(f"VM deleted successfully: {vm_id}")

    def get_vm_status(self, vm_id: UUID) -> VMStatusResponse:
        """
        Get VM status.

        Args:
            vm_id: VM unique identifier

        Returns:
            VM status details

        Raises:
            VMNotFoundException: If VM not found
        """
        vm = self.repository.get_by_id(vm_id)
        if not vm:
            raise VMNotFoundException(vm_id)

        return VMStatusResponse(vm_id=vm.id, status=vm.status, updated_at=vm.updated_at)
