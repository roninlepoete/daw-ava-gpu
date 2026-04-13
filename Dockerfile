# DAW-Ava GPU — RunPod Serverless
# Base officielle RunPod (CUDA + SDK pre-installe)

FROM runpod/base:0.6.3-cuda11.8.0

# Python 3.11
RUN ln -sf $(which python3.11) /usr/local/bin/python && \
    ln -sf $(which python3.11) /usr/local/bin/python3

# Dependances
COPY requirements.txt /requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r /requirements.txt

# Handler
ADD handler.py /handler.py

# -u = unbuffered stdout (obligatoire RunPod)
CMD ["python", "-u", "/handler.py"]
