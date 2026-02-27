"""
Test Configuration

Global pytest configuration and fixtures for test suite.

IMPORTANT: This module sets environment variables before any app imports.
"""

import os

# Set test environment variables BEFORE any imports from app
# This ensures settings are loaded with test configuration
os.environ["USE_REAL_OPENSTACK"] = "False"
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_LEVEL"] = "WARNING"

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def set_test_environment():
    """
    Verify test environment is set correctly.

    Environment variables are set at module level before imports.
    """
    # Verify settings
    from app.config import settings

    assert settings.use_real_openstack is False, "Tests must use mock repository"
    assert settings.environment == "test", "Tests must run in test environment"

    yield

    # Cleanup after all tests
    # Reset to default values
    os.environ.pop("USE_REAL_OPENSTACK", None)
    os.environ.pop("ENVIRONMENT", None)
    os.environ.pop("LOG_LEVEL", None)
