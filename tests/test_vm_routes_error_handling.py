"""
Error Handling Tests for VM API Routes

Tests exception handling and error paths in vm_routes to improve coverage.
Focuses on generic exception handlers that return 500 errors.
"""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from uuid import uuid4

from main import app
from app.exceptions import VMException
from app.routes.vm_routes import get_vm_service

client = TestClient(app)


@pytest.mark.unit
class TestCreateVMErrorHandling:
    """Test error handling in create_vm endpoint"""

    def test_create_vm_generic_vm_exception(self):
        """Test create_vm with generic VMException (base class)"""
        # Setup mock to raise base VMException
        mock_service = MagicMock()
        mock_service.create_vm.side_effect = VMException("Generic VM error")

        # Override dependency
        app.dependency_overrides[get_vm_service] = lambda: mock_service

        try:
            payload = {"name": "test-vm", "flavor": "m1.tiny", "image": "cirros"}
            response = client.post("/api/v1/vms", json=payload)

            assert response.status_code == 500
            assert "Generic VM error" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_create_vm_unexpected_exception(self):
        """Test create_vm with unexpected exception (RuntimeError)"""
        # Setup mock to raise unexpected exception
        mock_service = MagicMock()
        mock_service.create_vm.side_effect = RuntimeError("Database connection failed")

        # Override dependency
        app.dependency_overrides[get_vm_service] = lambda: mock_service

        try:
            payload = {"name": "test-vm", "flavor": "m1.tiny", "image": "cirros"}
            response = client.post("/api/v1/vms", json=payload)

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal server error"
        finally:
            app.dependency_overrides.clear()


@pytest.mark.unit
class TestListVMsErrorHandling:
    """Test error handling in list_vms endpoint"""

    def test_list_vms_unexpected_exception(self):
        """Test list_vms with unexpected exception"""
        # Setup mock to raise unexpected exception
        mock_service = MagicMock()
        mock_service.list_vms.side_effect = ValueError("Invalid database query")

        # Override dependency
        app.dependency_overrides[get_vm_service] = lambda: mock_service

        try:
            response = client.get("/api/v1/vms")

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal server error"
        finally:
            app.dependency_overrides.clear()


@pytest.mark.unit
class TestGetVMErrorHandling:
    """Test error handling in get_vm endpoint"""

    def test_get_vm_unexpected_exception(self):
        """Test get_vm with unexpected exception"""
        # Setup mock to raise unexpected exception
        mock_service = MagicMock()
        mock_service.get_vm.side_effect = ConnectionError("Network timeout")

        # Override dependency
        app.dependency_overrides[get_vm_service] = lambda: mock_service

        try:
            vm_id = str(uuid4())
            response = client.get(f"/api/v1/vms/{vm_id}")

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal server error"
        finally:
            app.dependency_overrides.clear()


@pytest.mark.unit
class TestGetVMStatusErrorHandling:
    """Test error handling in get_vm_status endpoint"""

    def test_get_vm_status_unexpected_exception(self):
        """Test get_vm_status with unexpected exception"""
        # Setup mock to raise unexpected exception
        mock_service = MagicMock()
        mock_service.get_vm_status.side_effect = AttributeError(
            "Object has no attribute"
        )

        # Override dependency
        app.dependency_overrides[get_vm_service] = lambda: mock_service

        try:
            vm_id = str(uuid4())
            response = client.get(f"/api/v1/vms/{vm_id}/status")

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal server error"
        finally:
            app.dependency_overrides.clear()


@pytest.mark.unit
class TestStartVMErrorHandling:
    """Test error handling in start_vm endpoint"""

    def test_start_vm_unexpected_exception(self):
        """Test start_vm with unexpected exception"""
        # Setup mock to raise unexpected exception
        mock_service = MagicMock()
        mock_service.start_vm.side_effect = OSError("System resource unavailable")

        # Override dependency
        app.dependency_overrides[get_vm_service] = lambda: mock_service

        try:
            vm_id = str(uuid4())
            response = client.post(f"/api/v1/vms/{vm_id}/start")

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal server error"
        finally:
            app.dependency_overrides.clear()


@pytest.mark.unit
class TestStopVMErrorHandling:
    """Test error handling in stop_vm endpoint"""

    def test_stop_vm_unexpected_exception(self):
        """Test stop_vm with unexpected exception"""
        # Setup mock to raise unexpected exception
        mock_service = MagicMock()
        mock_service.stop_vm.side_effect = MemoryError("Out of memory")

        # Override dependency
        app.dependency_overrides[get_vm_service] = lambda: mock_service

        try:
            vm_id = str(uuid4())
            response = client.post(f"/api/v1/vms/{vm_id}/stop")

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal server error"
        finally:
            app.dependency_overrides.clear()


@pytest.mark.unit
class TestRestartVMErrorHandling:
    """Test error handling in restart_vm endpoint"""

    def test_restart_vm_unexpected_exception(self):
        """Test restart_vm with unexpected exception"""
        # Setup mock to raise unexpected exception
        mock_service = MagicMock()
        mock_service.restart_vm.side_effect = TypeError("Invalid type conversion")

        # Override dependency
        app.dependency_overrides[get_vm_service] = lambda: mock_service

        try:
            vm_id = str(uuid4())
            response = client.post(f"/api/v1/vms/{vm_id}/restart")

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal server error"
        finally:
            app.dependency_overrides.clear()


@pytest.mark.unit
class TestPauseVMErrorHandling:
    """Test error handling in pause_vm endpoint"""

    def test_pause_vm_unexpected_exception(self):
        """Test pause_vm with unexpected exception"""
        # Setup mock to raise unexpected exception
        mock_service = MagicMock()
        mock_service.pause_vm.side_effect = KeyError("Missing configuration key")

        # Override dependency
        app.dependency_overrides[get_vm_service] = lambda: mock_service

        try:
            vm_id = str(uuid4())
            response = client.post(f"/api/v1/vms/{vm_id}/pause")

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal server error"
        finally:
            app.dependency_overrides.clear()


@pytest.mark.unit
class TestResumeVMErrorHandling:
    """Test error handling in resume_vm endpoint"""

    def test_resume_vm_unexpected_exception(self):
        """Test resume_vm with unexpected exception"""
        # Setup mock to raise unexpected exception
        mock_service = MagicMock()
        mock_service.resume_vm.side_effect = IndexError("List index out of range")

        # Override dependency
        app.dependency_overrides[get_vm_service] = lambda: mock_service

        try:
            vm_id = str(uuid4())
            response = client.post(f"/api/v1/vms/{vm_id}/resume")

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal server error"
        finally:
            app.dependency_overrides.clear()


@pytest.mark.unit
class TestDeleteVMErrorHandling:
    """Test error handling in delete_vm endpoint"""

    def test_delete_vm_unexpected_exception(self):
        """Test delete_vm with unexpected exception"""
        # Setup mock to raise unexpected exception
        mock_service = MagicMock()
        mock_service.delete_vm.side_effect = IOError("Disk write failed")

        # Override dependency
        app.dependency_overrides[get_vm_service] = lambda: mock_service

        try:
            vm_id = str(uuid4())
            response = client.delete(f"/api/v1/vms/{vm_id}")

            assert response.status_code == 500
            assert response.json()["detail"] == "Internal server error"
        finally:
            app.dependency_overrides.clear()
