import sys
from time import time

from attr import dataclass


@dataclass
class DeltaLogger:
    base_time: float = time()
    last_time: float = 0.0

    def log(self, msg: str):
        log_time = time() - self.base_time
        delta = log_time - self.last_time
        sys.stderr.write(f"time: {log_time:8.4f}▐time delta: {delta:.6f}▐{msg}\n")
        self.last_time = log_time


logger = DeltaLogger()
