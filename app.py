"""
INTELVIEW - AI-Powered Interview Assessment Platform
Flask Application Entry Point

Aplikasi web ini menyediakan endpoint untuk menganalisis video wawancara menggunakan
berbagai model AI untuk deteksi kecurangan dan evaluasi otomatis.
"""

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from modules.pipeline.analyzer import analyze_video_pipeline

import os

# Menonaktifkan logging verbose dari TensorFlow dan MediaPipe untuk output yang lebih bersih
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['MEDIAPIPE_DISABLE_LOG'] = '1'

# Menonaktifkan warnings yang tidak relevan
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
warnings.filterwarnings("ignore", message="SymbolDatabase.GetPrototype")
warnings.filterwarnings("ignore", category=UserWarning)

# Mengatur logging level untuk ABSL (digunakan oleh TensorFlow)
import absl.logging
absl.logging.set_verbosity(absl.logging.ERROR)

# Inisialisasi Flask application dengan konfigurasi folder
app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')
CORS(app)  # Enable Cross-Origin Resource Sharing

@app.route("/")
def home():
    """
    Route untuk halaman utama aplikasi.

    Returns:
        HTML: Render template index.html sebagai landing page
    """
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
async def analyze():
    """
    Endpoint utama untuk analisis video wawancara.

    Endpoint ini menerima satu atau lebih video beserta pertanyaan yang diajukan,
    kemudian menjalankan pipeline analisis lengkap yang mencakup:
    - Transkripsi speech-to-text
    - Deteksi kecurangan (multiple people, eye tracking)
    - Evaluasi AI menggunakan Gemini

    Request Form Data:
        video (FileList): Satu atau lebih file video (MP4, AVI, MOV, dll)
        question (List[str]): Pertanyaan yang diajukan untuk setiap video (opsional)

    Returns:
        JSON: Hasil analisis dengan struktur berbeda tergantung jumlah video:
            - Single video: Object dengan hasil analisis langsung
            - Multiple videos: Object dengan key 'results' berisi array hasil

    Response Status:
        200: Analisis berhasil
        400: Error - tidak ada video yang di-upload
    """
    # Mengambil semua video dan pertanyaan dari form data
    video_files = request.files.getlist("video")
    questions = request.form.getlist("question")

    # Validasi: pastikan ada minimal satu video
    if not video_files or len(video_files) == 0:
        return jsonify({"error": "no_video_uploaded"}), 400

    # Case 1: Single video upload (backward compatibility)
    # Mengembalikan hasil langsung tanpa wrapper array
    if len(video_files) == 1:
        question = questions[0] if questions else ""
        result = await analyze_video_pipeline(video_files[0], question)
        return jsonify(result), 200

    # Case 2: Multiple video upload
    # Process setiap video secara sequential dan kumpulkan hasilnya
    import asyncio
    results = []
    for i, video_file in enumerate(video_files):
        # Ambil pertanyaan sesuai index, atau string kosong jika tidak ada
        question = questions[i] if i < len(questions) else ""

        # Jalankan pipeline analisis untuk video ini
        result = await analyze_video_pipeline(video_file, question)

        # Tambahkan metadata untuk identifikasi
        result["video_index"] = i
        result["video_name"] = video_file.filename
        result["question"] = question
        results.append(result)

    # Kembalikan hasil dalam format structured untuk multiple videos
    return jsonify({
        "multiple": True,
        "count": len(results),
        "results": results
    }), 200


if __name__ == "__main__":
    # Ambil port dari environment variable atau gunakan default 5000
    port = int(os.getenv("PORT", 5000))

    # Jalankan aplikasi pada semua network interfaces (0.0.0.0)
    # Ini memungkinkan akses dari komputer lain dalam network yang sama
    app.run(host="0.0.0.0", port=port, debug=False)
