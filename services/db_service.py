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
            print(f"Access DB path does not exist or is empty: {path}")
            raise Exception("Access DB path does not exist or is empty")
    except Exception as e:
        logger.error(f"Access DB error: {e}")
        return None
