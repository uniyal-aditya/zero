# Dockerfile for Zero (yt-dlp + ffmpeg) — production-ready for Railway
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install system deps + ffmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libopus0 \
    libopus-dev \
    python3-dev \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*


# create app dir
WORKDIR /app

# copy only requirements first for caching
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# copy code
COPY . /app

# set env default port for Railway (optional)
ENV PORT=8080

# start command; use main bot file name
CMD ["python", "bot.py"]
