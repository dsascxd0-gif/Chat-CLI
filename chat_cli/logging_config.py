import logging
import os
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


def get_log_path() -> Path:
    base = Path(__file__).parent.parent / "logs"
    base.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime("%Y-%m-%d")
    existing = list(base.glob(f"{today}-*.log"))
    
    n = len(existing) + 1
    return base / f"{today}-{n}.log"


def setup_logger():
    log_path = get_log_path()
    
    logger = logging.getLogger("chat_cli")
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s\n",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10*1024*1024,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.info("=== Chat CLI Started ===\n")
    
    return logger


logger = setup_logger()


def log_info(msg: str):
    logger.info(msg)


def log_warning(msg: str):
    logger.warning(msg)


def log_error(msg: str, exc_info=None):
    logger.error(msg, exc_info=exc_info)


def log_operation(action: str, details: str = ""):
    msg = f"OPERATION: {action}"
    if details:
        msg += f" - {details}"
    logger.info(msg)