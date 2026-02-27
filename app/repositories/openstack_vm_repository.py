"""
OpenStack VM Repository

Real OpenStack SDK implementation for VM operations.
Connects to OpenStack DevStack or production deployment.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import openstack
from openstack.exceptions import (
    SDKException,
    ResourceNotFound,
    HttpException,
    ConflictException,
)

from app.config import settings
from app.exceptions import InvalidStateTransitionException
from app.models.vm import VMStatus, VMCreateRequest
from app.utils.helpers import get_datetime_now

logger = logging.getLogger(__name__)


class VM:
    """Internal VM representation matching OpenStack server"""

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
        openstack_id: Optional[str] = None,
    ):
        self.id = id
        self.name = name
        self.flavor = flavor
        self.image = image
        self.status = status
        self.ip_address = ip_address
        self.created_at = created_at
        self.updated_at = updated_at
        self.openstack_id = openstack_id or str(id)

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


class OpenStackVMRepository:
    """
    Repository for VM data access using real OpenStack SDK.

    Connects to OpenStack (DevStack or production) and manages VM lifecycle
    through Nova compute service.
    """

    # OpenStack status to application status mapping
    STATUS_MAP = {
        "ACTIVE": VMStatus.RUNNING,
        "SHUTOFF": VMStatus.STOPPED,
        "PAUSED": VMStatus.PAUSED,
        "ERROR": VMStatus.ERROR,
        "DELETED": VMStatus.DELETED,
        "BUILD": VMStatus.STOPPED,  # Building VM is not yet running
        "SUSPENDED": VMStatus.PAUSED,
    }

    def __init__(self):
        """Initialize OpenStack connection"""
        try:
            self.conn = openstack.connect(
                auth_url=settings.openstack_auth_url,
                project_name=settings.openstack_project_name,
                username=settings.openstack_username,
                password=settings.openstack_password,
                user_domain_name=settings.openstack_user_domain_name,
                project_domain_name=settings.openstack_project_domain_name,
                region_name=settings.openstack_region_name,
            )
            logger.info(
                f"Connected to OpenStack at {settings.openstack_auth_url} "
                f"(project: {settings.openstack_project_name})"
            )
        except Exception as e:
            logger.error(f"Failed to connect to OpenStack: {e}")
            raise RuntimeError(f"OpenStack connection failed: {e}")

    def _map_openstack_status(self, os_status: str) -> VMStatus:
        """Map OpenStack server status to application VMStatus"""
        status = self.STATUS_MAP.get(os_status.upper(), VMStatus.ERROR)
        logger.debug(f"Mapped OpenStack status '{os_status}' to '{status}'")
        return status

    def _get_server_ip(self, server) -> str:
        """Extract IP address from OpenStack server object"""
        # Try to get first available IP from any network
        if hasattr(server, "addresses") and server.addresses:
            for network_name, addresses in server.addresses.items():
                if addresses and len(addresses) > 0:
                    return addresses[0].get("addr", "N/A")
        return "N/A"

    def _find_network_id(self, network_name: str) -> str:
        """
        Find network ID by name.

        Args:
            network_name: Network name to look up

        Returns:
            Network UUID

        Raises:
            ValueError: If network not found
        """
        try:
            network = self.conn.network.find_network(network_name)
            if not network:
                raise ValueError(f"Network '{network_name}' not found in OpenStack")
            logger.debug(f"Resolved network '{network_name}' to ID: {network.id}")
            return network.id
        except SDKException as e:
            logger.error(f"Error finding network '{network_name}': {e}")
            raise ValueError(f"Failed to find network '{network_name}': {e}")

    def _server_to_vm(self, server) -> VM:
        """Convert OpenStack server to internal VM object"""
        try:
            vm_id = UUID(server.id) if isinstance(server.id, str) else server.id
        except (ValueError, TypeError):
            # If server.id is not a valid UUID, use a generated one
            from uuid import uuid4

            vm_id = uuid4()
            logger.warning(
                f"Server ID '{server.id}' is not a valid UUID, generated new: {vm_id}"
            )

        # Parse timestamps
        created_at = (
            server.created_at if hasattr(server, "created_at") else get_datetime_now()
        )
        updated_at = (
            server.updated_at if hasattr(server, "updated_at") else get_datetime_now()
        )

        # Handle string datetime from OpenStack
        if isinstance(created_at, str):
            from dateutil import parser  # type: ignore

            created_at = parser.parse(created_at)
        if isinstance(updated_at, str):
            from dateutil import parser  # type: ignore

            updated_at = parser.parse(updated_at)

        return VM(
            id=vm_id,
            name=server.name,
            flavor=(
                server.flavor.get("original_name", "unknown")
                if isinstance(server.flavor, dict)
                else str(server.flavor)
            ),
            image=(
                server.image.get("id", "unknown")
                if isinstance(server.image, dict)
                else str(server.image)
            ),
            status=self._map_openstack_status(server.status),
            ip_address=self._get_server_ip(server),
            created_at=created_at,
            updated_at=updated_at,
            openstack_id=server.id,
        )

    def create(self, request: VMCreateRequest) -> VM:
        """
        Create a new VM instance in OpenStack.

        Args:
            request: VM creation request

        Returns:
            Created VM instance

        Raises:
            RuntimeError: If creation fails
        """
        try:
            logger.info(
                f"Creating VM in OpenStack: name={request.name}, "
                f"flavor={request.flavor}, image={request.image}"
            )

            # Find flavor and image
            flavor = self.conn.compute.find_flavor(request.flavor.value)
            if not flavor:
                raise ValueError(f"Flavor '{request.flavor.value}' not found")

            image = self.conn.compute.find_image(request.image)
            if not image:
                raise ValueError(f"Image '{request.image}' not found")

            # Find network by name and get its UUID
            network_id = self._find_network_id(request.network)

            # Create server with resolved network ID
            server = self.conn.compute.create_server(
                name=request.name,
                image_id=image.id,
                flavor_id=flavor.id,
                networks=[{"uuid": network_id}],
            )

            # Wait for server to be created (optional, can be removed for async)
            server = self.conn.compute.wait_for_server(server, wait=60)

            vm = self._server_to_vm(server)
            logger.info(
                f"Created VM in OpenStack: id={vm.id}, openstack_id={server.id}"
            )
            return vm

        except (SDKException, ValueError) as e:
            logger.error(f"Failed to create VM in OpenStack: {e}")
            raise RuntimeError(f"OpenStack VM creation failed: {e}")

    def get_by_id(self, vm_id: UUID) -> Optional[VM]:
        """
        Retrieve VM by ID from OpenStack.

        Args:
            vm_id: VM unique identifier

        Returns:
            VM instance if found, None otherwise
        """
        try:
            server = self.conn.compute.get_server(str(vm_id))
            if server and server.status != "DELETED":
                return self._server_to_vm(server)
            return None
        except ResourceNotFound:
            logger.debug(f"VM not found in OpenStack: {vm_id}")
            return None
        except SDKException as e:
            logger.error(f"Error retrieving VM from OpenStack: {e}")
            return None

    def get_by_name(self, name: str) -> Optional[VM]:
        """
        Retrieve VM by name from OpenStack.

        Args:
            name: VM name

        Returns:
            VM instance if found, None otherwise
        """
        try:
            server = self.conn.compute.find_server(name)
            if server and server.status != "DELETED":
                return self._server_to_vm(server)
            return None
        except ResourceNotFound:
            logger.debug(f"VM not found in OpenStack: {name}")
            return None
        except SDKException as e:
            logger.error(f"Error retrieving VM from OpenStack: {e}")
            return None

    def list_all(self, status_filter: Optional[str] = None) -> List[VM]:
        """
        List all VMs from OpenStack, optionally filtered by status.

        Args:
            status_filter: Optional status to filter by

        Returns:
            List of VM instances
        """
        try:
            servers = self.conn.compute.servers()
            vms = []

            for server in servers:
                if server.status == "DELETED":
                    continue

                vm = self._server_to_vm(server)

                # Apply status filter if provided
                if status_filter:
                    if vm.status.value == status_filter.upper():
                        vms.append(vm)
                else:
                    vms.append(vm)

            logger.debug(
                f"Listed {len(vms)} VMs from OpenStack (filter: {status_filter})"
            )
            return vms

        except SDKException as e:
            logger.error(f"Error listing VMs from OpenStack: {e}")
            return []

    def update_status(self, vm_id: UUID, new_status: VMStatus) -> Optional[VM]:
        """
        Update VM status in OpenStack by performing the appropriate action.

        Args:
            vm_id: VM unique identifier
            new_status: New status to set

        Returns:
            Updated VM instance if found, None otherwise

        Raises:
            InvalidStateTransitionException: If transition is not allowed
        """
        old_status = (
            None  # Initialize to avoid undefined variable in exception handlers
        )
        try:
            server = self.conn.compute.get_server(str(vm_id))
            if not server:
                return None

            old_status = self._map_openstack_status(server.status)
            logger.info(f"Updating VM {vm_id} status: {old_status} -> {new_status}")

            # Perform the appropriate OpenStack action
            if new_status == VMStatus.RUNNING:
                if old_status == VMStatus.PAUSED:
                    self.conn.compute.unpause_server(server)
                elif old_status == VMStatus.STOPPED:
                    self.conn.compute.start_server(server)
            elif new_status == VMStatus.STOPPED:
                self.conn.compute.stop_server(server)
            elif new_status == VMStatus.PAUSED:
                self.conn.compute.pause_server(server)

            # Wait for status change
            server = self.conn.compute.wait_for_server(server, status="ACTIVE", wait=30)

            return self._server_to_vm(server)

        except ResourceNotFound:
            logger.warning(f"VM not found in OpenStack: {vm_id}")
            return None
        except (ConflictException, HttpException) as e:
            logger.error(f"Invalid state transition in OpenStack: {e}")
            # Use str() to convert status to string representation
            old_status_str = str(old_status) if old_status else "UNKNOWN"
            raise InvalidStateTransitionException(
                vm_id, old_status_str, str(new_status)
            )
        except SDKException as e:
            logger.error(f"Error updating VM status in OpenStack: {e}")
            raise RuntimeError(f"OpenStack status update failed: {e}")

    def delete(self, vm_id: UUID) -> bool:
        """
        Delete VM from OpenStack.

        Args:
            vm_id: VM unique identifier

        Returns:
            True if deleted, False if not found
        """
        try:
            server = self.conn.compute.get_server(str(vm_id))
            if not server:
                return False

            self.conn.compute.delete_server(server)
            logger.info(f"Deleted VM from OpenStack: id={vm_id}")
            return True

        except ResourceNotFound:
            logger.warning(f"VM not found in OpenStack: {vm_id}")
            return False
        except SDKException as e:
            logger.error(f"Error deleting VM from OpenStack: {e}")
            return False

    def count(self) -> int:
        """
        Count the total number of active VMs in OpenStack.

        Returns:
            Number of active VMs
        """
        try:
            servers = self.conn.compute.servers()
            count = sum(1 for s in servers if s.status != "DELETED")
            logger.debug(f"Total active VMs in OpenStack: {count}")
            return count
        except SDKException as e:
            logger.error(f"Error counting VMs in OpenStack: {e}")
            return 0
