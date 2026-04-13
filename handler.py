"""
DAW-Ava GPU Handler — RunPod Serverless
V1 : de-reverb + stems via audio-separator
Retourne des URLs de fichiers (pas de base64 — limite 20 Mo)
"""

import runpod
import os
import tempfile
import requests
import traceback
from pathlib import Path

print("DAW-Ava handler starting...")

try:
    from audio_separator.separator import Separator
    print("audio_separator imported OK")
except Exception as e:
    print(f"FATAL: audio_separator import failed: {e}")
    Separator = None


def download_file(url, dest):
    print(f"Downloading {url[:80]}...")
    r = requests.get(url)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)
    print(f"Downloaded {Path(dest).stat().st_size} bytes")
    return dest


def upload_to_transfer(file_path):
    """Upload vers transfer.sh (temporaire, 14 jours, gratuit)."""
    p = Path(file_path)
    print(f"Uploading {p.name} ({p.stat().st_size/(1024*1024):.1f} Mo)...")
    with open(file_path, "rb") as f:
        r = requests.put(
            f"https://transfer.sh/{p.name}",
            data=f,
            headers={"Max-Days": "7"}
        )
    if r.status_code == 200:
        url = r.text.strip()
        print(f"Uploaded: {url}")
        return url
    else:
        print(f"Upload failed: {r.status_code} {r.text[:200]}")
        return None


def handler(job):
    try:
        job_input = job["input"]
        operation = job_input.get("operation", "echo")
        print(f"Job received: operation={operation}")

        if operation == "echo":
            diag = {
                "status": "alive",
                "message": "daw-ava-gpu handler OK",
                "separator_available": Separator is not None,
                "input": job_input,
            }
            if job_input.get("debug"):
                try:
                    from audio_separator.separator import Separator as S
                    diag["import_test"] = "SUCCESS"
                except Exception as ie:
                    diag["import_test"] = "FAILED"
                    diag["import_error"] = str(ie)
            return diag

        if Separator is None:
            return {"error": "audio_separator not available"}

        audio_url = job_input.get("audio_url")
        if not audio_url:
            return {"error": "audio_url required"}

        work_dir = Path(tempfile.mkdtemp())
        audio_file = work_dir / "input.wav"
        download_file(audio_url, str(audio_file))

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
        print(f"Separation done")

        all_wavs = [f for f in work_dir.glob("*.wav") if f.name != "input.wav"]
        print(f"Output files: {[f.name for f in all_wavs]}")

        # Uploader les fichiers et retourner les URLs (pas de base64)
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

            url = upload_to_transfer(wav)
            outputs[key] = {
                "filename": wav.name,
                "size_mb": round(wav.stat().st_size / (1024 * 1024), 1),
                "url": url,
            }
            print(f"Output: {key} = {wav.name} -> {url}")

        return outputs

    except Exception as e:
        print(f"ERROR: {e}")
        print(traceback.format_exc())
        return {"error": str(e), "traceback": traceback.format_exc()}


runpod.serverless.start({"handler": handler})
