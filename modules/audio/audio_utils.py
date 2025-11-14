import os
import tempfile
import ffmpeg
import logging

logger = logging.getLogger(__name__)

def extract_audio(video_path, audio_path=None):
    if audio_path is None:
        fd, audio_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)

    try:
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, acodec="libmp3lame", vn=None)
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
        return audio_path
    except ffmpeg.Error as e:
        logger.error("ffmpeg error: %s", e.stderr.decode())
        raise
