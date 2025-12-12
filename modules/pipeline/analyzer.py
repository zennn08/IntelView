import os
import tempfile
import logging
import time
import asyncio   # <-- penting!

from modules.audio.audio_utils import extract_audio
from modules.stt.stt_utils import run_whisper
from modules.detection.people_detector import run_people_detector
from modules.detection.eye_tracking import run_eye_tracking
from modules.llm.llm_utils import evaluate_exam

logger = logging.getLogger(__name__)

async def analyze_video_pipeline(video_file):

    # ------------------------------
    # Time tracking - START
    # ------------------------------
    time_start = time.time()

    suffix = ".mp4"
    fd, temp_video_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    video_file.save(temp_video_path)

    audio_path = None

    try:
        # --------------------------------------
        # 1. Extract audio (sync)
        # --------------------------------------
        audio_path = extract_audio(temp_video_path)

        # --------------------------------------
        # 2. Run Whisper + People Detector + Eye Tracking ASYNC
        # --------------------------------------
        transcript_task = asyncio.to_thread(run_whisper, audio_path)
        people_task = asyncio.to_thread(run_people_detector, temp_video_path)
        eye_task = asyncio.to_thread(run_eye_tracking, temp_video_path)

        stt_output, people, eye = await asyncio.gather(
            transcript_task, people_task, eye_task
        )

        transcript_text = stt_output.get("text", "")
        acoustic_conf = stt_output.get("acoustic_confidence", 0)

        # --------------------------------------
        # 3. LLM Evaluation (sync)
        # --------------------------------------
        evaluation = evaluate_exam(transcript_text, people, eye)

        # --------------------------------------
        # Time tracking - END
        # --------------------------------------
        time_end = time.time()
        execution_time = round(time_end - time_start, 3)

        return {
            "transcript": transcript_text,
            "acoustic_confidence": acoustic_conf,
            "people": people,
            "evaluation": evaluation,
            "eye": eye,
            "time_start": time_start,
            "time_end": time_end,
            "execution_time_seconds": execution_time
        }

    finally:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)