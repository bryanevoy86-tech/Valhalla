import logging
import os
from logging.handlers import RotatingFileHandler

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_PATH = os.getenv("LOG_PATH", "valhalla.log")

def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(LOG_LEVEL)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root.addHandler(sh)

    fh = RotatingFileHandler(LOG_PATH, maxBytes=5_000_000, backupCount=3)
    fh.setFormatter(fmt)
    root.addHandler(fh)
