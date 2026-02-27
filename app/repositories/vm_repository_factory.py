"""
VM Repository Factory

Factory for creating the appropriate VM repository based on configuration.
"""

import logging
from typing import Union, TYPE_CHECKING

from app.config import settings
from app.repositories.vm_repository import VMRepository

if TYPE_CHECKING:
    from .openstack_vm_repository import OpenStackVMRepository

logger = logging.getLogger(__name__)


def create_vm_repository() -> Union[VMRepository, "OpenStackVMRepository"]:
    """
    Create and return the appropriate VM repository based on configuration.

    Returns:
        VMRepository (mock) or OpenStackVMRepository (real) based on settings

    Raises:
        RuntimeError: If OpenStack connection fails when use_real_openstack is True
    """
    if settings.use_real_openstack:
        logger.info("Using real OpenStack SDK repository")
        try:
            # Import here to avoid circular dependency and allow mock tests
            from app.repositories.openstack_vm_repository import OpenStackVMRepository

            return OpenStackVMRepository()
        except ImportError as e:
            logger.error(
                f"Failed to import OpenStackVMRepository. "
                f"Ensure openstacksdk is installed: {e}"
            )
            raise RuntimeError(
                "OpenStack SDK not available. Install with: pip install openstacksdk"
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenStack repository: {e}")
            raise RuntimeError(f"OpenStack initialization failed: {e}")
    else:
        logger.info("Using mock in-memory repository")
        return VMRepository()


# Singleton instance for dependency injection
_repository_instance = None


def reset_repository():
    """
    Reset singleton instance.

    This is useful for testing to ensure a fresh repository instance.
    """
    global _repository_instance
    _repository_instance = None
    logger.debug("Repository singleton reset")


def get_vm_repository() -> Union[VMRepository, "OpenStackVMRepository"]:
    """
    Get or create the singleton VM repository instance.

    This is used for dependency injection in FastAPI routes.
    In test environment, creates a fresh instance each time to avoid state leakage.

    Returns:
        The singleton repository instance (or fresh instance in test mode)
    """
    global _repository_instance

    # In test environment, don't use singleton to avoid state sharing between tests
    if settings.environment == "test":
        logger.debug("Test environment detected - creating fresh repository instance")
        return create_vm_repository()

    # Production/development: use singleton
    if _repository_instance is None:
        _repository_instance = create_vm_repository()
    return _repository_instance
