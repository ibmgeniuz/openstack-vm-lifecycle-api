"""
OpenStack Test Helpers

Utility functions for OpenStack integration testing.
"""

import logging
from typing import List, Optional

import openstack
from openstack.connection import Connection

logger = logging.getLogger(__name__)


def create_openstack_connection() -> Connection:
    """
    Create OpenStack connection for testing.

    Returns:
        OpenStack connection object

    Raises:
        RuntimeError: If connection fails
    """
    try:
        import os

        conn = openstack.connect(
            auth_url=os.getenv("OPENSTACK_AUTH_URL", "http://192.168.2.110/identity"),
            project_name=os.getenv("OPENSTACK_PROJECT_NAME", "demo"),
            username=os.getenv("OPENSTACK_USERNAME", "admin"),
            password=os.getenv("OPENSTACK_PASSWORD", "devstack"),
            user_domain_name=os.getenv("OPENSTACK_USER_DOMAIN_NAME", "Default"),
            project_domain_name=os.getenv("OPENSTACK_PROJECT_DOMAIN_NAME", "Default"),
            region_name=os.getenv("OPENSTACK_REGION_NAME", "RegionOne"),
        )
        logger.info("OpenStack connection established for testing")
        return conn
    except Exception as e:
        logger.error(f"Failed to create OpenStack connection: {e}")
        raise RuntimeError(f"OpenStack connection failed: {e}")


def cleanup_test_vms(
    conn: Connection, prefix: str = "test-", max_age_seconds: Optional[int] = None
):
    """
    Clean up VMs created during testing.

    Args:
        conn: OpenStack connection
        prefix: VM name prefix to identify test VMs
        max_age_seconds: Optional age threshold to delete older VMs

    Returns:
        Number of VMs deleted
    """
    try:
        servers = list(conn.compute.servers())
        deleted_count = 0

        for server in servers:
            if server.name.startswith(prefix):
                try:
                    logger.info(f"Deleting test VM: {server.name} (ID: {server.id})")
                    conn.compute.delete_server(server, wait=True)
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete VM {server.name}: {e}")

        logger.info(f"Cleaned up {deleted_count} test VMs")
        return deleted_count
    except Exception as e:
        logger.error(f"Failed to cleanup test VMs: {e}")
        return 0


def wait_for_server_status(
    conn: Connection, server_id: str, expected_status: str, timeout: int = 60
) -> bool:
    """
    Wait for server to reach expected status.

    Args:
        conn: OpenStack connection
        server_id: Server ID to monitor
        expected_status: Expected status (ACTIVE, SHUTOFF, etc.)
        timeout: Maximum wait time in seconds

    Returns:
        True if status reached, False on timeout
    """
    try:
        server = conn.compute.get_server(server_id)
        if not server:
            return False

        server = conn.compute.wait_for_server(
            server, status=expected_status, wait=timeout
        )
        return server.status == expected_status
    except Exception as e:
        logger.error(f"Error waiting for server status: {e}")
        return False


def get_available_networks(conn: Connection) -> List[str]:
    """
    Get list of available network names.

    Args:
        conn: OpenStack connection

    Returns:
        List of network names
    """
    try:
        networks = list(conn.network.networks())
        network_names = [net.name for net in networks]
        logger.debug(f"Available networks: {network_names}")
        return network_names
    except Exception as e:
        logger.error(f"Failed to get networks: {e}")
        return []


def get_available_images(conn: Connection) -> List[str]:
    """
    Get list of available image names.

    Args:
        conn: OpenStack connection

    Returns:
        List of image names
    """
    try:
        images = list(conn.compute.images())
        image_names = [img.name for img in images]
        logger.debug(f"Available images: {image_names}")
        return image_names
    except Exception as e:
        logger.error(f"Failed to get images: {e}")
        return []


def get_available_flavors(conn: Connection) -> List[str]:
    """
    Get list of available flavor names.

    Args:
        conn: OpenStack connection

    Returns:
        List of flavor names
    """
    try:
        flavors = list(conn.compute.flavors())
        flavor_names = [f.name for f in flavors]
        logger.debug(f"Available flavors: {flavor_names}")
        return flavor_names
    except Exception as e:
        logger.error(f"Failed to get flavors: {e}")
        return []


def verify_openstack_availability() -> bool:
    """
    Verify that OpenStack is available and accessible.

    Returns:
        True if OpenStack is available, False otherwise
    """
    try:
        conn = create_openstack_connection()
        # Try a simple operation
        list(conn.compute.flavors(details=False, limit=1))
        logger.info("OpenStack is available and accessible")
        return True
    except Exception as e:
        logger.warning(f"OpenStack is not available: {e}")
        return False
