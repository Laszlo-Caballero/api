import threading
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

from ui.config_window import open_config_window

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
