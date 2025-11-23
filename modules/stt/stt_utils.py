import whisper
import logging
import time

logger = logging.getLogger(__name__)

stt_model = whisper.load_model("small")

def run_whisper(audio_path):
    time_start = time.time()
    result = stt_model.transcribe(audio_path, language="en")
    time_end = time.time()
    execution_time = round(time_end - time_start, 3)
    print("Time execution stt : " , execution_time)
    return result.get("text", "")
