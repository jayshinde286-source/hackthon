"""DBGuard custom exception hierarchy.

Provides structured, specific exceptions for integrity failures, format errors,
resource limit violations, and security violations.
"""

class DBGuardError(Exception):
    """Base exception for all DBGuard errors."""
    pass


class CompressionError(DBGuardError):
    """Base exception for compression-related failures."""
    pass


class CorruptedStreamError(CompressionError):
    """Raised when a compressed stream contains invalid CRC, trailer, or payload data."""
    pass


class TruncatedStreamError(CompressionError):
    """Raised when a stream ends unexpectedly before completion."""
    pass


class UnsupportedFormatError(DBGuardError):
    """Raised when an unrecognized, ambiguous, or unsupported format is supplied."""
    pass


class ResourceLimitExceededError(DBGuardError):
    """Raised when decompression exceeds max size or expansion ratio safety limits."""
    pass


class ParsingError(DBGuardError):
    """Raised when data parsing encounters unrecoverable structural syntax errors."""
    def __init__(self, message: str, line_number: int = -1, raw_excerpt: str = ""):
        super().__init__(message)
        self.line_number = line_number
        self.raw_excerpt = raw_excerpt


class ManifestError(DBGuardError):
    """Raised when integrity manifest validation fails or format is invalid."""
    pass


class SecurityError(DBGuardError):
    """Raised on unsafe file path traversal or hazardous operations."""
    pass

