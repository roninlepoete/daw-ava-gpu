"""
DAW-Ava GPU Handler — RunPod Serverless
V1 : de-reverb + stems via audio-separator
Conforme au template officiel RunPod.
"""

import runpod
import os
import tempfile
import requests
import base64
import traceback
from pathlib import Path

# ============================================================
# Chargement global (hors handler) — RunPod best practice
# Les modeles sont charges UNE SEULE FOIS au demarrage du worker
# ============================================================
print("DAW-Ava handler starting...")
print("Importing audio_separator...")

try:
    from audio_separator.separator import Separator
    print("audio_separator imported OK")
except Exception as e:
    print(f"FATAL: audio_separator import failed: {e}")
    Separator = None


def download_file(url, dest):
    """Telecharge un fichier depuis une URL."""
    print(f"Downloading {url[:80]}...")
    r = requests.get(url)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)
    print(f"Downloaded {Path(dest).stat().st_size} bytes")
    return dest


def file_to_b64(file_path):
    """Encode un fichier en base64."""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def handler(job):
    """Handler principal — conforme RunPod serverless."""
    try:
        job_input = job["input"]
        operation = job_input.get("operation", "echo")
        print(f"Job received: operation={operation}")

        # Echo — test de base
        if operation == "echo":
            return {
                "status": "alive",
                "message": "daw-ava-gpu handler OK",
                "separator_available": Separator is not None,
                "input": job_input,
            }

        # Verifier que audio-separator est disponible
        if Separator is None:
            return {"error": "audio_separator not available"}

        # Telecharger l'audio
        audio_url = job_input.get("audio_url")
        if not audio_url:
            return {"error": "audio_url required"}

        work_dir = Path(tempfile.mkdtemp())
        audio_file = work_dir / "input.wav"
        download_file(audio_url, str(audio_file))

        # Choisir le modele
        if operation == "dereverb":
            model_name = job_input.get("model", "UVR-DeEcho-DeReverb.pth")
        elif operation == "stems":
            model_name = job_input.get("model", "htdemucs_ft")
        else:
            return {"error": f"Unknown operation: {operation}"}

        print(f"Loading model: {model_name}")
        sep = Separator(output_dir=str(work_dir), output_format="wav")
        sep.load_model(model_filename=model_name)

        print("Separating...")
        result = sep.separate(str(audio_file))
        print(f"Separation result: {result}")

        # Lister les fichiers produits
        all_wavs = [f for f in work_dir.glob("*.wav") if f.name != "input.wav"]
        print(f"Output files: {[f.name for f in all_wavs]}")

        # Construire la reponse
        outputs = {}
        for wav in all_wavs:
            name_lower = wav.name.lower()
            if any(k in name_lower for k in ["no reverb", "no echo", "no_reverb", "no_echo"]):
                key = "dry"
            elif "vocal" in name_lower:
                key = "vocals"
            elif any(k in name_lower for k in ["other", "instrument"]):
                key = "instrumental"
            elif "reverb" in name_lower or "echo" in name_lower:
                key = "wet"
            else:
                key = wav.stem

            outputs[key] = {
                "filename": wav.name,
                "size_mb": round(wav.stat().st_size / (1024 * 1024), 1),
                "data_b64": file_to_b64(wav),
            }
            print(f"Output: {key} = {wav.name} ({wav.stat().st_size} bytes)")

        return outputs

    except Exception as e:
        print(f"ERROR: {e}")
        print(traceback.format_exc())
        return {"error": str(e), "traceback": traceback.format_exc()}


runpod.serverless.start({"handler": handler})
