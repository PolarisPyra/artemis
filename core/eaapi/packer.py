import math


class Packer:
    def __init__(self, offset: int = 0):
        self._word_cursor = offset
        self._short_cursor = offset
        self._byte_cursor = offset
        self._boundary = offset % 4

    def _next_block(self) -> int:
        self._word_cursor += 4
        return self._word_cursor - 4

    def request_allocation(self, size: int) -> int:
        if size == 0:
            return self._word_cursor
        elif size == 1:
            if self._byte_cursor % 4 == self._boundary:
                self._byte_cursor = self._next_block() + 1
            else:
                self._byte_cursor += 1
            return self._byte_cursor - 1
        elif size == 2:
            if self._short_cursor % 4 == self._boundary:
                self._short_cursor = self._next_block() + 2
            else:
                self._short_cursor += 2
            return self._short_cursor - 2
        else:
            old_cursor = self._word_cursor
            for _ in range(math.ceil(size / 4)):
                self._word_cursor += 4
            return old_cursor

    def notify_skipped(self, no_bytes: int) -> None:
        for _ in range(math.ceil(no_bytes / 4)):
            self.request_allocation(4)


__all__ = ("Packer", )
