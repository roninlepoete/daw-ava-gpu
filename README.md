# Docker DAW-Ava GPU — RunPod Serverless

> Pipeline audio complet sur GPU cloud.
> Un seul container, toutes les operations.

---

## Operations supportees

| Operation | Modele | Description |
|-----------|--------|-------------|
| `stems` | Demucs htdemucs_ft | Separation 2 stems (vocal + instrumental) |
| `dereverb` | UVR-DeEcho-DeReverb | Suppression echo + reverb |
| `svs` | SoulX-Singer | Synthese vocale chantee (melodie + paroles + timbre) |
| `svc` | RVC v2 (futur) | Conversion vocale (Phase 2) |

---

## Build

```bash
docker build -t daw-ava-gpu .
```

## Push vers Docker Hub

```bash
docker tag daw-ava-gpu roninlepoete/daw-ava-gpu:latest
docker push roninlepoete/daw-ava-gpu:latest
```

## Deploiement RunPod

1. Aller sur https://www.runpod.io/console/serverless
2. Creer un nouveau endpoint
3. Image : `roninlepoete/daw-ava-gpu:latest`
4. GPU : L4 (24 Go VRAM) — suffisant pour toutes les operations
5. Max Workers : 1
6. Idle Timeout : 5 sec

---

## Appel API

### Stems

```python
import runpod
runpod.api_key = os.environ["RUNPOD_API_KEY"]

result = runpod.run(
    endpoint_id="ENDPOINT_ID",
    input={
        "operation": "stems",
        "audio_url": "https://example.com/song.wav"
    }
)
```

### De-reverb

```python
result = runpod.run(
    endpoint_id="ENDPOINT_ID",
    input={
        "operation": "dereverb",
        "audio_url": "https://example.com/vocals.wav",
        "model": "UVR-DeEcho-DeReverb.pth"
    }
)
```

### SVS (SoulX-Singer)

```python
result = runpod.run(
    endpoint_id="ENDPOINT_ID",
    input={
        "operation": "svs",
        "prompt_audio_url": "https://example.com/my-voice.wav",
        "target_audio_url": "https://example.com/suno-vocals.wav",
        "control": "melody",
        "auto_shift": True,
        "pitch_shift": 0
    }
)
```

---

## Cout estime

| Operation | Duree GPU | Cout (L4 $0.48/h) |
|-----------|-----------|-------------------|
| stems | ~30 sec | ~$0.004 |
| dereverb | ~15 sec | ~$0.002 |
| svs | ~2-3 min | ~$0.02-0.03 |
| **Pipeline complet** | ~4 min | **~$0.03** |

---

*"Le compute va au cloud. Le controle reste au Cap'taine."*
