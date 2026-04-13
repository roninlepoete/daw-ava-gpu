"""
DAW-Ava GPU Handler — RunPod Serverless
V1 : de-reverb + stems via audio-separator
Retourne les metadonnees (pas les fichiers — limite 20 Mo)
"""

import runpod
import os
import subprocess
import tempfile
import requests
import base64
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
    print(f"Downloading...")
    r = requests.get(url)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)
    print(f"Downloaded {Path(dest).stat().st_size} bytes")


def handler(job):
    try:
        job_input = job["input"]
        operation = job_input.get("operation", "echo")
        print(f"Job: {operation}")

        if operation == "echo":
            diag = {
                "status": "alive",
                "separator_available": Separator is not None,
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

        print(f"Model: {model_name}")
        sep = Separator(output_dir=str(work_dir), output_format="wav")
        sep.load_model(model_filename=model_name)

        print("Separating...")
        sep.separate(str(audio_file))
        print("Done")

        all_wavs = [f for f in work_dir.glob("*.wav") if f.name != "input.wav"]

        # Convertir en MP3 et retourner en base64
        outputs = {}
        for wav in all_wavs:
            name_lower = wav.name.lower()
            if any(k in name_lower for k in ["no reverb", "no echo"]):
                key = "dry"
            elif "vocal" in name_lower:
                key = "vocals"
            elif any(k in name_lower for k in ["other", "instrument"]):
                key = "instrumental"
            else:
                key = "wet"

            # WAV -> MP3 via ffmpeg
            mp3 = work_dir / f"{key}.mp3"
            subprocess.run(["ffmpeg", "-y", "-i", str(wav), "-b:a", "192k", str(mp3)], capture_output=True)

            if mp3.exists() and mp3.stat().st_size < 15_000_000:
                with open(mp3, "rb") as f:
                    outputs[key] = {
                        "filename": mp3.name,
                        "size_mb": round(mp3.stat().st_size / (1024*1024), 1),
                        "data_b64": base64.b64encode(f.read()).decode("utf-8"),
                    }
                print(f"Output: {key} ({mp3.stat().st_size/(1024*1024):.1f} Mo MP3)")
            else:
                # Fallback : juste les metadonnees sans le fichier
                outputs[key] = {
                    "filename": wav.name,
                    "size_mb": round(wav.stat().st_size / (1024*1024), 1),
                    "note": "file too large for response, MP3 conversion may have failed",
                }

        return outputs

    except Exception as e:
        print(f"ERROR: {e}")
        return {"error": str(e), "traceback": traceback.format_exc()}


runpod.serverless.start({"handler": handler})
