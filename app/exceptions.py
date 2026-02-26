"""
Custom Exceptions

Application-specific exception classes with HTTP status code mapping.
"""

from typing import Optional
from uuid import UUID


class VMException(Exception):
    """Base exception for VM operations"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class VMNotFoundException(VMException):
    """Exception raised when VM is not found"""

    def __init__(self, vm_id: UUID):
        message = f"VM with ID {vm_id} not found"
        super().__init__(message, status_code=404)
        self.vm_id = vm_id


class InvalidStateTransitionException(VMException):
    """Exception raised when attempting an invalid state transition"""

    def __init__(self, vm_id: UUID, current_state: str, attempted_action: str):
        message = (
            f"Cannot perform '{attempted_action}' on VM {vm_id} "
            f"in state '{current_state}'"
        )
        super().__init__(message, status_code=409)
        self.vm_id = vm_id
        self.current_state = current_state
        self.attempted_action = attempted_action


class ValidationException(VMException):
    """Exception raised for validation errors"""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, status_code=422)
        self.field = field


class VMAlreadyExistsException(VMException):
    """Exception raised when trying to create a VM with a name that already exists"""

    def __init__(self, name: str):
        message = f"VM with name '{name}' already exists"
        super().__init__(message, status_code=409)
        self.name = name
