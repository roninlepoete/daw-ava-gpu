"""
DAW-Ava GPU Handler — RunPod Serverless
Toutes les operations audio GPU dans un seul endpoint.

Operations supportees :
  - svs      : Singing Voice Synthesis (SoulX-Singer)
  - svc      : Singing Voice Conversion (RVC v2)
  - dereverb : De-reverb/de-echo (audio-separator MelBand Roformer)
  - stems    : Separation de stems (Demucs htdemucs_ft)
"""

import runpod
import os
import tempfile
import requests
import base64
import json
from pathlib import Path


def download_file(url, dest):
    """Telecharge un fichier depuis une URL."""
    r = requests.get(url)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)
    return dest


def upload_result(file_path):
    """Encode le fichier en base64 pour le retour RunPod."""
    with open(file_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return {
        "filename": Path(file_path).name,
        "size_mb": round(Path(file_path).stat().st_size / (1024 * 1024), 1),
        "data_b64": data,
    }


def op_stems(job_input, work_dir):
    """Separation de stems via Demucs htdemucs_ft."""
    from audio_separator.separator import Separator

    audio_url = job_input["audio_url"]
    stem_mode = job_input.get("stem", "vocals")
    audio_file = download_file(audio_url, work_dir / "input.wav")

    sep = Separator(output_dir=str(work_dir), output_format="wav")
    sep.load_model(model_filename="htdemucs_ft")
    result = sep.separate(str(audio_file))

    outputs = {}
    for f in result:
        p = Path(f)
        if p.exists():
            name = "vocals" if "vocal" in p.name.lower() else "instrumental"
            outputs[name] = upload_result(p)

    return outputs


def op_dereverb(job_input, work_dir):
    """De-reverb/de-echo via audio-separator."""
    from audio_separator.separator import Separator

    audio_url = job_input["audio_url"]
    model_name = job_input.get("model", "UVR-DeEcho-DeReverb.pth")
    audio_file = download_file(audio_url, work_dir / "input.wav")

    sep = Separator(output_dir=str(work_dir), output_format="wav")
    sep.load_model(model_filename=model_name)
    result = sep.separate(str(audio_file))

    outputs = {}
    for f in result:
        p = Path(f)
        if p.exists():
            if "no reverb" in p.name.lower() or "no echo" in p.name.lower():
                outputs["dry"] = upload_result(p)
            else:
                outputs["wet"] = upload_result(p)

    return outputs


def op_svc(job_input, work_dir):
    """Singing Voice Conversion — V1 delegue a Replicate."""
    return {"error": "SVC : utiliser Replicate (zsxkib/realistic-voice-cloning). RunPod SVC = V2."}


def op_svs(job_input, work_dir):
    """Singing Voice Synthesis — V1 delegue a HuggingFace Space."""
    return {"error": "SVS : utiliser HuggingFace Space (Soul-AILab/SoulX-Singer). RunPod SVS = V2."}


def handler(job):
    """Handler principal RunPod — dispatche selon l'operation demandee."""
    job_input = job["input"]
    operation = job_input.get("operation", "")

    work_dir = Path(tempfile.mkdtemp())

    try:
        if operation == "stems":
            return op_stems(job_input, work_dir)
        elif operation == "dereverb":
            return op_dereverb(job_input, work_dir)
        elif operation == "svc":
            return op_svc(job_input, work_dir)
        elif operation == "svs":
            return op_svs(job_input, work_dir)
        else:
            return {"error": f"Operation inconnue : {operation}. Valides : stems, dereverb, svc, svs"}
    except Exception as e:
        return {"error": str(e)}


runpod.serverless.start({"handler": handler})
