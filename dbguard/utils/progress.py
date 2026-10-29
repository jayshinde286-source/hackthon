"""Progress tracking callbacks for bounded streaming operations."""

from typing import Callable, Optional


class StreamProgressTracker:
    """Tracks byte-level progress through an input stream with optional callback."""

    def __init__(self, total_bytes: Optional[int] = None, callback: Optional[Callable[[int, Optional[int]], None]] = None):
        self.total_bytes = total_bytes
        self.bytes_processed = 0
        self.callback = callback

    def update(self, chunk_size: int) -> None:
        """Increment bytes processed and invoke callback if registered."""
        self.bytes_processed += chunk_size
        if self.callback:
            self.callback(self.bytes_processed, self.total_bytes)

    @property
    def percentage(self) -> Optional[float]:
        """Current completion percentage if total bytes is known."""
        if self.total_bytes and self.total_bytes > 0:
            return min(100.0, (self.bytes_processed / self.total_bytes) * 100.0)
        return None

