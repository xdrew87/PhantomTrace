"""Logging utility for PhantomTrace."""
import logging
from pathlib import Path
from datetime import datetime


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(f"phantomtrace.{name}")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    log_file = log_dir / f"phantomtrace_{datetime.now().strftime('%Y%m%d')}.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    logger.addHandler(fh)
    return logger
