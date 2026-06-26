import json
import sys
from pathlib import Path
import logging

logger = logging.getLogger("api")

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        # Since this utility is in utils/config.py (a subfolder),
        # the root directory of the application is the parent directory.
        return Path(__file__).parent.parent.resolve()

CONFIG_FILE = get_base_dir() / "config.json"

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
