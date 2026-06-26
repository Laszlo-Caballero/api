import json
import threading
import time
import shutil
import sys
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import tkinter as tk
from tkinter import filedialog

import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import pyodbc
import pandas as pd
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("api")

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.resolve()

CONFIG_FILE = get_base_dir() / "config.json"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# --------------------
# DB CONNECTION UTILS
# --------------------
def get_sqlite_connection(primary_path, fallback_path=None):
    """
    Attempts to connect to primary SQLite database.
    If it fails, falls back to fallback_path database.
    """
    try:
        if primary_path and Path(primary_path).exists():
            conn = sqlite3.connect(str(primary_path), timeout=5)
            return conn, "PRIMARY"
        else:
            raise Exception("Primary path does not exist or is empty")
    except Exception as e:
        logger.error(f"Primary DB failed: {e}")
        if fallback_path:
            try:
                if Path(fallback_path).exists():
                    conn = sqlite3.connect(str(fallback_path), timeout=5)
                    return conn, "FALLBACK"
                else:
                    raise Exception("Fallback path does not exist or is empty")
            except Exception as e2:
                logger.error(f"Fallback DB failed: {e2}")
    return None, "FAILED"

def get_access_connection(path):
    """
    Attempts to connect to Microsoft Access DB.
    """
    try:
        if path and Path(path).exists():
            conn_str = (
                r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
                rf"DBQ={path};"
            )
            conn = pyodbc.connect(conn_str, timeout=5)
            return conn
        else:
            raise Exception("Access DB path does not exist or is empty")
    except Exception as e:
        logger.error(f"Access DB error: {e}")
        return None

# --------------------
# API ENDPOINTS
# --------------------
@app.get("/maquina-a/{id}")
async def get_maquina_a(id: str):
    config = load_config()
    maquina_a = config.get("maquina_a", "")
    if not maquina_a:
        return {"error": "Maquina A path is not configured"}

    file_path = Path(maquina_a).joinpath("dbreport.nii").resolve()
    conn = get_access_connection(file_path)

    if not conn:
        return {"error": "Maquina A no disponible"}

    try:
        query = f"""
                select p.exid,pt.assayid, pt.assayname, rd.rlu, pt.answer, r.unit, rd.enddate, rd.endtime
                    from 
                    ((((patient p inner join patientrecord pt on p.id = pt.patientid)
                    inner join journal j on j.patientid = p.id)
                    inner join result r on r.journalid = j.id and r.asyid = pt.assayid)
                    inner join resultdetail rd on rd.resultid = r.id)
                    WHERE 
                        p.exid = '{id}'
                """
        df = pd.read_sql_query(query, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error querying Maquina A: {e}")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.get("/maquina-b/{id}")
async def get_maquina_b(id: str):
    config = load_config()
    maquina_b = config.get("maquina_b", "")
    origen_maquina_b = config.get("origen_maquina_b", "")

    primary_db = Path(maquina_b).joinpath("User.db").resolve() if maquina_b else None
    fallback_db = Path(origen_maquina_b).joinpath("User.db").resolve() if origen_maquina_b else None

    conn, source = get_sqlite_connection(primary_db, fallback_db)

    if conn is None:
        return {"error": "No database available"}

    logger.info(f"Connected using: {source}")

    try:
        query = f"""
            select p.id, e.id as idexamen, p.barcode, e.Abbr, r.result, u.name, r.resultTime  from smpinfo p
            inner join smpresult r on r.smpinfodbid = p.id
            inner join iteminfo e on e.id = r.itemdbid
            inner join unit u on u.id = e.unitid
            where p.barcode like '%{id}%'
        """
        df = pd.read_sql_query(query, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error querying Maquina B: {e}")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


@app.get("/maquina-b-count")
async def get_maquina_b_count():
    config = load_config()
    maquina_b = config.get("maquina_b", "")
    origen_maquina_b = config.get("origen_maquina_b", "")

    primary_db = Path(maquina_b).joinpath("User.db").resolve() if maquina_b else None
    fallback_db = Path(origen_maquina_b).joinpath("User.db").resolve() if origen_maquina_b else None

    conn, source = get_sqlite_connection(primary_db, fallback_db)

    if conn is None:
        return {"error": "No database available"}

    try:
        query = """
            select count(*) as count from smpinfo p
            inner join smpresult r on r.smpinfodbid = p.id
            inner join iteminfo e on e.id = r.itemdbid
            inner join unit u on u.id = e.unitid        
        """
        df = pd.read_sql_query(query, conn)
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error querying Maquina B Count: {e}")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


# --------------------
# CONFIG
# --------------------
def load_config():
    defaults = {
        "maquina_a": "",
        "maquina_b": "",
        "origen_maquina_b": "",
        "host": "0.0.0.0",
        "port": 2314,
        "sync_interval": 120
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                for k, v in defaults.items():
                    if k not in config:
                        config[k] = v
                return config
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
    return defaults


def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving config file: {e}")


# --------------------
# BACKGROUND REPLICATION (AUTO-SYNC EVERY X SECONDS)
# --------------------
def sync_db_loop():
    logger.info("Background SQLite replication task started.")
    while True:
        sleep_time = 120
        try:
            config = load_config()
            maquina_b = config.get("maquina_b", "")
            origen_maquina_b = config.get("origen_maquina_b", "")
            sleep_time = max(5, config.get("sync_interval", 120))  # minimum 5 seconds to avoid performance issues

            if maquina_b and origen_maquina_b:
                src = Path(origen_maquina_b).joinpath("User.db").resolve()
                dst_dir = Path(maquina_b).resolve()
                dst = dst_dir.joinpath("User.db")

                if src.exists():
                    dst_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    logger.info(f"Replication sync successful: {src} -> {dst}")
                else:
                    logger.warning(f"Replication skipped: Source SQLite file does not exist: {src}")
            else:
                logger.info("Replication skipped: Maquina B or Origen Maquina B paths not configured.")
        except Exception as e:
            logger.error(f"Replication error (PC offline or path unavailable): {e}")

        # Sleep for configured seconds
        time.sleep(sleep_time)


# --------------------
# VENTANA CONFIG
# --------------------
def open_config_window():
    config = load_config()

    root = tk.Tk()
    root.title("Configuración de Servicio")

    input_var = tk.StringVar(value=config["maquina_a"])
    output_var = tk.StringVar(value=config["maquina_b"])
    backup_var = tk.StringVar(value=config["origen_maquina_b"])
    host_var = tk.StringVar(value=config["host"])
    port_var = tk.IntVar(value=config["port"])
    sync_var = tk.IntVar(value=config["sync_interval"])

    def select_input():
        folder = filedialog.askdirectory()
        if folder:
            input_var.set(folder)

    def select_output():
        folder = filedialog.askdirectory()
        if folder:
            output_var.set(folder)

    def select_backup():
        folder = filedialog.askdirectory()
        if folder:
            backup_var.set(folder)

    def save():
        try:
            port_val = int(port_var.get())
        except ValueError:
            port_val = 2314

        try:
            sync_val = int(sync_var.get())
        except ValueError:
            sync_val = 120

        save_config({
            "maquina_a": input_var.get(),
            "maquina_b": output_var.get(),
            "origen_maquina_b": backup_var.get(),
            "host": host_var.get(),
            "port": port_val,
            "sync_interval": sync_val
        })
        root.destroy()

    tk.Label(root, text="Carpeta Maquina A (Access)").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(root, textvariable=input_var, width=60).grid(row=0, column=1, padx=5, pady=5)
    tk.Button(root, text="...", command=select_input).grid(row=0, column=2, padx=5, pady=5)

    tk.Label(root, text="Carpeta Lectura Maquina B (Local)").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(root, textvariable=output_var, width=60).grid(row=1, column=1, padx=5, pady=5)
    tk.Button(root, text="...", command=select_output).grid(row=1, column=2, padx=5, pady=5)

    tk.Label(root, text="Carpeta Origen Maquina B (Remoto/Red)").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(root, textvariable=backup_var, width=60).grid(row=2, column=1, padx=5, pady=5)
    tk.Button(root, text="...", command=select_backup).grid(row=2, column=2, padx=5, pady=5)

    tk.Label(root, text="IP / Host").grid(row=3, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(root, textvariable=host_var, width=60).grid(row=3, column=1, padx=5, pady=5, columnspan=2, sticky="w")

    tk.Label(root, text="Puerto").grid(row=4, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(root, textvariable=port_var, width=20).grid(row=4, column=1, padx=5, pady=5, columnspan=2, sticky="w")

    tk.Label(root, text="Intervalo de Copia (segundos)").grid(row=5, column=0, padx=5, pady=5, sticky="e")
    tk.Entry(root, textvariable=sync_var, width=20).grid(row=5, column=1, padx=5, pady=5, columnspan=2, sticky="w")

    tk.Button(root, text="Guardar", command=save).grid(row=6, column=1, pady=10)

    root.mainloop()


# --------------------
# SYSTEM TRAY
# --------------------
def create_image():
    image = Image.new("RGB", (64, 64), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 48, 48), fill="blue")
    return image


def on_open(icon, item):
    threading.Thread(target=open_config_window, daemon=True).start()


def on_exit(icon, item):
    icon.stop()


def run_tray():
    icon = pystray.Icon(
        "MiServicio",
        create_image(),
        "Mi Servicio",
        menu=pystray.Menu(
            item("Configurar", on_open),
            item("Salir", on_exit),
        ),
    )
    icon.run()


# --------------------
# UVICORN
# --------------------
def run_api():
    from tkinter import messagebox
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
