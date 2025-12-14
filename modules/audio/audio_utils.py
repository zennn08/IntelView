"""
Audio Extraction Utility

Module ini menangani ekstraksi audio track dari file video menggunakan FFmpeg.
Audio yang diekstrak akan digunakan untuk speech-to-text transcription.
"""

import os
import tempfile
import ffmpeg
import logging

logger = logging.getLogger(__name__)

def extract_audio(video_path, audio_path=None):
    """
    Ekstrak audio track dari file video dan konversi ke format MP3.

    Fungsi ini menggunakan FFmpeg untuk:
    1. Membaca stream video dari file input
    2. Mengekstrak audio track saja (tanpa video)
    3. Mengkonversi ke format MP3 menggunakan codec libmp3lame
    4. Menyimpan ke temporary file atau path yang ditentukan

    Args:
        video_path (str): Path absolut ke file video input
        audio_path (str, optional): Path untuk menyimpan audio output.
                                    Jika None, akan dibuat temporary file otomatis.

    Returns:
        str: Path ke file audio yang berhasil diekstrak (format MP3)

    Raises:
        ffmpeg.Error: Jika terjadi error dalam proses FFmpeg
                      (file tidak ditemukan, format tidak didukung, dll)

    Example:
        >>> audio_file = extract_audio("/tmp/interview.mp4")
        >>> print(audio_file)
        /tmp/tmpxyz123.mp3
    """
    # Jika audio_path tidak disediakan, buat temporary file
    if audio_path is None:
        fd, audio_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)  # Tutup file descriptor, kita hanya butuh path-nya

    try:
        # Jalankan FFmpeg command untuk ekstraksi audio:
        # - input(video_path): Baca file video
        # - output(...): Konfigurasi output
        #   - acodec="libmp3lame": Gunakan MP3 encoder
        #   - vn=None: Disable video stream (audio only)
        # - run(...): Execute command
        #   - overwrite_output=True: Overwrite file jika sudah ada
        #   - capture_stdout/stderr=True: Capture output untuk error handling
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, acodec="libmp3lame", vn=None)
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
        return audio_path

    except ffmpeg.Error as e:
        # Log error detail dari stderr FFmpeg untuk debugging
        logger.error("ffmpeg error: %s", e.stderr.decode())
        raise
