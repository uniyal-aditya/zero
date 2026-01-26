FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libopus0 \
    libopus-dev \
    libsodium-dev \
    libffi-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
