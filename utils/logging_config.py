import logging
from pathlib import Path
from utils.config import get_base_dir

def setup_logging():
    base_dir = get_base_dir()
    log_file = base_dir / "errors.txt"

    logger = logging.getLogger("api")
    logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Console Handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (ERROR and above)
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.error(f"Could not setup file logging: {e}")

    return logger

# Initialize logger immediately so modules importing it can use it
logger = setup_logging()
