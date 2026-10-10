from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(self, status_code: int, code: str, detail: str):
        super().__init__(status_code=status_code, detail={"code": code, "detail": detail})


class NotFoundError(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(status.HTTP_404_NOT_FOUND, "NOT_FOUND", f"{resource} not found")


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", detail)


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Access denied"):
        super().__init__(status.HTTP_403_FORBIDDEN, "FORBIDDEN", detail)


class ConflictError(AppException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status.HTTP_409_CONFLICT, "CONFLICT", detail)


class ValidationError(AppException):
    def __init__(self, detail: str):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", detail)


class ServiceUnavailableError(AppException):
    def __init__(self, detail: str = "Service unavailable"):
        super().__init__(status.HTTP_503_SERVICE_UNAVAILABLE, "SERVICE_UNAVAILABLE", detail)
