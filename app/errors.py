class DomainError(Exception):
    """Business rule violation mapped to a JSON error response."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def not_found(entity: str) -> DomainError:
    return DomainError(404, f"{entity.upper()}_NOT_FOUND", f"{entity.capitalize()} not found.")


def conflict(code: str, message: str) -> DomainError:
    return DomainError(409, code, message)


def forbidden(code: str, message: str) -> DomainError:
    return DomainError(403, code, message)


def unauthorized(message: str = "Valid Bearer token required.") -> DomainError:
    return DomainError(401, "UNAUTHORIZED", message)
