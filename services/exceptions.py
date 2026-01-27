"""
Custom exceptions for service layer.
Following refactor:flask exception handling patterns.
"""


class ServiceException(Exception):
    """Base exception for all service layer errors."""
    pass


class ParejaValidationError(ServiceException):
    """Raised when pareja data validation fails."""
    pass


class ParejaNotFoundError(ServiceException):
    """Raised when a pareja is not found in the system."""
    pass


class ResultadoAlgoritmoNotFoundError(ServiceException):
    """Raised when resultado_algoritmo is not available."""
    pass


class GrupoNotFoundError(ServiceException):
    """Raised when a grupo is not found."""
    pass
