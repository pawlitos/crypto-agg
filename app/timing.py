import logging
import time
from contextlib import contextmanager

# Uvicorn's own logger, so our messages match the server's "INFO:     ..." output.
logger = logging.getLogger("uvicorn")


@contextmanager
def log_time(label: str):
    """Log how long the code inside a `with log_time(...)` block took."""
    start = time.perf_counter()
    try:
        yield
    finally:
        ms = (time.perf_counter() - start) * 1000
        logger.info("%s took %.0f ms", label, ms)
