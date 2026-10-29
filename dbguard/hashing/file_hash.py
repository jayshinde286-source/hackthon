"""Compressed file SHA-256 computation using chunked streaming."""

import hashlib
from pathlib import Path
from typing import BinaryIO, Union
from dbguard.utils.safe_paths import validate_input_path


def compute_file_sha256(file_path_or_buffer: Union[str, Path, BinaryIO], chunk_size: int = 65_536) -> str:
    """Compute SHA-256 hash over exact compressed file bytes in O(chunk_size) memory.

    Args:
        file_path_or_buffer: Path to file or binary stream.
        chunk_size: Bounded chunk read size.

    Returns:
        Hexadecimal SHA-256 digest.
    """
    hasher = hashlib.sha256()

    if isinstance(file_path_or_buffer, (str, Path)):
        p = validate_input_path(file_path_or_buffer, must_exist=True)
        with open(p, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
    else:
        stream = file_path_or_buffer
        pos = stream.tell() if hasattr(stream, "tell") else None
        if hasattr(stream, "seek"):
            stream.seek(0)
        while chunk := stream.read(chunk_size):
            hasher.update(chunk)
        if pos is not None and hasattr(stream, "seek"):
            stream.seek(pos)

    return hasher.hexdigest()

