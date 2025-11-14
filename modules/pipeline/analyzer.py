import os
import tempfile
import logging

from modules.audio.audio_utils import extract_audio
from modules.stt.stt_utils import run_whisper
from modules.detection.people_detector import run_people_detector
from modules.llm.llm_utils import evaluate_exam

logger = logging.getLogger(__name__)

def analyze_video_pipeline(video_file):
    # simpan file video
    suffix = ".mp4"
    fd, temp_video_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    video_file.save(temp_video_path)

    try:
        audio_path = extract_audio(temp_video_path)
        transcript = run_whisper(audio_path)
        people = run_people_detector(temp_video_path)
        evaluation = evaluate_exam(transcript, people)

        return {
            "transcript": transcript,
            "people": people,
            "evaluation": evaluation
        }
    finally:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)