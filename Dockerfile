# DAW-Ava GPU — Docker RunPod Serverless
# V1 : de-reverb + stems (audio-separator)

FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    runpod \
    requests \
    audio-separator[cpu]

COPY handler.py /app/handler.py

CMD ["python", "/app/handler.py"]
