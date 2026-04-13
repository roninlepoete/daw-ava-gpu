# DAW-Ava GPU — Docker RunPod Serverless
# V1 : de-reverb + stems (audio-separator)
# SVS (SoulX-Singer) sera ajoute en V2

FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Dependances systeme
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# RunPod SDK + HTTP + torch CPU (leger pour audio-separator)
RUN pip install --no-cache-dir \
    runpod \
    requests \
    torch==2.2.0+cpu \
    torchaudio==2.2.0+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

# audio-separator (de-reverb + stems)
RUN pip install --no-cache-dir audio-separator

# Handler RunPod
COPY handler.py /app/handler.py

CMD ["python", "/app/handler.py"]
