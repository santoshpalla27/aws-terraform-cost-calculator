"""
Custom exceptions for immutable results.
"""


class ImmutableResultError(Exception):
    """Raised when attempting to modify an immutable result."""
    pass


class ResultAlreadyExistsError(Exception):
    """Raised when attempting to create a duplicate result."""
    pass


class ResultNotFoundError(Exception):
    """Raised when result is not found."""
    pass
