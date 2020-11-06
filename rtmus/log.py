from time import time

from attr import dataclass


@dataclass
class DeltaLogger:
    base_time = time()
    last_time = time()

    def log(self, msg):
        log_time = time() - self.base_time
        delta = log_time - self.last_time
        print(f"time: {log_time:.4f}\ttime delta: {delta:.4f}\t{msg}")
        self.last_time = log_time


logger = DeltaLogger()
