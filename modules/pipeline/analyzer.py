"""
Video Analysis Pipeline - Main Orchestrator

Module ini adalah orchestrator utama yang mengkoordinasikan seluruh proses analisis video.
Pipeline ini menjalankan berbagai task secara asinkron untuk efisiensi maksimal:
1. Ekstraksi audio dari video
2. Paralel execution: Whisper transcription, people detection, eye tracking
3. Evaluasi menggunakan LLM (Gemini)

Formula confidence score:
    Final Score = 0.2 × acoustic_confidence
                + 0.4 × people_confidence
                + 0.4 × eye_confidence
"""

import os
import tempfile
import logging
import time
import asyncio

from modules.audio.audio_utils import extract_audio
from modules.stt.stt_utils import run_whisper
from modules.detection.people_detector import run_people_detector
from modules.detection.eye_tracking import run_eye_tracking
from modules.llm.llm_utils import evaluate_exam

logger = logging.getLogger(__name__)

async def analyze_video_pipeline(video_file, question=""):
    """
    Pipeline utama untuk analisis video wawancara secara komprehensif.

    Workflow:
    1. Simpan video upload ke temporary file
    2. Ekstrak audio menggunakan FFmpeg
    3. Jalankan 3 task secara paralel (async):
       - Whisper: Transkripsi speech-to-text + acoustic confidence
       - YOLO: Deteksi multiple people
       - MediaPipe: Eye tracking dan gaze detection
    4. Evaluasi hasil dengan Gemini AI
    5. Hitung composite confidence score
    6. Cleanup temporary files

    Args:
        video_file (FileStorage): File video yang di-upload dari Flask request
        question (str, optional): Pertanyaan yang diajukan dalam wawancara.
                                  Digunakan untuk matching dengan question bank.

    Returns:
        dict: Hasil analisis lengkap dengan struktur:
            {
                "transcript": str,              # Transkripsi lengkap
                "confidence_score": float,      # Composite score (0-1)
                "speech": dict,                 # Detail hasil Whisper
                "people": dict,                 # Detail hasil people detection
                "evaluation": dict,             # Hasil evaluasi Gemini
                "eye": dict,                    # Detail hasil eye tracking
                "question": str,                # Pertanyaan yang diajukan
                "time_start": float,            # Unix timestamp mulai
                "time_end": float,              # Unix timestamp selesai
                "execution_time_seconds": float # Durasi eksekusi total
            }

    Raises:
        Exception: Error dalam proses ekstraksi audio atau analisis
    """

    # Mulai tracking waktu eksekusi total
    time_start = time.time()

    # Buat temporary file untuk menyimpan video upload
    # Menggunakan suffix .mp4 untuk kompatibilitas dengan FFmpeg
    suffix = ".mp4"
    fd, temp_video_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)  # Tutup file descriptor, kita hanya butuh path-nya
    video_file.save(temp_video_path)

    audio_path = None

    try:
        # =========================================
        # STEP 1: Ekstraksi Audio (Synchronous)
        # =========================================
        # FFmpeg extract audio track dari video dan konversi ke MP3
        # Ini operasi I/O bound tapi tetap sync karena FFmpeg subprocess
        audio_path = extract_audio(temp_video_path)

        # =========================================
        # STEP 2: Parallel Processing (Asynchronous)
        # =========================================
        # Jalankan 3 task berat secara paralel untuk efisiensi:
        # - run_whisper: CPU-intensive, ~10-20 detik untuk video 1 menit
        # - run_people_detector: GPU/CPU-intensive, ~5-15 detik
        # - run_eye_tracking: CPU-intensive, ~5-10 detik
        #
        # asyncio.to_thread() membungkus sync function agar bisa di-await
        # asyncio.gather() menjalankan semua task paralel dan menunggu semuanya selesai
        transcript_task = asyncio.to_thread(run_whisper, audio_path)
        people_task = asyncio.to_thread(run_people_detector, temp_video_path)
        eye_task = asyncio.to_thread(run_eye_tracking, temp_video_path)

        # Tunggu semua task selesai, hasil dikembalikan dalam order yang sama
        stt_output, people, eye = await asyncio.gather(
            transcript_task, people_task, eye_task
        )

        # Ekstrak hasil dari setiap komponen
        transcript_text = stt_output.get("text", "")
        acoustic_conf = stt_output.get("acoustic_confidence", 0)
        confidence_score_people = people.get("confidence_score", 0)
        confidence_score_eye = eye.get("confidence_score", 0)

        # =========================================
        # STEP 3: Hitung Composite Confidence Score
        # =========================================
        # Weighted average dengan bobot:
        # - 20% acoustic confidence (kualitas suara)
        # - 40% people confidence (single person vs multiple)
        # - 40% eye confidence (fokus vs looking away)
        #
        # Bobot lebih tinggi untuk visual cheating detection karena
        # lebih reliable dan sulit di-manipulasi
        final_confidence_score = (
            0.2 * acoustic_conf +
            0.4 * confidence_score_people +
            0.4 * confidence_score_eye
        )

        # =========================================
        # STEP 4: LLM Evaluation (Synchronous)
        # =========================================
        # Gemini evaluasi transcript dengan mempertimbangkan:
        # - Kualitas jawaban (content, accuracy, examples)
        # - Cheating indicators dari people & eye detection
        # - Question matching dengan bank of questions
        evaluation = evaluate_exam(transcript_text, people, eye, question)

        # =========================================
        # STEP 5: Finalisasi dan Return
        # =========================================
        time_end = time.time()
        execution_time = round(time_end - time_start, 3)

        # Kembalikan hasil lengkap dengan semua metrics
        return {
            "transcript": transcript_text,
            "confidence_score": round(final_confidence_score, 2),
            "speech": stt_output,
            "people": people,
            "evaluation": evaluation,
            "eye": eye,
            "question": question,
            "time_start": time_start,
            "time_end": time_end,
            "execution_time_seconds": execution_time
        }

    finally:
        # =========================================
        # Cleanup: Hapus Temporary Files
        # =========================================
        # Penting untuk cleanup agar tidak memenuhi disk space
        # Executed bahkan jika ada exception (finally block)
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
