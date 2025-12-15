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
        no_speech_threshold=0.3
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
        speech_confidence = float(1 - np.mean(no_speech_probs))
    else:
        speech_confidence = 0.0

    speech_confidence = max(0, min(1, speech_confidence))

    # ============================================
    #            WORD METRICS
    # ============================================
    text = result.get("text", "").strip()

    # Jumlah kata
    word_count = len(text.split()) if text else 0

    # Durasi audio berdasarkan segment (detik)
    if len(segments) > 0:
        audio_duration = segments[-1]["end"] - segments[0]["start"]
    else:
        audio_duration = 0.0

    # Words Rate Per Minute (WRP)
    if audio_duration > 0:
        wrp = round(word_count / (audio_duration / 60), 2)
    else:
        wrp = 0.0

    return {
        "text": text,
        "word_count": word_count,
        "wrp": wrp,
        "acoustic_confidence": round(speech_confidence, 2),
        "execution_time": execution_time
    }
