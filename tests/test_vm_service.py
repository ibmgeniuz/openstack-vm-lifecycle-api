"""
Unit Tests for VM Service

Tests business logic and state transitions.
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from app.exceptions import (
    VMNotFoundException,
    InvalidStateTransitionException,
    VMAlreadyExistsException
)
from app.models.vm import VMStatus, VMFlavor, VMCreateRequest
from app.repositories.vm_repository import VMRepository, VM
from app.services.vm_service import VMService
from datetime import datetime


@pytest.fixture
def repository():
    """Create a fresh repository for each test"""
    return VMRepository()


@pytest.fixture
def service(repository):
    """Create a service with repository"""
    return VMService(repository)


@pytest.fixture
def sample_vm_request():
    """Sample VM creation request"""
    return VMCreateRequest(
        name="test-vm",
        flavor=VMFlavor.SMALL,
        image="ubuntu-22.04",
        network="default"
    )


class TestVMCreation:
    """Test VM creation"""

    def test_create_vm_success(self, service, sample_vm_request):
        """Test successful VM creation"""
        vm = service.create_vm(sample_vm_request)

        assert vm.name == "test-vm"
        assert vm.flavor == VMFlavor.SMALL.value
        assert vm.image == "ubuntu-22.04"
        assert vm.status == VMStatus.STOPPED
        assert vm.ip_address is not None
        assert vm.id is not None

    def test_create_vm_duplicate_name(self, service, sample_vm_request):
        """Test creating VM with duplicate name raises exception"""
        service.create_vm(sample_vm_request)

        with pytest.raises(VMAlreadyExistsException) as exc_info:
            service.create_vm(sample_vm_request)

        assert "test-vm" in str(exc_info.value)


class TestVMRetrieval:
    """Test VM retrieval"""

    def test_get_vm_success(self, service, sample_vm_request):
        """Test retrieving existing VM"""
        created = service.create_vm(sample_vm_request)
        retrieved = service.get_vm(created.id)

        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_vm_not_found(self, service):
        """Test retrieving non-existent VM raises exception"""
        fake_id = uuid4()

        with pytest.raises(VMNotFoundException) as exc_info:
            service.get_vm(fake_id)

        assert str(fake_id) in str(exc_info.value)

    def test_list_vms_empty(self, service):
        """Test listing VMs when none exist"""
        result = service.list_vms()

        assert result.total == 0
        assert len(result.items) == 0

    def test_list_vms_with_items(self, service, sample_vm_request):
        """Test listing VMs"""
        service.create_vm(sample_vm_request)

        request2 = VMCreateRequest(
            name="test-vm-2",
            flavor=VMFlavor.MEDIUM,
            image="centos-8"
        )
        service.create_vm(request2)

        result = service.list_vms()

        assert result.total == 2
        assert len(result.items) == 2

    def test_list_vms_pagination(self, service, sample_vm_request):
        """Test VM list pagination"""
        # Create 5 VMs
        for i in range(5):
            request = VMCreateRequest(
                name=f"test-vm-{i}",
                flavor=VMFlavor.SMALL,
                image="ubuntu-22.04"
            )
            service.create_vm(request)

        # Page 1, size 2
        page1 = service.list_vms(page=1, page_size=2)
        assert len(page1.items) == 2
        assert page1.total == 5

        # Page 2, size 2
        page2 = service.list_vms(page=2, page_size=2)
        assert len(page2.items) == 2

        # Page 3, size 2
        page3 = service.list_vms(page=3, page_size=2)
        assert len(page3.items) == 1

    def test_list_vms_with_status_filter(self, service, sample_vm_request):
        """Test filtering VMs by status"""
        vm1 = service.create_vm(sample_vm_request)

        request2 = VMCreateRequest(
            name="test-vm-2",
            flavor=VMFlavor.MEDIUM,
            image="centos-8"
        )
        vm2 = service.create_vm(request2)

        # Start one VM
        service.start_vm(vm1.id)

        # Filter by RUNNING
        running_vms = service.list_vms(status_filter="RUNNING")
        assert running_vms.total == 1
        assert running_vms.items[0].id == vm1.id

        # Filter by STOPPED
        stopped_vms = service.list_vms(status_filter="STOPPED")
        assert stopped_vms.total == 1
        assert stopped_vms.items[0].id == vm2.id


class TestVMLifecycle:
    """Test VM lifecycle operations"""

    def test_start_vm_success(self, service, sample_vm_request):
        """Test starting a stopped VM"""
        vm = service.create_vm(sample_vm_request)
        assert vm.status == VMStatus.STOPPED

        started_vm = service.start_vm(vm.id)
        assert started_vm.status == VMStatus.RUNNING

    def test_start_running_vm_fails(self, service, sample_vm_request):
        """Test starting an already running VM raises exception"""
        vm = service.create_vm(sample_vm_request)
        service.start_vm(vm.id)

        with pytest.raises(InvalidStateTransitionException) as exc_info:
            service.start_vm(vm.id)

        assert "start" in str(exc_info.value).lower()
        assert "running" in str(exc_info.value).lower()

    def test_stop_vm_success(self, service, sample_vm_request):
        """Test stopping a running VM"""
        vm = service.create_vm(sample_vm_request)
        service.start_vm(vm.id)

        stopped_vm = service.stop_vm(vm.id)
        assert stopped_vm.status == VMStatus.STOPPED

    def test_stop_stopped_vm_fails(self, service, sample_vm_request):
        """Test stopping an already stopped VM raises exception"""
        vm = service.create_vm(sample_vm_request)

        with pytest.raises(InvalidStateTransitionException):
            service.stop_vm(vm.id)

    def test_restart_vm_success(self, service, sample_vm_request):
        """Test restarting a running VM"""
        vm = service.create_vm(sample_vm_request)
        service.start_vm(vm.id)

        restarted_vm = service.restart_vm(vm.id)
        assert restarted_vm.status == VMStatus.RUNNING

    def test_restart_stopped_vm_fails(self, service, sample_vm_request):
        """Test restarting a stopped VM raises exception"""
        vm = service.create_vm(sample_vm_request)

        with pytest.raises(InvalidStateTransitionException) as exc_info:
            service.restart_vm(vm.id)

        assert "restart" in str(exc_info.value).lower()

    def test_pause_vm_success(self, service, sample_vm_request):
        """Test pausing a running VM"""
        vm = service.create_vm(sample_vm_request)
        service.start_vm(vm.id)

        paused_vm = service.pause_vm(vm.id)
        assert paused_vm.status == VMStatus.PAUSED

    def test_pause_stopped_vm_fails(self, service, sample_vm_request):
        """Test pausing a stopped VM raises exception"""
        vm = service.create_vm(sample_vm_request)

        with pytest.raises(InvalidStateTransitionException):
            service.pause_vm(vm.id)

    def test_resume_vm_success(self, service, sample_vm_request):
        """Test resuming a paused VM"""
        vm = service.create_vm(sample_vm_request)
        service.start_vm(vm.id)
        service.pause_vm(vm.id)

        resumed_vm = service.resume_vm(vm.id)
        assert resumed_vm.status == VMStatus.RUNNING

    def test_resume_running_vm_fails(self, service, sample_vm_request):
        """Test resuming a running VM raises exception"""
        vm = service.create_vm(sample_vm_request)
        service.start_vm(vm.id)

        with pytest.raises(InvalidStateTransitionException):
            service.resume_vm(vm.id)

    def test_stop_paused_vm_success(self, service, sample_vm_request):
        """Test stopping a paused VM"""
        vm = service.create_vm(sample_vm_request)
        service.start_vm(vm.id)
        service.pause_vm(vm.id)

        stopped_vm = service.stop_vm(vm.id)
        assert stopped_vm.status == VMStatus.STOPPED


class TestVMDeletion:
    """Test VM deletion"""

    def test_delete_vm_success(self, service, sample_vm_request):
        """Test deleting a VM"""
        vm = service.create_vm(sample_vm_request)

        service.delete_vm(vm.id)

        with pytest.raises(VMNotFoundException):
            service.get_vm(vm.id)

    def test_delete_nonexistent_vm_fails(self, service):
        """Test deleting non-existent VM raises exception"""
        fake_id = uuid4()

        with pytest.raises(VMNotFoundException):
            service.delete_vm(fake_id)

    def test_delete_running_vm(self, service, sample_vm_request):
        """Test deleting a running VM (should be allowed)"""
        vm = service.create_vm(sample_vm_request)
        service.start_vm(vm.id)

        service.delete_vm(vm.id)

        with pytest.raises(VMNotFoundException):
            service.get_vm(vm.id)


class TestVMStatus:
    """Test VM status operations"""

    def test_get_vm_status_success(self, service, sample_vm_request):
        """Test getting VM status"""
        vm = service.create_vm(sample_vm_request)

        status = service.get_vm_status(vm.id)

        assert status.vm_id == vm.id
        assert status.status == VMStatus.STOPPED
        assert status.updated_at is not None

    def test_get_status_nonexistent_vm_fails(self, service):
        """Test getting status of non-existent VM raises exception"""
        fake_id = uuid4()

        with pytest.raises(VMNotFoundException):
            service.get_vm_status(fake_id)


class TestCompleteWorkflow:
    """Test complete VM lifecycle workflows"""

    def test_full_lifecycle_workflow(self, service, sample_vm_request):
        """Test complete VM lifecycle: create -> start -> pause -> resume -> stop -> delete"""
        # Create
        vm = service.create_vm(sample_vm_request)
        assert vm.status == VMStatus.STOPPED

        # Start
        vm = service.start_vm(vm.id)
        assert vm.status == VMStatus.RUNNING

        # Pause
        vm = service.pause_vm(vm.id)
        assert vm.status == VMStatus.PAUSED

        # Resume
        vm = service.resume_vm(vm.id)
        assert vm.status == VMStatus.RUNNING

        # Stop
        vm = service.stop_vm(vm.id)
        assert vm.status == VMStatus.STOPPED

        # Delete
        service.delete_vm(vm.id)
        with pytest.raises(VMNotFoundException):
            service.get_vm(vm.id)

    def test_restart_workflow(self, service, sample_vm_request):
        """Test restart workflow"""
        vm = service.create_vm(sample_vm_request)

        # Start then restart
        service.start_vm(vm.id)
        restarted_vm = service.restart_vm(vm.id)

        assert restarted_vm.status == VMStatus.RUNNING
