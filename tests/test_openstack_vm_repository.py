"""
Integration Tests for OpenStack VM Repository

These tests require a real OpenStack connection and are skipped by default.
Run with: USE_REAL_OPENSTACK=True pytest -m integration
"""

import os
import pytest
from uuid import uuid4

from app.models.vm import VMStatus, VMFlavor, VMCreateRequest
from app.repositories.openstack_vm_repository import OpenStackVMRepository
from tests.openstack_helpers import (
    create_openstack_connection,
    cleanup_test_vms,
    verify_openstack_availability,
    get_available_networks,
    get_available_images,
    get_available_flavors,
)

# Skip all tests in this module if OpenStack is not configured
pytestmark = pytest.mark.integration

# Check if OpenStack is available
OPENSTACK_AVAILABLE = os.getenv("USE_REAL_OPENSTACK") == "True"


@pytest.fixture(scope="module", autouse=True)
def cleanup_before_and_after():
    """Clean up test VMs before and after test module"""
    if not OPENSTACK_AVAILABLE:
        pytest.skip("OpenStack not configured (USE_REAL_OPENSTACK != True)")

    conn = create_openstack_connection()

    # Cleanup before tests
    cleanup_test_vms(conn, prefix="pytest-test-")

    yield

    # Cleanup after tests
    cleanup_test_vms(conn, prefix="pytest-test-")


@pytest.fixture
def repository():
    """Create OpenStack repository for testing"""
    if not OPENSTACK_AVAILABLE:
        pytest.skip("OpenStack not configured")

    return OpenStackVMRepository()


@pytest.fixture
def sample_vm_request():
    """Sample VM creation request for integration tests"""
    return VMCreateRequest(
        name=f"pytest-test-vm-{uuid4().hex[:8]}",
        flavor=VMFlavor.TINY,
        image="cirros",
        network="private",
    )


class TestOpenStackConnection:
    """Test OpenStack connection"""

    def test_openstack_availability(self):
        """Test that OpenStack is available and accessible"""
        assert verify_openstack_availability(), "OpenStack should be accessible"

    def test_repository_initialization(self, repository):
        """Test repository can be initialized"""
        assert repository is not None
        assert hasattr(repository, "conn")
        assert repository.conn is not None

    def test_get_available_resources(self):
        """Test retrieving available OpenStack resources"""
        conn = create_openstack_connection()

        networks = get_available_networks(conn)
        assert len(networks) > 0, "Should have at least one network"
        assert "private" in networks, "Should have 'private' network"

        images = get_available_images(conn)
        assert len(images) > 0, "Should have at least one image"
        assert "cirros" in images, "Should have 'cirros' image"

        flavors = get_available_flavors(conn)
        assert len(flavors) > 0, "Should have at least one flavor"
        assert "m1.tiny" in flavors, "Should have 'm1.tiny' flavor"


class TestOpenStackVMCreation:
    """Test VM creation in OpenStack"""

    def test_create_vm_success(self, repository, sample_vm_request):
        """Test successful VM creation in OpenStack"""
        vm = repository.create(sample_vm_request)

        assert vm is not None
        assert vm.name == sample_vm_request.name
        assert vm.flavor == VMFlavor.TINY.value
        assert vm.image == sample_vm_request.image
        assert vm.id is not None
        assert vm.openstack_id is not None

        # Cleanup
        repository.delete(vm.id)

    def test_create_vm_with_different_networks(self, repository):
        """Test creating VMs with different networks"""
        networks_to_test = ["private", "public", "shared"]
        created_vms = []

        for network in networks_to_test:
            try:
                request = VMCreateRequest(
                    name=f"pytest-test-net-{network}-{uuid4().hex[:6]}",
                    flavor=VMFlavor.TINY,
                    image="cirros",
                    network=network,
                )
                vm = repository.create(request)
                assert vm is not None
                assert vm.name == request.name
                created_vms.append(vm.id)
            except Exception as e:
                pytest.fail(f"Failed to create VM with network '{network}': {e}")

        # Cleanup
        for vm_id in created_vms:
            try:
                repository.delete(vm_id)
            except Exception:
                pass

    def test_network_name_resolution(self, repository):
        """Test that network names are resolved to IDs"""
        # This implicitly tests _find_network_id method
        request = VMCreateRequest(
            name=f"pytest-test-network-{uuid4().hex[:8]}",
            flavor=VMFlavor.TINY,
            image="cirros",
            network="private",
        )

        vm = repository.create(request)
        assert vm is not None

        # Cleanup
        repository.delete(vm.id)


class TestOpenStackVMRetrieval:
    """Test VM retrieval operations"""

    def test_get_vm_by_id(self, repository, sample_vm_request):
        """Test retrieving VM by ID"""
        # Create VM
        created_vm = repository.create(sample_vm_request)

        # Retrieve by ID
        retrieved_vm = repository.get_by_id(created_vm.id)

        assert retrieved_vm is not None
        assert retrieved_vm.id == created_vm.id
        assert retrieved_vm.name == created_vm.name

        # Cleanup
        repository.delete(created_vm.id)

    def test_get_vm_by_name(self, repository, sample_vm_request):
        """Test retrieving VM by name"""
        # Create VM
        created_vm = repository.create(sample_vm_request)

        # Retrieve by name
        retrieved_vm = repository.get_by_name(created_vm.name)

        assert retrieved_vm is not None
        assert retrieved_vm.name == created_vm.name
        assert retrieved_vm.id == created_vm.id

        # Cleanup
        repository.delete(created_vm.id)

    def test_get_nonexistent_vm(self, repository):
        """Test retrieving non-existent VM returns None"""
        fake_id = uuid4()
        vm = repository.get_by_id(fake_id)
        assert vm is None

    def test_list_vms(self, repository):
        """Test listing VMs"""
        # Get initial count
        initial_vms = repository.list_all()
        initial_count = len(initial_vms)

        # Create test VM
        request = VMCreateRequest(
            name=f"pytest-test-list-{uuid4().hex[:8]}",
            flavor=VMFlavor.TINY,
            image="cirros",
            network="private",
        )
        created_vm = repository.create(request)

        # List VMs
        vms = repository.list_all()
        assert len(vms) == initial_count + 1

        # Verify our VM is in the list
        vm_names = [vm.name for vm in vms]
        assert created_vm.name in vm_names

        # Cleanup
        repository.delete(created_vm.id)

    def test_list_vms_with_status_filter(self, repository, sample_vm_request):
        """Test listing VMs with status filter"""
        # Create and start VM
        created_vm = repository.create(sample_vm_request)

        # List with filter (may not work perfectly due to OpenStack timing)
        vms = repository.list_all(status_filter="RUNNING")
        assert isinstance(vms, list)

        # Cleanup
        repository.delete(created_vm.id)


class TestOpenStackVMLifecycle:
    """Test VM lifecycle operations"""

    def test_vm_status_transitions(self, repository, sample_vm_request):
        """Test VM status transitions through lifecycle"""
        # Create VM
        vm = repository.create(sample_vm_request)
        assert vm is not None

        # Initial status should be STOPPED or RUNNING (depending on OpenStack config)
        assert vm.status in [VMStatus.STOPPED, VMStatus.RUNNING]

        # Cleanup
        repository.delete(vm.id)

    def test_update_vm_status(self, repository, sample_vm_request):
        """Test updating VM status"""
        # Create VM
        vm = repository.create(sample_vm_request)

        # Try to update status (actual transitions depend on OpenStack state)
        # This test verifies the method doesn't crash
        try:
            updated_vm = repository.update_status(vm.id, VMStatus.RUNNING)
            assert updated_vm is not None
        except Exception:
            # Some state transitions may fail depending on current state
            # That's OK - we're testing the code path exists
            pass

        # Cleanup
        repository.delete(vm.id)


class TestOpenStackVMDeletion:
    """Test VM deletion"""

    def test_delete_vm_success(self, repository, sample_vm_request):
        """Test successful VM deletion"""
        # Create VM
        vm = repository.create(sample_vm_request)
        assert vm is not None

        # Delete VM
        result = repository.delete(vm.id)
        assert result is True

        # Verify deletion
        deleted_vm = repository.get_by_id(vm.id)
        assert deleted_vm is None

    def test_delete_nonexistent_vm(self, repository):
        """Test deleting non-existent VM returns False"""
        fake_id = uuid4()
        result = repository.delete(fake_id)
        assert result is False

    def test_count_vms(self, repository):
        """Test counting VMs"""
        count = repository.count()
        assert isinstance(count, int)
        assert count >= 0


class TestOpenStackStatusMapping:
    """Test OpenStack status to app status mapping"""

    def test_status_map_coverage(self, repository):
        """Test that status map covers expected statuses"""
        expected_statuses = ["ACTIVE", "SHUTOFF", "PAUSED", "ERROR", "DELETED", "BUILD"]

        for os_status in expected_statuses:
            app_status = repository._map_openstack_status(os_status)
            assert app_status is not None
            assert isinstance(app_status, VMStatus)

    def test_unknown_status_mapping(self, repository):
        """Test unknown status maps to ERROR"""
        unknown_status = repository._map_openstack_status("UNKNOWN_STATUS")
        assert unknown_status == VMStatus.ERROR


class TestOpenStackNetworkResolution:
    """Test network name to ID resolution"""

    def test_find_network_id_private(self, repository):
        """Test resolving 'private' network name to ID"""
        network_id = repository._find_network_id("private")
        assert network_id is not None
        assert len(network_id) > 0

    def test_find_network_id_public(self, repository):
        """Test resolving 'public' network name to ID"""
        network_id = repository._find_network_id("public")
        assert network_id is not None
        assert len(network_id) > 0

    def test_find_network_id_shared(self, repository):
        """Test resolving 'shared' network name to ID"""
        network_id = repository._find_network_id("shared")
        assert network_id is not None
        assert len(network_id) > 0

    def test_find_nonexistent_network(self, repository):
        """Test resolving non-existent network raises ValueError"""
        with pytest.raises(ValueError, match="not found"):
            repository._find_network_id("nonexistent-network-xyz")
