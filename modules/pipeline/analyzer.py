import os
import tempfile
import logging
import time
import asyncio

from modules.audio.audio_utils import extract_audio
from modules.stt.stt_utils import run_whisper
from modules.detection.people_detector import run_people_detector
# from modules.detection.eye_gaze_detector import run_eye_gaze_detector
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
        # 2. Run Whisper + People Detector ASYNC
        # --------------------------------------
        transcript_task = asyncio.to_thread(run_whisper, audio_path)
        people_task = asyncio.to_thread(run_people_detector, temp_video_path)
        # eye_task = asyncio.to_thread(run_eye_gaze_detector, temp_video_path)

        transcript, people = await asyncio.gather(
            transcript_task, people_task
        )

        # --------------------------------------
        # 3. LLM Evaluation (sync)
        # --------------------------------------
        evaluation = evaluate_exam(transcript, people)

        # --------------------------------------
        # Time tracking - END
        # --------------------------------------
        time_end = time.time()
        execution_time = round(time_end - time_start, 3)

        return {
            "transcript": transcript,
            "people": people,
            "evaluation": evaluation,
            "time_start": time_start,
            "time_end": time_end,
            "execution_time_seconds": execution_time
        }

    finally:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
