import sys
from time import time
from typing import List

from attr import dataclass


@dataclass
class DeltaLogger:
    base_time: float = time()
    last_time: float = 0.0
    buffer: List[str] = []

    def log(self, msg: str, *args, **kwargs):
        log_time = time() - self.base_time
        delta = log_time - self.last_time
        msg = msg.format(*args, **kwargs)
        self.buffer.append(f"time: {log_time:8.4f}▐time delta: {delta:.6f}▐{msg}\n")
        self.last_time = log_time

    def flush(self):
        sys.stderr.write("".join(self.buffer))
        self.buffer.clear()


logger = DeltaLogger()
