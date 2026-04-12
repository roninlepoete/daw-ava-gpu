# DAW-Ava GPU — Docker RunPod Serverless
# Pipeline audio complet : SVS + SVC + de-reverb + stems
# Base : PyTorch 2.2 + CUDA 12.1

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

# RunPod SDK
RUN pip install --no-cache-dir runpod requests

# audio-separator (de-reverb + stems)
RUN pip install --no-cache-dir audio-separator

# Pre-telecharger les modeles de-reverb et stems
RUN python -c "\
from audio_separator.separator import Separator; \
sep = Separator(); \
sep.load_model(model_filename='UVR-DeEcho-DeReverb.pth'); \
print('UVR-DeEcho-DeReverb OK')"

RUN python -c "\
from audio_separator.separator import Separator; \
sep = Separator(); \
sep.load_model(model_filename='Reverb_HQ_By_FoxJoy.onnx'); \
print('Reverb_HQ_FoxJoy OK')"

# SoulX-Singer (SVS)
RUN git clone https://github.com/Soul-AILab/SoulX-Singer.git /app/SoulX-Singer

RUN pip install --no-cache-dir \
    accelerate einops g2p_en librosa loralib \
    mido ml_collections nltk numba omegaconf \
    praat-parselmouth pretty_midi pyloudnorm pyworld \
    rotary_embedding_torch scikit_learn scipy \
    soundfile tqdm transformers webrtcvad

# Pre-telecharger les modeles SoulX-Singer
RUN pip install --no-cache-dir huggingface_hub && \
    huggingface-cli download Soul-AILab/SoulX-Singer --local-dir /app/pretrained_models/SoulX-Singer && \
    huggingface-cli download Soul-AILab/SoulX-Singer-Preprocess --local-dir /app/pretrained_models/SoulX-Singer-Preprocess

# Handler RunPod
COPY handler.py /app/handler.py

CMD ["python", "/app/handler.py"]
