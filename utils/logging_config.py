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

    # File Handler (INFO and above to trace steps before a crash)
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.error(f"Could not setup file logging: {e}")

    return logger

# Initialize logger immediately so modules importing it can use it
logger = setup_logging()

import sys
import threading
import tkinter as tk
from tkinter import messagebox

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Unhandled exception in main thread", exc_info=(exc_type, exc_value, exc_traceback))
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Error Inesperado",
            f"Ocurrió un error inesperado en la aplicación:\n\n{exc_value}\n\nRevisa el archivo errors.txt para más detalles."
        )
        root.destroy()
    except Exception:
        pass

def handle_thread_exception(args):
    logger.critical("Unhandled exception in background thread", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Error Inesperado (Hilo)",
            f"Ocurrió un error en un proceso en segundo plano:\n\n{args.exc_value}\n\nRevisa el archivo errors.txt para más detalles."
        )
        root.destroy()
    except Exception:
        pass

sys.excepthook = handle_exception
threading.excepthook = handle_thread_exception

