import sqlite3
import pyodbc
import logging
from pathlib import Path

logger = logging.getLogger("api")


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


import tempfile
import shutil
import time
from utils.config import get_base_dir

def write_debug(msg):
    try:
        log_file = get_base_dir() / "debug_crash.txt"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
            f.flush()
    except Exception:
        pass

def get_access_connection(path):
    """
    Attempts to connect to Microsoft Access DB.
    To avoid driver crashes with non-standard extensions (like .nii)
    and avoid lock errors if the file is in use, we copy it to a temp file
    with a proper .accdb extension first.
    """
    write_debug("--- get_access_connection started ---")
    temp_path = None
    try:
        write_debug(f"Target path: {path}")
        if path and Path(path).exists():
            write_debug("Path exists. Reading first 100 bytes...")
            # Read first 100 bytes to check file type and log it
            with open(path, "rb") as f:
                header = f.read(100)
            
            write_debug(f"Read header: {header[:30].hex()}")
            logger.info(f"File header hex (first 30 bytes): {header[:30].hex()}")
            
            # Check for SQLite magic bytes
            if b"SQLite format 3" in header:
                write_debug("SQLite detected. Raising ValueError.")
                logger.error("CRITICAL: dbreport.nii is actually a SQLite 3 database, NOT a Microsoft Access database! Do not use Microsoft Access Driver.")
                raise ValueError("dbreport.nii is a SQLite database")
            
            # Check for Microsoft Access magic bytes
            is_access = b"Standard Jet DB" in header or b"Standard ACE DB" in header
            write_debug(f"Is Access DB markers present? {is_access}")
            if not is_access:
                logger.warning(f"File header does not contain standard Access DB markers ('Standard Jet DB' or 'Standard ACE DB'). Header: {header[:50]}")
            
            temp_dir = Path(tempfile.gettempdir())
            suffix = ".accdb"
            temp_path = temp_dir / f"temp_access_db_{time.time_ns()}{suffix}"
            write_debug(f"Temp file path: {temp_path}")
            
            # Copy to temp file
            write_debug("Copying file to temp path...")
            shutil.copy2(path, temp_path)
            write_debug("Copy successful.")
            logger.info(f"Copied {path} to temporary file {temp_path}")
            
            conn_str = (
                r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
                rf"DBQ={temp_path};"
            )
            write_debug(f"Connection string: {conn_str}")
            
            write_debug("Invoking pyodbc.connect...")
            conn = pyodbc.connect(conn_str, timeout=5)
            write_debug("pyodbc.connect succeeded!")
            
            # Store temp path on connection object to delete it after closing
            conn.temp_path = temp_path
            return conn
        else:
            write_debug("Path does not exist or is empty.")
            logger.error(f"Access DB path does not exist or is empty: {path}")
            return None
    except Exception as e:
        write_debug(f"Exception caught: {e}")
        logger.error(f"Access DB error during connection setup: {e}", exc_info=True)
        if temp_path and temp_path.exists():
            try:
                write_debug(f"Deleting temp path {temp_path} after error...")
                temp_path.unlink()
                write_debug("Delete successful.")
                logger.info(f"Cleaned up temp file after error: {temp_path}")
            except Exception as e2:
                write_debug(f"Failed to delete temp path: {e2}")
        return None

