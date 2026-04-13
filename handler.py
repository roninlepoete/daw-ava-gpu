"""
DAW-Ava GPU Handler — RunPod Serverless
V1 : de-reverb + stems (audio-separator)
"""

import runpod
import os
import tempfile
import requests
import base64
import traceback
from pathlib import Path


def download_file(url, dest):
    r = requests.get(url)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)
    return dest


def upload_result(file_path):
    with open(file_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return {
        "filename": Path(file_path).name,
        "size_mb": round(Path(file_path).stat().st_size / (1024 * 1024), 1),
        "data_b64": data,
    }


def handler(job):
    job_input = job["input"]
    operation = job_input.get("operation", "")
    logs = []

    work_dir = Path(tempfile.mkdtemp())
    logs.append(f"work_dir: {work_dir}")

    try:
        if operation not in ("stems", "dereverb"):
            return {"error": f"Operation inconnue: {operation}"}

        # Download audio
        audio_url = job_input.get("audio_url", "")
        logs.append(f"audio_url: {audio_url[:80]}")
        audio_file = work_dir / "input.wav"
        download_file(audio_url, audio_file)
        logs.append(f"downloaded: {audio_file.stat().st_size} bytes")

        # audio-separator
        from audio_separator.separator import Separator

        if operation == "dereverb":
            model_name = job_input.get("model", "UVR-DeEcho-DeReverb.pth")
        else:
            model_name = "htdemucs_ft"

        logs.append(f"model: {model_name}")

        sep = Separator(output_dir=str(work_dir), output_format="wav")
        sep.load_model(model_filename=model_name)
        logs.append("model loaded")

        result = sep.separate(str(audio_file))
        logs.append(f"separate result: {result}")

        # List ALL files in work_dir
        all_files = list(work_dir.glob("*"))
        logs.append(f"work_dir files: {[f.name for f in all_files]}")

        # Collect outputs
        outputs = {}
        for wav in work_dir.glob("*.wav"):
            if wav.name == "input.wav":
                continue
            name_lower = wav.name.lower()
            if any(k in name_lower for k in ["no reverb", "no echo", "no_reverb", "no_echo"]):
                key = "dry"
            elif any(k in name_lower for k in ["vocal"]):
                key = "vocals"
            elif any(k in name_lower for k in ["other", "instrument"]):
                key = "instrumental"
            else:
                key = wav.stem
            outputs[key] = upload_result(wav)
            logs.append(f"output: {key} = {wav.name} ({wav.stat().st_size} bytes)")

        # Also check CWD (audio-separator might output there)
        if not outputs:
            cwd = Path.cwd()
            logs.append(f"checking cwd: {cwd}")
            for wav in cwd.glob("*.wav"):
                logs.append(f"cwd file: {wav.name}")
                outputs[wav.stem] = upload_result(wav)

        outputs["_logs"] = logs
        return outputs

    except Exception as e:
        logs.append(f"ERROR: {str(e)}")
        logs.append(traceback.format_exc())
        return {"error": str(e), "_logs": logs}


runpod.serverless.start({"handler": handler})
