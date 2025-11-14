import whisper
import logging

logger = logging.getLogger(__name__)

stt_model = whisper.load_model("small")

def run_whisper(audio_path):
    result = stt_model.transcribe(audio_path, language="en")
    return result.get("text", "")
