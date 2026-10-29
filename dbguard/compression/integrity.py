"""Module 3: Compression Integrity Validation.

Executes complete format-specific decompression passes to verify stream integrity,
header magic numbers, CRC-32/Adler checksums, and trailer structure without
loading entire uncompressed datasets into memory.
"""

import hashlib
from pathlib import Path
from typing import BinaryIO, Union, Optional

from dbguard.compression.streaming import StreamingDecompressor
from dbguard.exceptions import (
    CompressionError,
    CorruptedStreamError,
    ResourceLimitExceededError,
    TruncatedStreamError,
    UnsupportedFormatError,
)
from dbguard.models import (
    CompressionFormat,
    CompressionValidationResult,
    VerificationStatus,
)


def validate_compression_integrity(
    stream_or_path: Union[str, Path, BinaryIO],
    format_type: CompressionFormat,
    compressed_file_size: Optional[int] = None,
    chunk_size: int = 65_536,
    max_decompressed_size: int = 5_368_709_120,
    max_expansion_ratio: float = 100.0,
) -> CompressionValidationResult:
    """Perform full stream decompression to test physical container integrity.

    Verifies framing, block integrity, CRC trailers (where supported), and detects
    truncation. Computes SHA-256 of the decompressed stream on the fly.

    Args:
        stream_or_path: File path or open binary buffer.
        format_type: Detected compression format.
        compressed_file_size: Known compressed byte size from file inspection.
        chunk_size: Read buffer size.
        max_decompressed_size: Safety limit on total decompressed bytes.
        max_expansion_ratio: Safety limit on expansion ratio.

    Returns:
        CompressionValidationResult with verification status and stream metrics.
    """
    limitations = [
        "Passing stream integrity proves the compression container is structurally intact and decodable.",
        "It does NOT prove that the database export command included all records from the source table."
    ]

    if format_type == CompressionFormat.UNKNOWN:
        return CompressionValidationResult(
            status=VerificationStatus.FAIL,
            format=format_type,
            compressed_bytes_read=0,
            decompressed_bytes=0,
            expansion_ratio=0.0,
            sha256_decompressed="",
            is_truncated=False,
            crc_or_trailer_valid=False,
            error_message="Unknown or unsupported compression header format.",
            limitations=limitations
        )

    decompressor = StreamingDecompressor(
        stream_or_path=stream_or_path,
        format_type=format_type,
        chunk_size=chunk_size,
        max_decompressed_size=max_decompressed_size,
        max_expansion_ratio=max_expansion_ratio,
    )

    hasher = hashlib.sha256()
    decompressed_bytes = 0
    is_truncated = False
    crc_valid = None
    status = VerificationStatus.PASS
    error_msg = None

    try:
        for chunk in decompressor.stream_chunks():
            hasher.update(chunk)
            decompressed_bytes += len(chunk)

        # Successfully reached stream EOF and trailer verified
        crc_valid = True

    except TruncatedStreamError as e:
        status = VerificationStatus.FAIL
        is_truncated = True
        crc_valid = False
        error_msg = f"Stream truncated unexpectedly: {e}"
    except CorruptedStreamError as e:
        status = VerificationStatus.FAIL
        crc_valid = False
        error_msg = f"Stream payload or CRC corrupted: {e}"
    except ResourceLimitExceededError as e:
        status = VerificationStatus.FAIL
        error_msg = f"Security limit exceeded: {e}"
    except UnsupportedFormatError as e:
        status = VerificationStatus.NOT_APPLICABLE
        error_msg = str(e)
    except Exception as e:
        status = VerificationStatus.FAIL
        error_msg = f"Unexpected decompression failure: {type(e).__name__}: {e}"

    compressed_size = compressed_file_size or decompressor.compressed_bytes_read or 1
    expansion_ratio = round(decompressed_bytes / max(1, compressed_size), 4)

    return CompressionValidationResult(
        status=status,
        format=format_type,
        compressed_bytes_read=compressed_size,
        decompressed_bytes=decompressed_bytes,
        expansion_ratio=expansion_ratio,
        sha256_decompressed=hasher.hexdigest() if status == VerificationStatus.PASS else "",
        is_truncated=is_truncated,
        crc_or_trailer_valid=crc_valid,
        error_message=error_msg,
        limitations=limitations
    )

