FROM python:3.11-slim-buster

ARG BOT_TOKEN
ENV BOT_TOKEN=$BOT_TOKEN

# Dependencies for opencv.
RUN apt-get update && apt-get install -y \
    libgl1-mesa-dev \
    libglib2.0-0

WORKDIR /usr/src/app

COPY . .

RUN pip install -r bot_requirements.txt

ENV PYTHONPATH .:${PYTHONPATH}
CMD ["python", "-u", "./bot/bot.py"]