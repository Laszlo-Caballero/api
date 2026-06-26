import time
import shutil
import logging
from pathlib import Path
from utils.config import load_config

logger = logging.getLogger("api")

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
