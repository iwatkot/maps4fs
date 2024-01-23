FROM python:3.11-slim-buster

RUN apt-get update && apt-get install -y \
    libgl1-mesa-dev \
    libglib2.0-0

WORKDIR /usr/src/app

COPY . .

RUN pip install -r bot_requirements.txt

CMD ["python", "-u", "./src/bot.py"]