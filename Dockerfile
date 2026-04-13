# DAW-Ava GPU — RunPod Serverless
# D80 : onnxruntime CPU suffit pour audio-separator (de-reverb/stems)
# Le GPU n'est PAS necessaire pour le traitement audio UVR

FROM runpod/base:0.6.3-cuda11.8.0

RUN ln -sf $(which python3.11) /usr/local/bin/python && \
    ln -sf $(which python3.11) /usr/local/bin/python3

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir \
    runpod>=1.7.0 \
    requests \
    onnxruntime \
    audio-separator

ADD handler.py /handler.py

CMD ["python", "-u", "/handler.py"]
