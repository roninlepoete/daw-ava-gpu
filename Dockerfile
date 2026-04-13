# DAW-Ava GPU — Docker RunPod Serverless
# Pipeline audio complet : SVS + de-reverb + stems
# Base : PyTorch 2.2 + CUDA 12.1
# Les modeles sont telecharges au premier run (pas au build)

FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Dependances systeme
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# RunPod SDK + HTTP
RUN pip install --no-cache-dir runpod requests

# audio-separator (de-reverb + stems) — modeles telecharges au premier run
RUN pip install --no-cache-dir audio-separator

# SoulX-Singer (SVS) — code source
RUN git clone https://github.com/Soul-AILab/SoulX-Singer.git /app/SoulX-Singer

# Dependances SoulX-Singer (sans nemo_toolkit et sageattention qui sont trop lourds)
RUN pip install --no-cache-dir \
    accelerate einops g2p_en librosa loralib \
    mido ml_collections nltk numba omegaconf \
    praat-parselmouth pretty_midi pyloudnorm pyworld \
    rotary_embedding_torch scikit_learn scipy \
    soundfile tqdm transformers webrtcvad huggingface_hub

# Handler RunPod
COPY handler.py /app/handler.py

CMD ["python", "/app/handler.py"]
