import os
from time import time

import streamlit as st

import maps4fs as mfs

working_directory = os.getcwd()
archives_directory = os.path.join(working_directory, "archives")
maps_directory = os.path.join(working_directory, "maps")
os.makedirs(archives_directory, exist_ok=True)
os.makedirs(maps_directory, exist_ok=True)
download_path = None
logger = mfs.Logger(__name__, level="DEBUG")

if "generated" not in st.session_state:
    st.session_state.generated = False


def launch_process():
    game = mfs.Game.from_code(game_code_input)

    try:
        lat, lon = map(float, lat_lon_input.split(","))
    except ValueError:
        st.error("Invalid latitude and longitude!")
        return

    coordinates = (lat, lon)

    map_size = map_size_input[0]
    if not isinstance(map_size, int):
        st.error("Invalid map size!")
        return

    distance = int(map_size / 2)

    max_height = max_height_input
    if not isinstance(max_height, int):
        st.error("Invalid maximum height!")
        return
    blur_seed = blur_seed_input
    if not isinstance(blur_seed, int):
        st.error("Invalid blur seed!")
        return

    session_name = f"{int(time())}"

    st.success("Started map generation...")
    map_directory = os.path.join(maps_directory, session_name)
    os.makedirs(map_directory, exist_ok=True)

    mp = mfs.Map(
        game,
        coordinates,
        distance,
        map_directory,
        blur_seed=blur_seed,
        max_height=max_height,
        logger=logger,
    )
    mp.generate()
    archive_path = mp.pack(os.path.join(archives_directory, session_name))

    global download_path
    download_path = archive_path

    st.session_state.generated = True

    st.success("Map generation completed!")


# UI Elements
st.write("Select the game for which you want to generate the map:")
game_code_input = st.selectbox(
    "Game",
    options=["FS22", "FS25"],
    key="game_code",
    label_visibility="collapsed",
)

st.write("Enter latitude and longitude of the center point of the map:")
lat_lon_input = st.text_input(
    "Latitude and Longitude", "45.2602, 19.8086", key="lat_lon", label_visibility="collapsed"
)

st.write("Select size of the map:")
map_size_input = st.selectbox(
    "Map Size",
    options=[
        (2048, "2048 x 2048 meters"),
        (4096, "4096 x 4096 meters"),
        (8192, "8192 x 8192 meters"),
        (16384, "16384 x 16384 meters"),
    ],
    format_func=lambda x: x[1],
    key="size",
    label_visibility="collapsed",
)

st.write("Enter maximum height:")
max_height_input = st.number_input(
    "Maximum Height",
    value=200,
    key="max_height",
    label_visibility="collapsed",
    min_value=10,
    max_value=3000,
)

st.write("Enter blur seed:")
blur_seed_input = st.number_input(
    "Blur Seed",
    value=5,
    key="blur_seed",
    label_visibility="collapsed",
    min_value=1,
    max_value=1000,
)

if st.button("Generate", key="launch_btn"):
    launch_process()

if st.session_state.generated:
    with open(download_path, "rb") as f:
        st.download_button(
            label="Download",
            data=f,
            file_name=f"{download_path.split('/')[-1]}",
            mime="application/zip",
        )

    st.session_state.generated = False
