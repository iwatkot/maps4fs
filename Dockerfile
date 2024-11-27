FROM python:3.11-slim-buster

# Dependencies for opencv.
RUN apt-get update && apt-get install -y \
    libgl1-mesa-dev \
    libglib2.0-0

WORKDIR /usr/src/app

COPY data /usr/src/app/data
COPY webui /usr/src/app/webui

RUN pip install "opencv-python" "pyproj" "folium" "geopy" "osmnx<2.0.0" "fast-simplification" "rasterio" "trimesh" "streamlit" "maps4fs"

EXPOSE 8501

ENV PYTHONPATH .:${PYTHONPATH}
CMD ["streamlit", "run", "./webui/webui.py"]