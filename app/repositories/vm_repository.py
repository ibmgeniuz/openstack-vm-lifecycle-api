"""
VM Repository

Data access layer for VM operations with mock OpenStack integration.
In production, this would interface with the real OpenStack SDK.
"""

import logging
import random
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from app.models.vm import VMStatus, VMCreateRequest
from app.utils.helpers import get_datetime_now

logger = logging.getLogger(__name__)


class VM:
    """Internal VM representation"""

    def __init__(
        self,
        id: UUID,
        name: str,
        flavor: str,
        image: str,
        status: VMStatus,
        ip_address: str,
        created_at: datetime,
        updated_at: datetime,
    ):
        self.id = id
        self.name = name
        self.flavor = flavor
        self.image = image
        self.status = status
        self.ip_address = ip_address
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        """Convert VM to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "flavor": self.flavor,
            "image": self.image,
            "status": self.status,
            "ip_address": self.ip_address,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class VMRepository:
    """
    Repository for VM data access.

    Mock implementation using in-memory storage.
    In production, this would use OpenStack SDK.
    """

    def __init__(self):
        """Initialize the repository with in-memory storage"""
        self._storage: Dict[UUID, VM] = {}
        self._name_index: Dict[str, UUID] = {}
        logger.info("VMRepository initialized with in-memory storage")

    @staticmethod
    def _generate_ip_address() -> str:
        """Generate a random IP address for demo purposes"""
        return f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"

    def create(self, request: VMCreateRequest) -> VM:
        """
        Create a new VM instance.

        Args:
            request: VM creation request

        Returns:
            Created VM instance
        """
        vm_id = uuid4()
        now = get_datetime_now()

        vm = VM(
            id=vm_id,
            name=request.name,
            flavor=request.flavor.value,
            image=request.image,
            status=VMStatus.STOPPED,  # New VMs start in STOPPED state
            ip_address=self._generate_ip_address(),
            created_at=now,
            updated_at=now,
        )

        self._storage[vm_id] = vm
        self._name_index[request.name] = vm_id

        logger.info(
            f"Created VM: id={vm_id}, name={request.name}, flavor={request.flavor}"
        )
        return vm

    def get_by_id(self, vm_id: UUID) -> Optional[VM]:
        """
        Retrieve VM by ID.

        Args:
            vm_id: VM unique identifier

        Returns:
            VM instance if found, None otherwise
        """
        vm = self._storage.get(vm_id)
        if vm and vm.status != VMStatus.DELETED:
            return vm
        return None

    def get_by_name(self, name: str) -> Optional[VM]:
        """
        Retrieve VM by name.

        Args:
            name: VM name

        Returns:
            VM instance if found, None otherwise
        """
        vm_id = self._name_index.get(name)
        if vm_id:
            return self.get_by_id(vm_id)
        return None

    def list_all(self, status_filter: Optional[str] = None) -> List[VM]:
        """
        List all VMs, optionally filtered by status.

        Args:
            status_filter: Optional status to filter by

        Returns:
            List of VM instances
        """
        vms = [vm for vm in self._storage.values() if vm.status != VMStatus.DELETED]

        if status_filter:
            vms = [vm for vm in vms if vm.status.value == status_filter.upper()]

        logger.debug(f"Listed {len(vms)} VMs (filter: {status_filter})")
        return vms

    def update_status(self, vm_id: UUID, new_status: VMStatus) -> Optional[VM]:
        """
        Update VM status.

        Args:
            vm_id: VM unique identifier
            new_status: New status to set

        Returns:
            Updated VM instance if found, None otherwise
        """
        vm = self.get_by_id(vm_id)
        if vm:
            old_status = vm.status
            vm.status = new_status
            vm.updated_at = get_datetime_now()
            logger.info(f"Updated VM {vm_id} status: {old_status} -> {new_status}")
            return vm
        return None

    def delete(self, vm_id: UUID) -> bool:
        """
        Delete VM (mark as deleted).

        Args:
            vm_id: VM unique identifier

        Returns:
            True if deleted, False if not found
        """
        vm = self.get_by_id(vm_id)
        if vm:
            vm.status = VMStatus.DELETED
            vm.updated_at = get_datetime_now()
            # Remove from name index
            if vm.name in self._name_index:
                del self._name_index[vm.name]
            logger.info(f"Deleted VM: id={vm_id}, name={vm.name}")
            return True
        return False

    def count(self) -> int:
        """
        Count the total number of non-deleted VMs.

        Returns:
            Number of active VMs
        """
        return len(
            [vm for vm in self._storage.values() if vm.status != VMStatus.DELETED]
        )
