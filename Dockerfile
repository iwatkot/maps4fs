FROM python:3.11-slim-buster

# Dependencies for opencv and blender.
RUN apt-get update && apt-get install -y \
    libgl1-mesa-dev \
    libglib2.0-0 \ 
    wget \
    tar \
    ca-certificates \
    xz-utils \
    libxrender1 \ 
    libxi6 \
    libxkbcommon0 \ 
    libsm6 \
    libice6 \
    libx11-6 \
    libxext6 \
    libxfixes3 \
    libxxf86vm1 \
    libxrandr2 \
    libxinerama1 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    libpulse0 \
    libopenal1 \
    libsndfile1 \
    libvorbisfile3 \
    libvorbis0a \
    libogg0 \
    libflac8 \
    libtheora0 \
    libjack-jackd2-0 \
    libavcodec58 \
    libavdevice58 \
    libavformat58 \
    libavutil56 \
    libswscale5 \
    libswresample3 \
    libavfilter7 \
    libglew2.1 \
    libopencolorio1v5 \
    libraw19 \
    libtiff5 \
    libjpeg62-turbo \
    libpng16-16 \
    libfreetype6 \
    libfontconfig1 \
    libharfbuzz0b \
    libpugixml1v5 \
    libspnav0 \
    libtinyxml2.6.2v5 \
    libjemalloc2 \
    libjemalloc-dev

# Install blender 4.3.0.
RUN wget https://download.blender.org/release/Blender4.3/blender-4.3.0-linux-x64.tar.xz && \
    tar -xvf blender-4.3.0-linux-x64.tar.xz && \
    mv blender-4.3.0-linux-x64 /opt/blender && \
    ln -s /opt/blender/blender /usr/bin/blender && \
    /usr/bin/blender --version

WORKDIR /usr/src/app

COPY .streamlit /usr/src/app/.streamlit
COPY data /usr/src/app/data
COPY docs /usr/src/app/docs
COPY webui /usr/src/app/webui
COPY requirements.txt /usr/src/app/requirements.txt

RUN pip install -r requirements.txt

# Ensure the latest version of maps4fs is installed.
RUN pip install --upgrade maps4fs

EXPOSE 8501

ENV PYTHONPATH .:${PYTHONPATH}
CMD ["streamlit", "run", "./webui/webui.py"]