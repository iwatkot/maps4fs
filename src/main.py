import os
import time
import tkinter as tk
from tkinter import ttk

import generate


def start():
    lat = float(lat_entry.get())
    lon = float(lon_entry.get())
    size = int(size_var.get())
    distance = int(size / 2)

    blur_seed = int(blur_seed_entry.get())
    max_height = int(max_height_var.get())
    dem_settings = generate.DemSettings(blur_seed, max_height)

    result_label.config(text="Generating...")
    root.update()
    generate.Map((lat, lon), distance, dem_settings)
    result_label.config(text="Saved in:")
    path_label.config(text=f"{generate.OUTPUT_DIR}")
    for i in range(5, 0, -1):
        close_time_label.config(text=f"Closing in {i} seconds...")
        root.update()
        time.sleep(1)
    root.destroy()


def open_output_dir(event):
    os.startfile(generate.OUTPUT_DIR)


root = tk.Tk()
root.geometry("300x300")

lat_label = tk.Label(root, text="Latitude:")
lat_label.grid(row=0, column=0)
lat_entry = tk.Entry(root)
lat_entry.insert(0, "")
lat_entry.grid(row=0, column=1)

lon_label = tk.Label(root, text="Longitude:")
lon_label.grid(row=1, column=0)
lon_entry = tk.Entry(root)
lon_entry.insert(0, "")
lon_entry.grid(row=1, column=1)

size_label = tk.Label(root, text="Map size:")
size_label.grid(row=2, column=0)
size_var = tk.StringVar(root)
size_var.set("2048")
size_menu = tk.OptionMenu(root, size_var, *generate.MAP_SIZES)
size_menu.grid(row=2, column=1)

button = tk.Button(root, text="Generate map", command=start)
button.grid(row=3, column=0, columnspan=2)

result_label = tk.Label(root, text="")
result_label.grid(row=4, column=0)

path_label = tk.Label(root, text="", fg="blue", cursor="hand2")
path_label.grid(row=4, column=1)
path_label.bind("<Button-1>", open_output_dir)

close_time_label = tk.Label(root, text="")
close_time_label.grid(row=5, column=0)

separator = ttk.Separator(root, orient="horizontal")
separator.grid(row=6, column=0, columnspan=2, sticky="ew")

advanced_options = tk.Label(root, text="Advanced options")
advanced_options.grid(row=7, column=0, columnspan=2)

blur_seed_label = tk.Label(root, text="Blur seed:")
blur_seed_label.grid(row=8, column=0)
blur_seed_entry = tk.Entry(root)
blur_seed_entry.insert(0, "5")
blur_seed_entry.grid(row=8, column=1)

max_height_label = tk.Label(root, text="Max height:")
max_height_label.grid(row=9, column=0)
max_height_var = tk.StringVar(root)
max_height_var.set("400")
max_height_menu = tk.OptionMenu(root, max_height_var, *list(generate.MAX_HEIGHTS.keys()))
max_height_menu.grid(row=9, column=1)

root.mainloop()
