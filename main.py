import json
import threading
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


CONFIG_FILE = "config.json"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


# --------------------
# API
# --------------------
@app.get("/maquina-a/{id}")
async def get_maquina_a(id: str):
    config = load_config()
    maquina_a = config["maquina_a"]

    file_path = Path(maquina_a).joinpath("dbreport.nii").resolve()
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        rf"DBQ={file_path};"
    )
    conn = pyodbc.connect(conn_str)

    print(id)

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


@app.get("/maquina-b/{id}")
async def get_maquina_b(id: str):
    config = load_config()

    maquina_b = config["maquina_b"]

    file_path = Path(maquina_b).joinpath("User.db").resolve()

    conn = sqlite3.connect(file_path)

    query = f"""
        select p.id, e.id as idexamen, p.barcode, e.Abbr, r.result, u.name, r.resultTime  from smpinfo p
        inner join smpresult r on r.smpinfodbid = p.id
        inner join iteminfo e on e.id = r.itemdbid
        inner join unit u on u.id = e.unitid
        where p.barcode like '%{id}%'
    """

    df = pd.read_sql_query(query, conn)

    return df.to_dict(orient="records")


@app.get("/maquina-b-count")
async def get_maquina_b_count():
    config = load_config()
    maquina_b = config["maquina_b"]
    file_path = Path(maquina_b).joinpath("User.db").resolve()
    conn = sqlite3.connect(file_path)
    query = """
        select count(*) as count from smpinfo p
        inner join smpresult r on r.smpinfodbid = p.id
        inner join iteminfo e on e.id = r.itemdbid
        inner join unit u on u.id = e.unitid        
    """
    df = pd.read_sql_query(query, conn)
    return df.to_dict(orient="records")


# --------------------
# CONFIG
# --------------------
def load_config():
    if Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {"maquina_a": "", "maquina_b": ""}


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


# --------------------
# VENTANA CONFIG
# --------------------
def open_config_window():
    config = load_config()

    root = tk.Tk()
    root.title("Configuración")

    input_var = tk.StringVar(value=config["maquina_a"])
    output_var = tk.StringVar(value=config["maquina_b"])

    def select_input():
        folder = filedialog.askdirectory()
        if folder:
            input_var.set(folder)

    def select_output():
        folder = filedialog.askdirectory()
        if folder:
            output_var.set(folder)

    def save():
        save_config({"maquina_a": input_var.get(), "maquina_b": output_var.get()})

        root.destroy()

    tk.Label(root, text="Carpeta origen").grid(row=0, column=0, padx=5, pady=5)

    tk.Entry(root, textvariable=input_var, width=60).grid(row=0, column=1)

    tk.Button(root, text="...", command=select_input).grid(row=0, column=2)

    tk.Label(root, text="Carpeta destino").grid(row=1, column=0, padx=5, pady=5)

    tk.Entry(root, textvariable=output_var, width=60).grid(row=1, column=1)

    tk.Button(root, text="...", command=select_output).grid(row=1, column=2)

    tk.Button(root, text="Guardar", command=save).grid(row=2, column=1, pady=10)

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
    uvicorn.run(app, host="0.0.0.0", port=2314, log_level="info")


if __name__ == "__main__":
    threading.Thread(target=run_api, daemon=True).start()

    run_tray()
