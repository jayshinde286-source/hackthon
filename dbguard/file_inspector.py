"""Module 1: File Intake and Inspection.

Inspects incoming export files securely using file signatures (magic bytes),
computes chunked SHA-256 of the compressed payload, enforces size limits,
and generates a structured FileInspection result object.
"""

import hashlib
import os
from pathlib import Path
from typing import Union, BinaryIO, Optional

from dbguard.models import FileInspection, CompressionFormat
from dbguard.exceptions import SecurityError, UnsupportedFormatError, ResourceLimitExceededError
from dbguard.utils.safe_paths import validate_input_path

# Standard Magic Byte Signatures
MAGIC_GZIP = b"\x1f\x8b"
MAGIC_BZIP2 = b"BZh"
MAGIC_XZ = b"\xfd7zXZ\x00"
MAGIC_ZSTD = b"\x28\xb5/\xfd"

DEFAULT_MAX_COMPRESSED_SIZE = 524_288_000  # 500 MB default guard
CHUNK_SIZE = 65_536  # 64 KB chunk for bounded memory reads


def detect_compression_format(header_bytes: bytes) -> CompressionFormat:
    """Determine compression format using standard magic byte headers."""
    if header_bytes.startswith(MAGIC_GZIP):
        return CompressionFormat.GZIP
    elif header_bytes.startswith(MAGIC_BZIP2):
        return CompressionFormat.BZIP2
    elif header_bytes.startswith(MAGIC_XZ):
        return CompressionFormat.XZ
    elif header_bytes.startswith(MAGIC_ZSTD):
        return CompressionFormat.ZSTD
    elif len(header_bytes) > 0 and all(b >= 32 or b in (9, 10, 13) for b in header_bytes[:32]):
        # Printable ASCII / UTF-8 plain text data
        return CompressionFormat.UNCOMPRESSED
    return CompressionFormat.UNKNOWN


def inspect_file(
    file_path_or_buffer: Union[str, Path, BinaryIO],
    filename_override: Optional[str] = None,
    max_size_bytes: int = DEFAULT_MAX_COMPRESSED_SIZE,
    allow_uncompressed: bool = True
) -> FileInspection:
    """Perform non-destructive intake inspection of an export file.

    Reads in bounded chunks, calculates compressed-file SHA-256, and verifies
    magic bytes. Does NOT decompress the full stream or load the whole file into RAM.

    Args:
        file_path_or_buffer: Path to file or open binary stream (e.g. from Streamlit).
        filename_override: Display name if passing a binary stream.
        max_size_bytes: Maximum allowed compressed file size.
        allow_uncompressed: Whether to accept uncompressed plain text exports.

    Returns:
        FileInspection object containing verified metadata.
    """
    notes = []
    is_path = isinstance(file_path_or_buffer, (str, Path))

    if is_path:
        path_obj = validate_input_path(file_path_or_buffer, must_exist=True)
        file_size = path_obj.stat().st_size
        filename = path_obj.name
        f = open(path_obj, "rb")
    else:
        f = file_path_or_buffer
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        f.seek(0)
        filename = filename_override or getattr(f, "name", "uploaded_export.bin")
        path_obj = Path(filename)

    try:
        # Check size constraints
        if file_size > max_size_bytes:
            raise ResourceLimitExceededError(
                f"File size ({file_size:,} bytes) exceeds configured maximum limit of {max_size_bytes:,} bytes."
            )

        if file_size == 0:
            notes.append("Input file is completely empty (0 bytes).")
            return FileInspection(
                path=str(path_obj),
                filename=filename,
                file_size_bytes=0,
                detected_compression=CompressionFormat.UNKNOWN,
                sha256_compressed="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                is_empty=True,
                is_valid_header=False,
                header_hex="",
                inspection_notes=notes
            )

        # Read first 16 bytes for header signature detection
        header = f.read(16)
        header_hex = header.hex()
        format_detected = detect_compression_format(header)

        if format_detected == CompressionFormat.UNKNOWN:
            notes.append("Unrecognized compression header signature.")
        elif format_detected == CompressionFormat.UNCOMPRESSED:
            if not allow_uncompressed:
                raise UnsupportedFormatError(
                    "Plain uncompressed exports are disallowed by current configuration."
                )
            notes.append("File appears to be uncompressed text.")
        else:
            notes.append(f"Detected valid {format_detected.value} header.")

        # Compute SHA-256 over compressed bytes using chunked streaming
        f.seek(0)
        hasher = hashlib.sha256()
        bytes_read = 0

        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)
            bytes_read += len(chunk)

        compressed_sha256 = hasher.hexdigest()
        is_valid_header = format_detected not in (CompressionFormat.UNKNOWN,)

        return FileInspection(
            path=str(path_obj),
            filename=filename,
            file_size_bytes=file_size,
            detected_compression=format_detected,
            sha256_compressed=compressed_sha256,
            is_empty=False,
            is_valid_header=is_valid_header,
            header_hex=header_hex,
            inspection_notes=notes
        )

    finally:
        if is_path and f:
            f.close()
        elif hasattr(f, "seek"):
            f.seek(0)

