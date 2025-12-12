import whisper
import logging
import time
import numpy as np

logger = logging.getLogger(__name__)

stt_model = whisper.load_model("small")

def run_whisper(audio_path):
    time_start = time.time()

    result = stt_model.transcribe(
        audio_path,
        language="en",
        no_speech_threshold=0.3  # bisa disesuaikan
    )

    time_end = time.time()
    execution_time = round(time_end - time_start, 3)
    print("Time execution stt:", execution_time)

    # ============================================
    #            ACOUSTIC CONFIDENCE
    # ============================================
    segments = result.get("segments", [])

    no_speech_probs = []
    for seg in segments:
        if "no_speech_prob" in seg:
            no_speech_probs.append(seg["no_speech_prob"])

    if len(no_speech_probs) > 0:
        # Model confidence bahwa audio punya ucapan
        speech_confidence = float(1 - np.mean(no_speech_probs))
    else:
        # Jika tidak ada segment → anggap rendah
        speech_confidence = 0.0

    # Pastikan nilai 0–1
    speech_confidence = max(0, min(1, speech_confidence))

    return {
        "text": result.get("text", ""),
        "acoustic_confidence": round(speech_confidence * 100, 2),
        "execution_time": execution_time
    }
