import sys

# PyInstaller stream configuration
if sys.stdout is None or sys.stderr is None:
    class DummyStream:
        def write(self, data):
            pass
        def flush(self):
            pass
        def isatty(self):
            return False

    if sys.stdout is None:
        sys.stdout = DummyStream()
    if sys.stderr is None:
        sys.stderr = DummyStream()

import threading
import uvicorn
import tkinter as tk
from tkinter import messagebox

# Initialize logging config first so all other modules use configured logger
from utils.logging_config import logger
from utils.config import load_config
from services.sync_service import sync_db_loop
from controllers.api import app
from ui.system_tray import run_tray

def run_api():
    config = load_config()
    host = config.get("host", "0.0.0.0")
    port = config.get("port", 2314)
    try:
        logger.info(f"Starting API on {host}:{port}")
        uvicorn.run(app, host=host, port=port, log_level="info")
    except Exception as e:
        logger.error(f"Failed to start API: {e}")
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Error de API", 
                f"No se pudo iniciar la API en {host}:{port}.\n\n"
                f"Detalle del error: {e}\n\n"
                "Asegúrate de que el puerto no esté en uso por otra instancia "
                "del servicio o que la dirección IP sea correcta."
            )
            root.destroy()
        except Exception:
            pass

if __name__ == "__main__":
    # Start API thread
    threading.Thread(target=run_api, daemon=True).start()

    # Start sync daemon thread
    threading.Thread(target=sync_db_loop, daemon=True).start()

    # Run system tray
    run_tray()
