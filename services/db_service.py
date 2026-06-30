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

def get_access_connection(path):
    """
    Attempts to connect to Microsoft Access DB.
    To avoid driver crashes with non-standard extensions (like .nii)
    and avoid lock errors if the file is in use, we copy it to a temp file
    with a proper .accdb extension first.
    """
    temp_path = None
    try:
        if path and Path(path).exists():
            temp_dir = Path(tempfile.gettempdir())
            suffix = ".accdb"
            temp_path = temp_dir / f"temp_access_db_{time.time_ns()}{suffix}"
            
            # Copy to temp file
            shutil.copy2(path, temp_path)
            logger.info(f"Copied {path} to temporary file {temp_path}")
            
            conn_str = (
                r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
                rf"DBQ={temp_path};"
            )
            conn = pyodbc.connect(conn_str, timeout=5)
            # Store temp path on connection object to delete it after closing
            conn.temp_path = temp_path
            return conn
        else:
            logger.error(f"Access DB path does not exist or is empty: {path}")
            return None
    except Exception as e:
        logger.error(f"Access DB error during connection setup: {e}", exc_info=True)
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
                logger.info(f"Cleaned up temp file after error: {temp_path}")
            except Exception:
                pass
        return None

