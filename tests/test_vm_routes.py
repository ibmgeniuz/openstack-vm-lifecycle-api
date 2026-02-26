"""
Integration Tests for VM API Routes

Tests complete API endpoints end-to-end.
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from main import app
from app.routes.vm_routes import _repository


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_repository():
    """Clear repository before each test"""
    _repository._storage.clear()
    _repository._name_index.clear()
    yield


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self):
        """Test health endpoint returns healthy status"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "v1"
        assert "timestamp" in data


class TestCreateVM:
    """Test VM creation endpoint"""

    def test_create_vm_success(self):
        """Test successful VM creation"""
        payload = {
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        }

        response = client.post("/api/v1/vms", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-vm"
        assert data["flavor"] == "m1.small"
        assert data["status"] == "STOPPED"
        assert "id" in data
        assert "ip_address" in data

    def test_create_vm_duplicate_name(self):
        """Test creating VM with duplicate name fails"""
        payload = {
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        }

        # Create first VM
        response1 = client.post("/api/v1/vms", json=payload)
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = client.post("/api/v1/vms", json=payload)
        assert response2.status_code == 409

    def test_create_vm_invalid_name(self):
        """Test creating VM with invalid name fails"""
        payload = {
            "name": "ab",  # Too short
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        }

        response = client.post("/api/v1/vms", json=payload)
        assert response.status_code == 422

    def test_create_vm_invalid_flavor(self):
        """Test creating VM with invalid flavor fails"""
        payload = {
            "name": "test-vm",
            "flavor": "invalid-flavor",
            "image": "ubuntu-22.04"
        }

        response = client.post("/api/v1/vms", json=payload)
        assert response.status_code == 422


class TestListVMs:
    """Test VM listing endpoint"""

    def test_list_vms_empty(self):
        """Test listing VMs when none exist"""
        response = client.get("/api/v1/vms")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_vms_with_items(self):
        """Test listing multiple VMs"""
        # Create 3 VMs
        for i in range(3):
            payload = {
                "name": f"test-vm-{i}",
                "flavor": "m1.small",
                "image": "ubuntu-22.04"
            }
            client.post("/api/v1/vms", json=payload)

        response = client.get("/api/v1/vms")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_vms_pagination(self):
        """Test VM listing pagination"""
        # Create 5 VMs
        for i in range(5):
            payload = {
                "name": f"test-vm-{i}",
                "flavor": "m1.small",
                "image": "ubuntu-22.04"
            }
            client.post("/api/v1/vms", json=payload)

        # Page 1, size 2
        response = client.get("/api/v1/vms?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1

    def test_list_vms_with_status_filter(self):
        """Test filtering VMs by status"""
        # Create 2 VMs
        response1 = client.post("/api/v1/vms", json={
            "name": "vm-1",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        })
        vm1_id = response1.json()["id"]

        client.post("/api/v1/vms", json={
            "name": "vm-2",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        })

        # Start one VM
        client.post(f"/api/v1/vms/{vm1_id}/start")

        # Filter by RUNNING
        response = client.get("/api/v1/vms?status=RUNNING")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


class TestGetVM:
    """Test get VM endpoint"""

    def test_get_vm_success(self):
        """Test retrieving existing VM"""
        # Create VM
        create_response = client.post("/api/v1/vms", json={
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        })
        vm_id = create_response.json()["id"]

        # Get VM
        response = client.get(f"/api/v1/vms/{vm_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == vm_id
        assert data["name"] == "test-vm"

    def test_get_vm_not_found(self):
        """Test retrieving non-existent VM"""
        fake_id = str(uuid4())

        response = client.get(f"/api/v1/vms/{fake_id}")

        assert response.status_code == 404


class TestGetVMStatus:
    """Test get VM status endpoint"""

    def test_get_status_success(self):
        """Test getting VM status"""
        # Create VM
        create_response = client.post("/api/v1/vms", json={
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        })
        vm_id = create_response.json()["id"]

        # Get status
        response = client.get(f"/api/v1/vms/{vm_id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["vm_id"] == vm_id
        assert data["status"] == "STOPPED"

    def test_get_status_not_found(self):
        """Test getting status of non-existent VM"""
        fake_id = str(uuid4())

        response = client.get(f"/api/v1/vms/{fake_id}/status")

        assert response.status_code == 404


class TestStartVM:
    """Test start VM endpoint"""

    def test_start_vm_success(self):
        """Test starting a stopped VM"""
        # Create VM
        create_response = client.post("/api/v1/vms", json={
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        })
        vm_id = create_response.json()["id"]

        # Start VM
        response = client.post(f"/api/v1/vms/{vm_id}/start")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RUNNING"

    def test_start_vm_already_running(self):
        """Test starting an already running VM fails"""
        # Create and start VM
        create_response = client.post("/api/v1/vms", json={
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        })
        vm_id = create_response.json()["id"]
        client.post(f"/api/v1/vms/{vm_id}/start")

        # Try to start again
        response = client.post(f"/api/v1/vms/{vm_id}/start")

        assert response.status_code == 409


class TestStopVM:
    """Test stop VM endpoint"""

    def test_stop_vm_success(self):
        """Test stopping a running VM"""
        # Create and start VM
        create_response = client.post("/api/v1/vms", json={
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        })
        vm_id = create_response.json()["id"]
        client.post(f"/api/v1/vms/{vm_id}/start")

        # Stop VM
        response = client.post(f"/api/v1/vms/{vm_id}/stop")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "STOPPED"

    def test_stop_vm_already_stopped(self):
        """Test stopping an already stopped VM fails"""
        # Create VM (already stopped)
        create_response = client.post("/api/v1/vms", json={
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        })
        vm_id = create_response.json()["id"]

        # Try to stop
        response = client.post(f"/api/v1/vms/{vm_id}/stop")

        assert response.status_code == 409


class TestRestartVM:
    """Test restart VM endpoint"""

    def test_restart_vm_success(self):
        """Test restarting a running VM"""
        # Create and start VM
        create_response = client.post("/api/v1/vms", json={
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        })
        vm_id = create_response.json()["id"]
        client.post(f"/api/v1/vms/{vm_id}/start")

        # Restart VM
        response = client.post(f"/api/v1/vms/{vm_id}/restart")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RUNNING"

    def test_restart_stopped_vm_fails(self):
        """Test restarting a stopped VM fails"""
        # Create VM (stopped)
        create_response = client.post("/api/v1/vms", json={
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        })
        vm_id = create_response.json()["id"]

        # Try to restart
        response = client.post(f"/api/v1/vms/{vm_id}/restart")

        assert response.status_code == 409


class TestPauseVM:
    """Test pause VM endpoint"""

    def test_pause_vm_success(self):
        """Test pausing a running VM"""
        # Create and start VM
        create_response = client.post("/api/v1/vms", json={
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        })
        vm_id = create_response.json()["id"]
        client.post(f"/api/v1/vms/{vm_id}/start")

        # Pause VM
        response = client.post(f"/api/v1/vms/{vm_id}/pause")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PAUSED"

    def test_pause_stopped_vm_fails(self):
        """Test pausing a stopped VM fails"""
        # Create VM (stopped)
        create_response = client.post("/api/v1/vms", json={
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        })
        vm_id = create_response.json()["id"]

        # Try to pause
        response = client.post(f"/api/v1/vms/{vm_id}/pause")

        assert response.status_code == 409


class TestResumeVM:
    """Test resume VM endpoint"""

    def test_resume_vm_success(self):
        """Test resuming a paused VM"""
        # Create, start, and pause VM
        create_response = client.post("/api/v1/vms", json={
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        })
        vm_id = create_response.json()["id"]
        client.post(f"/api/v1/vms/{vm_id}/start")
        client.post(f"/api/v1/vms/{vm_id}/pause")

        # Resume VM
        response = client.post(f"/api/v1/vms/{vm_id}/resume")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RUNNING"

    def test_resume_running_vm_fails(self):
        """Test resuming a running VM fails"""
        # Create and start VM
        create_response = client.post("/api/v1/vms", json={
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        })
        vm_id = create_response.json()["id"]
        client.post(f"/api/v1/vms/{vm_id}/start")

        # Try to resume
        response = client.post(f"/api/v1/vms/{vm_id}/resume")

        assert response.status_code == 409


class TestDeleteVM:
    """Test delete VM endpoint"""

    def test_delete_vm_success(self):
        """Test deleting a VM"""
        # Create VM
        create_response = client.post("/api/v1/vms", json={
            "name": "test-vm",
            "flavor": "m1.small",
            "image": "ubuntu-22.04"
        })
        vm_id = create_response.json()["id"]

        # Delete VM
        response = client.delete(f"/api/v1/vms/{vm_id}")

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/v1/vms/{vm_id}")
        assert get_response.status_code == 404

    def test_delete_vm_not_found(self):
        """Test deleting non-existent VM"""
        fake_id = str(uuid4())

        response = client.delete(f"/api/v1/vms/{fake_id}")

        assert response.status_code == 404


class TestCompleteWorkflows:
    """Test complete end-to-end workflows"""

    def test_full_lifecycle(self):
        """Test complete VM lifecycle"""
        # Create
        response = client.post("/api/v1/vms", json={
            "name": "workflow-vm",
            "flavor": "m1.medium",
            "image": "ubuntu-22.04"
        })
        assert response.status_code == 201
        vm_id = response.json()["id"]

        # Start
        response = client.post(f"/api/v1/vms/{vm_id}/start")
        assert response.status_code == 200
        assert response.json()["status"] == "RUNNING"

        # Pause
        response = client.post(f"/api/v1/vms/{vm_id}/pause")
        assert response.status_code == 200
        assert response.json()["status"] == "PAUSED"

        # Resume
        response = client.post(f"/api/v1/vms/{vm_id}/resume")
        assert response.status_code == 200
        assert response.json()["status"] == "RUNNING"

        # Restart
        response = client.post(f"/api/v1/vms/{vm_id}/restart")
        assert response.status_code == 200
        assert response.json()["status"] == "RUNNING"

        # Stop
        response = client.post(f"/api/v1/vms/{vm_id}/stop")
        assert response.status_code == 200
        assert response.json()["status"] == "STOPPED"

        # Delete
        response = client.delete(f"/api/v1/vms/{vm_id}")
        assert response.status_code == 204

    def test_multiple_vms_workflow(self):
        """Test managing multiple VMs"""
        vm_ids = []

        # Create 3 VMs
        for i in range(3):
            response = client.post("/api/v1/vms", json={
                "name": f"multi-vm-{i}",
                "flavor": "m1.small",
                "image": "ubuntu-22.04"
            })
            assert response.status_code == 201
            vm_ids.append(response.json()["id"])

        # Start all VMs
        for vm_id in vm_ids:
            response = client.post(f"/api/v1/vms/{vm_id}/start")
            assert response.status_code == 200

        # List VMs (all should be running)
        response = client.get("/api/v1/vms?status=RUNNING")
        assert response.status_code == 200
        assert response.json()["total"] == 3

        # Stop first VM
        response = client.post(f"/api/v1/vms/{vm_ids[0]}/stop")
        assert response.status_code == 200

        # List running VMs (should be 2)
        response = client.get("/api/v1/vms?status=RUNNING")
        assert response.json()["total"] == 2

        # Delete all VMs
        for vm_id in vm_ids:
            response = client.delete(f"/api/v1/vms/{vm_id}")
            assert response.status_code == 204
