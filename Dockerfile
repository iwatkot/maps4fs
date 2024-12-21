FROM python:3.11-slim-buster

# Dependencies for opencv.
RUN apt-get update && apt-get install -y \
    libgl1-mesa-dev \
    libglib2.0-0

WORKDIR /usr/src/app

COPY .streamlit /usr/src/app/.streamlit
COPY data /usr/src/app/data
COPY docs /usr/src/app/docs
COPY webui /usr/src/app/webui
COPY requirements.txt /usr/src/app/requirements.txt

# RUN pip install "opencv-python" "pyproj" "folium" "geopy" "pympler" "streamlit-stl==0.0.2" "osmnx>=2.0.0" "fast-simplification" "rasterio" "trimesh" "streamlit" "maps4fs"
RUN pip install -r requirements.txt

EXPOSE 8501

ENV PYTHONPATH .:${PYTHONPATH}
CMD ["streamlit", "run", "./webui/webui.py"]