# DAW-Ava GPU — RunPod Serverless
# Base officielle RunPod (CUDA 11.8)
# D80 : onnxruntime-gpu DOIT matcher la version CUDA de l'image

FROM runpod/base:0.6.3-cuda11.8.0

RUN ln -sf $(which python3.11) /usr/local/bin/python && \
    ln -sf $(which python3.11) /usr/local/bin/python3

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir \
    runpod>=1.7.0 \
    requests && \
    pip install --no-cache-dir \
    onnxruntime-gpu \
    --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-11/pypi/simple/ && \
    pip install --no-cache-dir \
    audio-separator

ADD handler.py /handler.py

CMD ["python", "-u", "/handler.py"]
