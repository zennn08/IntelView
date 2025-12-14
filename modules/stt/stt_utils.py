"""
Speech-to-Text Utility menggunakan OpenAI Whisper

Module ini menangani transkripsi audio menggunakan model Whisper dari OpenAI.
Selain transkripsi, module ini juga menghitung acoustic confidence score
berdasarkan probabilitas no_speech dari setiap segment.

Model yang digunakan: "small" (trade-off antara accuracy dan speed)
- Tiny: Paling cepat, accuracy rendah
- Base: Cepat, accuracy sedang
- Small: Balance (DIGUNAKAN)
- Medium: Lambat, accuracy tinggi
- Large: Paling lambat, accuracy tertinggi
"""

import whisper
import logging
import time
import numpy as np

logger = logging.getLogger(__name__)

# Load Whisper model sekali saat module di-import (caching)
# Model "small" dipilih untuk balance antara speed dan accuracy
# Loading time: ~2-5 detik pertama kali, kemudian cached in memory
stt_model = whisper.load_model("small")

def run_whisper(audio_path):
    """
    Transkripsi audio file ke text menggunakan Whisper model.

    Proses yang dilakukan:
    1. Load audio file dan preprocess
    2. Jalankan inference Whisper untuk transkripsi
    3. Hitung acoustic confidence dari no_speech_prob setiap segment
    4. Return transcript text dan confidence score

    Acoustic Confidence Score:
        Dihitung dari rata-rata no_speech_prob semua segment.
        Formula: confidence = 1 - mean(no_speech_prob)

        - Score tinggi (>0.8): Audio jelas dengan ucapan yang konsisten
        - Score sedang (0.5-0.8): Audio ada noise atau pause
        - Score rendah (<0.5): Audio buruk, banyak noise, atau tidak jelas

    Args:
        audio_path (str): Path absolut ke file audio (MP3, WAV, dll)

    Returns:
        dict: Hasil transkripsi dengan struktur:
            {
                "text": str,                    # Full transcript
                "acoustic_confidence": float,   # Confidence score 0-1
                "execution_time": float         # Waktu eksekusi dalam detik
            }

    Example:
        >>> result = run_whisper("/tmp/audio.mp3")
        >>> print(result["text"])
        "TensorFlow is an open-source machine learning framework..."
        >>> print(result["acoustic_confidence"])
        0.87
    """
    # Mulai tracking waktu eksekusi
    time_start = time.time()

    # Jalankan Whisper transcription
    # Parameters:
    # - language="en": Force English transcription (lebih akurat untuk bahasa spesifik)
    # - no_speech_threshold=0.3: Threshold untuk mendeteksi segment tanpa ucapan
    #   Nilai lebih tinggi = lebih strict (hanya segment dengan speech jelas)
    #   Nilai lebih rendah = lebih permissive (termasuk background noise)
    result = stt_model.transcribe(
        audio_path,
        language="en",
        no_speech_threshold=0.3
    )

    # Hitung waktu eksekusi
    time_end = time.time()
    execution_time = round(time_end - time_start, 3)
    print("Time execution stt:", execution_time)

    # ============================================
    # Hitung Acoustic Confidence Score
    # ============================================
    # Whisper memberikan no_speech_prob untuk setiap segment
    # yang menunjukkan probabilitas bahwa segment tersebut tidak ada ucapan
    # Kita inverse nilai ini untuk mendapat speech confidence

    segments = result.get("segments", [])

    # Kumpulkan no_speech_prob dari semua segment
    no_speech_probs = []
    for seg in segments:
        if "no_speech_prob" in seg:
            no_speech_probs.append(seg["no_speech_prob"])

    # Hitung rata-rata dan inverse untuk mendapat speech confidence
    if len(no_speech_probs) > 0:
        # Speech confidence = 1 - rata-rata probabilitas "no speech"
        # Semakin rendah no_speech_prob, semakin tinggi confidence
        speech_confidence = float(1 - np.mean(no_speech_probs))
    else:
        # Jika tidak ada segment terdeteksi, anggap confidence rendah
        # Ini bisa terjadi jika audio terlalu pendek atau kosong
        speech_confidence = 0.0

    # Clamp nilai confidence ke range [0, 1] untuk safety
    speech_confidence = max(0, min(1, speech_confidence))

    # Return hasil transkripsi lengkap
    return {
        "text": result.get("text", ""),
        "acoustic_confidence": round(speech_confidence, 2),
        "execution_time": execution_time
    }
