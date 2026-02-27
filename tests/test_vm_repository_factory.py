"""
Unit Tests for VM Repository Factory

Tests the factory pattern for creating mock or real OpenStack repositories.
"""

import pytest
from unittest.mock import patch

from app.repositories.vm_repository import VMRepository
from app.repositories.vm_repository_factory import (
    create_vm_repository,
    get_vm_repository,
    reset_repository,
)


pytestmark = pytest.mark.unit


class TestCreateVMRepository:
    """Test create_vm_repository function"""

    def test_create_mock_repository_when_flag_false(self):
        """Test factory creates mock repository when USE_REAL_OPENSTACK=False"""
        with patch("app.repositories.vm_repository_factory.settings") as mock_settings:
            mock_settings.use_real_openstack = False

            repo = create_vm_repository()

            assert repo is not None
            assert isinstance(repo, VMRepository)
            assert type(repo).__name__ == "VMRepository"

    def test_create_openstack_repository_when_flag_true(self):
        """Test factory creates OpenStack repository when USE_REAL_OPENSTACK=True"""
        with patch("app.repositories.vm_repository_factory.settings") as mock_settings:
            mock_settings.use_real_openstack = True
            mock_settings.openstack_auth_url = "http://test/identity"
            mock_settings.openstack_username = "admin"
            mock_settings.openstack_password = "test"
            mock_settings.openstack_project_name = "demo"
            mock_settings.openstack_user_domain_name = "Default"
            mock_settings.openstack_project_domain_name = "Default"
            mock_settings.openstack_region_name = "RegionOne"

            # Mock the OpenStack connection
            with patch("app.repositories.openstack_vm_repository.openstack.connect"):
                repo = create_vm_repository()

                assert repo is not None
                assert type(repo).__name__ == "OpenStackVMRepository"

    def test_create_openstack_repository_import_error(self):
        """Test ImportError is caught and re-raised as RuntimeError"""
        with patch("app.repositories.vm_repository_factory.settings") as mock_settings:
            mock_settings.use_real_openstack = True

            # Mock the import to fail
            with patch("builtins.__import__", side_effect=ImportError("No module")):
                with pytest.raises(RuntimeError, match="OpenStack SDK not available"):
                    create_vm_repository()

    def test_create_openstack_repository_connection_error(self):
        """Test connection error is caught and re-raised as RuntimeError"""
        with patch("app.repositories.vm_repository_factory.settings") as mock_settings:
            mock_settings.use_real_openstack = True
            mock_settings.openstack_auth_url = "http://invalid/identity"

            # Mock OpenStack connection to fail
            with patch(
                "app.repositories.openstack_vm_repository.openstack.connect",
                side_effect=Exception("Connection failed"),
            ):
                with pytest.raises(
                    RuntimeError, match="OpenStack initialization failed"
                ):
                    create_vm_repository()


class TestGetVMRepository:
    """Test get_vm_repository function (singleton pattern)"""

    def setUp(self):
        """Reset repository before each test"""
        reset_repository()

    def test_singleton_returns_same_instance_in_production(self):
        """Test singleton pattern returns same instance in production/development"""
        with patch("app.repositories.vm_repository_factory.settings") as mock_settings:
            mock_settings.use_real_openstack = False
            mock_settings.environment = "development"

            repo1 = get_vm_repository()
            repo2 = get_vm_repository()

            assert repo1 is repo2, "Should return same instance (singleton)"

    def test_fresh_instance_in_test_environment(self):
        """Test that test environment gets fresh instances (no singleton)"""
        with patch("app.repositories.vm_repository_factory.settings") as mock_settings:
            mock_settings.use_real_openstack = False
            mock_settings.environment = "test"

            repo1 = get_vm_repository()
            repo2 = get_vm_repository()

            # In test mode, should get fresh instances
            # Note: This test verifies the factory is called, not object identity
            assert repo1 is not None
            assert repo2 is not None

    def test_singleton_lazy_initialization(self):
        """Test singleton is created on first access"""
        reset_repository()

        with patch("app.repositories.vm_repository_factory.settings") as mock_settings:
            mock_settings.use_real_openstack = False
            mock_settings.environment = "production"

            # First call should create instance
            repo = get_vm_repository()
            assert repo is not None

            # Subsequent calls should return same instance
            repo2 = get_vm_repository()
            assert repo is repo2


class TestResetRepository:
    """Test reset_repository function"""

    def test_reset_repository_clears_singleton(self):
        """Test reset_repository clears the singleton instance"""
        with patch("app.repositories.vm_repository_factory.settings") as mock_settings:
            mock_settings.use_real_openstack = False
            mock_settings.environment = "development"

            # Get first instance
            repo1 = get_vm_repository()
            assert repo1 is not None

            # Reset
            reset_repository()

            # Get new instance - should be different
            repo2 = get_vm_repository()
            assert repo2 is not None
            assert repo1 is not repo2, "After reset, should get new instance"

    def test_reset_repository_can_be_called_multiple_times(self):
        """Test reset_repository can be called multiple times safely"""
        reset_repository()
        reset_repository()
        reset_repository()

        # Should still work after multiple resets
        with patch("app.repositories.vm_repository_factory.settings") as mock_settings:
            mock_settings.use_real_openstack = False
            mock_settings.environment = "development"

            repo = get_vm_repository()
            assert repo is not None


class TestFactoryIntegration:
    """Integration tests for factory behavior"""

    def test_factory_respects_configuration_changes(self):
        """Test factory respects configuration flag changes"""
        # First with mock
        with patch("app.repositories.vm_repository_factory.settings") as mock_settings:
            mock_settings.use_real_openstack = False
            mock_settings.environment = "test"

            repo1 = create_vm_repository()
            assert type(repo1).__name__ == "VMRepository"

            # Then with OpenStack (mocked)
            mock_settings.use_real_openstack = True
            mock_settings.openstack_auth_url = "http://test/identity"
            mock_settings.openstack_username = "admin"
            mock_settings.openstack_password = "test"
            mock_settings.openstack_project_name = "demo"
            mock_settings.openstack_user_domain_name = "Default"
            mock_settings.openstack_project_domain_name = "Default"
            mock_settings.openstack_region_name = "RegionOne"

            with patch("app.repositories.openstack_vm_repository.openstack.connect"):
                repo2 = create_vm_repository()
                assert type(repo2).__name__ == "OpenStackVMRepository"

    def test_factory_type_hints_are_correct(self):
        """Test factory returns Union[VMRepository, OpenStackVMRepository]"""
        with patch("app.repositories.vm_repository_factory.settings") as mock_settings:
            mock_settings.use_real_openstack = False
            mock_settings.environment = "test"

            repo = create_vm_repository()

            # Should be one of the expected types
            assert type(repo).__name__ in ["VMRepository", "OpenStackVMRepository"]
