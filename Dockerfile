# DAW-Ava GPU — RunPod Serverless
# Base officielle RunPod (CUDA 11.8)
# D80 : lu la doc avant de coder

FROM runpod/base:0.6.3-cuda11.8.0

# Python 3.11 (pre-installe dans l'image RunPod)
RUN ln -sf $(which python3.11) /usr/local/bin/python && \
    ln -sf $(which python3.11) /usr/local/bin/python3

# Dependances
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir \
    runpod>=1.7.0 \
    requests \
    onnxruntime-gpu \
    audio-separator

# Handler
ADD handler.py /handler.py

# -u = unbuffered stdout (obligatoire RunPod)
CMD ["python", "-u", "/handler.py"]
