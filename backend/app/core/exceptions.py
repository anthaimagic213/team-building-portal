from fastapi import HTTPException, status


class UnauthorizedException(HTTPException):
    """Raised when authentication fails (401)"""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenException(HTTPException):
    """Raised when user lacks required permissions (403)"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFoundException(HTTPException):
    """Raised when requested resource is not found (404)"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class ConflictException(HTTPException):
    """
    Raised when operation conflicts with current state (409).
    Used extensively for Gala Dinner optimistic locking.
    """
    def __init__(self, detail: str = "Resource conflict detected"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class BadRequestException(HTTPException):
    """Raised when request validation fails (400)"""
    def __init__(self, detail: str = "Invalid request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class RegistrationClosedException(HTTPException):
    """Raised when attempting to modify registration after deadline"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration period has closed. No modifications allowed."
        )


class AllocationInProgressException(HTTPException):
    """Raised when data cannot be modified during allocation"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot modify data while allocation is in progress"
        )


class CapacityExceededException(HTTPException):
    """Raised when trying to exceed vehicle/flight/seat capacity"""
    def __init__(self, resource_type: str, available: int, requested: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{resource_type} capacity exceeded. Available: {available}, Requested: {requested}"
        )

