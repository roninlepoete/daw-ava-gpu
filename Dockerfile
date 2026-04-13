# DAW-Ava GPU — RunPod Serverless
# D80 : onnxruntime DOIT etre installe APRES audio-separator
# car audio-separator peut installer une version GPU incompatible

FROM runpod/base:0.6.3-cuda11.8.0

RUN ln -sf $(which python3.11) /usr/local/bin/python && \
    ln -sf $(which python3.11) /usr/local/bin/python3

# Etape 1 : deps de base + audio-separator
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir \
    runpod>=1.7.0 \
    requests \
    audio-separator

# Etape 2 : FORCER onnxruntime CPU APRES audio-separator
# audio-separator ne l'installe pas automatiquement sur cette image
RUN pip install --no-cache-dir onnxruntime

# Etape 3 : VERIFIER que l'import fonctionne au build
RUN python -c "import onnxruntime; print(f'onnxruntime {onnxruntime.__version__} OK')"
RUN python -c "from audio_separator.separator import Separator; print('audio_separator import OK')"

ADD handler.py /handler.py

CMD ["python", "-u", "/handler.py"]
