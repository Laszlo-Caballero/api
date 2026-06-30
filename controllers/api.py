import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.config import load_config
from services.db_service import get_sqlite_connection, get_access_connection

logger = logging.getLogger("api")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.get("/maquina-a/{id}")
async def get_maquina_a(id: str):
    config = load_config()
    maquina_a = config.get("maquina_a", "")
    if not maquina_a:
        logger.warning("Maquina A path is not configured in config.json")
        return {"error": "Maquina A path is not configured"}

    file_path = Path(maquina_a).joinpath("dbreport.nii").resolve()
    logger.info(f"Querying Maquina A for id: {id}")
    logger.info(f"Connecting to Access DB at: {file_path}")
    
    conn = None
    try:
        conn = get_access_connection(file_path)
    except Exception as e:
        logger.error(f"Error during get_access_connection: {e}", exc_info=True)
        return {"error": f"Error conectando a Maquina A: {e}"}

    if not conn:
        logger.warning("Maquina A connection is None")
        return {"error": "Maquina A no disponible (conexión fallida)"}

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
        logger.info("Executing query on Access DB...")
        df = pd.read_sql_query(query, conn)
        logger.info("Query completed successfully")
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error querying Maquina A: {e}", exc_info=True)
        return {"error": f"Error al consultar Maquina A: {e}"}
    finally:
        if conn:
            logger.info("Closing Access DB connection")
            temp_path = getattr(conn, "temp_path", None)
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Error closing Access DB connection: {e}", exc_info=True)
            
            if temp_path and Path(temp_path).exists():
                try:
                    Path(temp_path).unlink()
                    logger.info(f"Deleted temporary DB file: {temp_path}")
                except Exception as e:
                    logger.error(f"Error deleting temporary DB file {temp_path}: {e}")


@app.get("/maquina-b/{id}")
async def get_maquina_b(id: str):
    config = load_config()
    maquina_b = config.get("maquina_b", "")
    origen_maquina_b = config.get("origen_maquina_b", "")

    primary_db = Path(maquina_b).joinpath("User.db").resolve() if maquina_b else None
    fallback_db = (
        Path(origen_maquina_b).joinpath("User.db").resolve()
        if origen_maquina_b
        else None
    )

    conn, source = get_sqlite_connection(primary_db, fallback_db)

    if conn is None:
        return {"error": "No database available"}

    logger.info(f"Connected to SQLite using: {source}")

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
        logger.error(f"Error querying Maquina B: {e}", exc_info=True)
        return []
    finally:
        if conn:
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
    fallback_db = (
        Path(origen_maquina_b).joinpath("User.db").resolve()
        if origen_maquina_b
        else None
    )

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
        logger.error(f"Error querying Maquina B Count: {e}", exc_info=True)
        return []
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
