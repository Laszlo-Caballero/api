import tkinter as tk
from tkinter import filedialog
from utils.config import load_config, save_config

def open_config_window():
    config = load_config()

    root = tk.Tk()
    root.title("Configuración de Servicio")

    input_var = tk.StringVar(value=config["maquina_a"])
    output_var = tk.StringVar(value=config["maquina_b"])
    backup_var = tk.StringVar(value=config["origen_maquina_b"])
    host_var = tk.StringVar(value=config["host"])
    port_var = tk.StringVar(value=str(config["port"]))
    sync_var = tk.StringVar(value=str(config["sync_interval"]))

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
