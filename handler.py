"""
DAW-Ava GPU Handler — RunPod Serverless
V1-debug : handler minimal pour tester le deploiement
"""

import runpod


def handler(job):
    """Handler minimal — juste un echo pour tester que le container demarre."""
    job_input = job.get("input", {})
    operation = job_input.get("operation", "echo")

    if operation == "echo":
        return {"status": "alive", "message": "daw-ava-gpu handler OK", "input_received": job_input}

    if operation == "dereverb" or operation == "stems":
        try:
            from audio_separator.separator import Separator
            return {"status": "import_ok", "message": "audio-separator imported successfully"}
        except Exception as e:
            return {"status": "import_error", "error": str(e)}

    return {"status": "unknown_operation", "operation": operation}


runpod.serverless.start({"handler": handler})
