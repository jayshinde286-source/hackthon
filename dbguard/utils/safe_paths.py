"""Path validation and safe filesystem utility functions.

Guards against path traversal, symlink attacks, and inadvertent file overwrites.
"""

import os
from pathlib import Path
from typing import Union
from dbguard.exceptions import SecurityError


def validate_input_path(filepath: Union[str, Path], must_exist: bool = True) -> Path:
    """Validate and resolve an input file path safely.

    Args:
        filepath: Input path string or Path object.
        must_exist: Whether the target file must already exist.

    Returns:
        Resolved absolute Path.

    Raises:
        SecurityError: If path contains null bytes, invalid characters, or fails safety checks.
        FileNotFoundError: If must_exist is True and file does not exist.
        IsADirectoryError: If path points to a directory when a file is expected.
    """
    if isinstance(filepath, str) and "\0" in filepath:
        raise SecurityError("Path contains prohibited null byte (directory traversal attempt).")

    p = Path(filepath).expanduser().resolve()

    if must_exist:
        if not p.exists():
            raise FileNotFoundError(f"Target file does not exist: {p}")
        if p.is_dir():
            raise IsADirectoryError(f"Target is a directory, not a file: {p}")
        if not os.access(p, os.R_OK):
            raise PermissionError(f"File is not readable: {p}")

    return p


def safe_output_path(destination: Union[str, Path], allow_overwrite: bool = False) -> Path:
    """Verify that an output path is safe and will not clobber protected files.

    Args:
        destination: Desired destination file path.
        allow_overwrite: Whether overwriting an existing file is permitted.

    Returns:
        Resolved Path.
    """
    if isinstance(destination, str) and "\0" in destination:
        raise SecurityError("Path contains null byte.")

    dest = Path(destination).expanduser().resolve()
    if dest.exists() and not allow_overwrite:
        raise FileExistsError(f"Target destination already exists and allow_overwrite is False: {dest}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest

