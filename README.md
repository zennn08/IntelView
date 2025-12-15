# INTELVIEW - AI-Powered Interview Assessment Platform

![INTELVIEW Logo](static/images/logo.png)

INTELVIEW adalah platform penilaian wawancara berbasis AI yang menganalisis rekaman video wawancara untuk mendeteksi kecurangan dan memberikan evaluasi otomatis. Aplikasi ini menggunakan berbagai model AI untuk menilai kandidat berdasarkan tiga dimensi: analisis ucapan, deteksi kecurangan, dan evaluasi AI.

## 🌟 Fitur Utama

### 1. **Analisis Multi-Dimensi**
- **Speech-to-Text Transcription** - Menggunakan OpenAI Whisper untuk transkripsi akurat
- **Acoustic Confidence Scoring** - Mengukur kepercayaan diri dari kualitas suara
- **Multi-Person Detection** - Mendeteksi kehadiran orang lain dalam frame menggunakan YOLO12n-Face
- **Eye Tracking & Gaze Detection** - Menganalisis gerakan mata menggunakan MediaPipe
- **AI-Powered Evaluation** - Penilaian otomatis menggunakan Google Gemini 2.5 Flash

### 2. **Deteksi Kecurangan**
- **People Cheating** - Mendeteksi lebih dari satu orang dalam frame
- **Eye Cheating** - Mendeteksi ketika kandidat melihat keluar layar terlalu lama
- **Confidence Metrics** - Skor kepercayaan diri berbasis akustik dan visual

### 3. **Fitur Tambahan**
- **Multiple Video Upload** - Upload dan proses beberapa video sekaligus
- **Question Bank Matching** - Sistem pencocokan pertanyaan cerdas dengan 5 pertanyaan teknis
- **Export Capabilities** - Export hasil ke format PDF atau JSON
- **Real-time Processing** - Pipeline asinkron untuk analisis cepat
- **Rubric-based Scoring** - Sistem penilaian 0-4 berdasarkan rubrik terstruktur

## 🏗️ Arsitektur Sistem

```
User Upload Video + Pertanyaan
         ↓
    Flask /analyze endpoint
         ↓
analyze_video_pipeline (async)
         ↓
    ┌────────────────────────────────┐
    │  1. Simpan video temporary     │
    │  2. Ekstrak audio (FFmpeg)     │
    └────────────────────────────────┘
         ↓
    ┌────────────────────────────────┐
    │  3. Pemrosesan Paralel:        │
    │     • Whisper (transkripsi)    │
    │     • YOLO (deteksi orang)     │
    │     • MediaPipe (eye tracking) │
    └────────────────────────────────┘
         ↓
    ┌────────────────────────────────┐
    │  4. Evaluasi Gemini:           │
    │     • Pencocokan pertanyaan    │
    │     • Scoring berbasis rubrik  │
    │     • Penilaian kecurangan     │
    │     • Generasi feedback        │
    └────────────────────────────────┘
         ↓
    Hasil Komposit
         ↓
    Display Frontend + Export
```

## 📂 Struktur Project

```
intelview/
│
├── app.py                          # Flask application entry point
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment configuration template
├── yolov12n-face.pt               # YOLO face detection model
│
├── modules/                        # Core Python modules
│   ├── audio/
│   │   └── audio_utils.py         # FFmpeg audio extraction
│   ├── detection/
│   │   ├── people_detector.py     # YOLO + MotPy people tracking
│   │   └── eye_tracking.py        # MediaPipe eye gaze detection
│   ├── stt/
│   │   └── stt_utils.py           # Whisper speech-to-text
│   ├── llm/
│   │   └── llm_utils.py           # Gemini evaluation & question matching
│   ├── pipeline/
│   │   └── analyzer.py            # Main async pipeline orchestrator
│   └── utils/
│       └── eye_utils.py           # Drawing utilities
│
├── templates/
│   └── index.html                 # Main web interface
│
└── static/
    ├── css/
    │   └── style.css              # Styling
    ├── js/
    │   └── app.js                 # Frontend logic
    └── images/
        └── logo.png               # Application logo
```

## 🛠️ Teknologi yang Digunakan

### Backend
- **Python 3.x** - Bahasa pemrograman utama
- **Flask 3.1.2 [async]** - Web framework dengan async support
- **Flask-CORS 6.0.1** - Cross-origin resource sharing

### AI/ML Models
- **OpenAI Whisper** (small model) - Speech recognition
- **YOLO12n-Face** - Face detection dan tracking
- **Google Gemini 2.5 Flash** - LLM evaluation dengan JSON output
- **MediaPipe 0.10.14** - Face mesh dan iris tracking

### Computer Vision
- **OpenCV 4.11.0.86** - Video processing
- **Ultralytics 8.3.229** - YOLO model inference
- **MotPy 0.0.10** - Multi-object tracking
- **NumPy 1.26.4** - Numerical operations

### Media Processing
- **ffmpeg-python 0.2.0** - Audio extraction dari video

## 🚀 Instalasi dan Setup

### 1. Prerequisites
- Python 3.8 atau lebih tinggi
- FFmpeg (untuk audio extraction)
- Google API Key untuk Gemini AI

### 2. Clone Repository
```bash
git clone https://github.com/zennn08/intelview.git
cd intelview
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
Buat file `.env` berdasarkan `.env.example`:
```bash
cp .env.example .env
```

Edit file `.env` dan tambahkan API key Anda:
```
GOOGLE_API_KEY=your_google_api_key_here
FLASK_ENV=production
PORT=5000
```

### 5. Jalankan Aplikasi
```bash
python app.py
```

Aplikasi akan berjalan di `http://0.0.0.0:5000`

## 📖 Cara Penggunaan

### 1. Upload Video
- Klik tombol "Add Video Entry" untuk menambah video baru
- Pilih file video wawancara (format: MP4, AVI, MOV, dll)
- Masukkan pertanyaan yang diajukan (opsional)

### 2. Analisis
- Klik tombol "Analyze Videos" untuk memulai proses analisis
- Tunggu hingga proses selesai (durasi tergantung panjang video)

### 3. Lihat Hasil
Hasil analisis mencakup:
- **Transcript** - Transkripsi lengkap dari jawaban
- **Score** - Nilai 0-4 berdasarkan rubrik
- **Reasoning** - Penjelasan penilaian
- **Feedback** - Saran konstruktif untuk perbaikan
- **Cheating Detection**
  - People Detected: Jumlah orang terdeteksi
  - Eye Tracking: Status gerakan mata
- **Confidence Metrics**
  - Overall Confidence
  - Acoustic Confidence
  - People Confidence
  - Eye Confidence

### 4. Export Hasil
- **Export to PDF** - Download hasil dalam format PDF
- **Export to JSON** - Download data mentah dalam format JSON

## 📊 Sistem Penilaian

### Formula Confidence Score
```
Final Score = 0.2 × acoustic_confidence
            + 0.4 × people_confidence
            + 0.4 × eye_confidence
```

Dimana:
- **acoustic_confidence** = 1 - rata-rata(no_speech_prob)
- **people_confidence** = single_person_frames / total_frames
- **eye_confidence** = 1 - (flagged_frames / frames_with_face)

### Rubrik Penilaian (0-4)
- **4 (Excellent)** - Jawaban lengkap, akurat, dengan contoh
- **3 (Good)** - Jawaban solid dengan minor gaps
- **2 (Fair)** - Jawaban parsial, kurang detail
- **1 (Poor)** - Jawaban sangat terbatas
- **0 (Insufficient)** - Tidak menjawab atau tidak relevan

### Bank Pertanyaan
Platform memiliki 5 pertanyaan pre-defined terkait TensorFlow:
1. TensorFlow basics dan use cases
2. Neural network training process
3. Overfitting dan regularization
4. TensorFlow deployment strategies
5. Recurrent Neural Networks (RNN)

Sistem akan mencocokkan pertanyaan user dengan bank pertanyaan (threshold 65% similarity) untuk menggunakan rubrik spesifik.

## 🔍 Deteksi Kecurangan

### People Detection
- Menggunakan YOLO12n-Face + MotPy tracking
- Deteksi setiap 4 frame untuk efisiensi
- Validasi track minimum 0.8 detik
- **Flagged**: Ketika >1 orang terdeteksi dalam periode signifikan

### Eye Tracking
- MediaPipe Face Mesh dengan iris refinement
- Gaze ratio estimation (posisi iris dalam batas mata)
- Smoothing 7-frame untuk mengurangi false positive
- Threshold: Left <0.25, Right >0.75
- **Flagged**: Ketika pandangan di luar threshold selama 0.5+ detik

## ⚡ Optimasi Performa

- **Async Processing** - I/O-bound tasks berjalan paralel
- **Frame Skipping** - Proses setiap 4 frame untuk people detection
- **Resolution Downscaling** - 640x360 untuk deteksi lebih cepat
- **Model Caching** - Whisper model dimuat sekali
- **Temporary File Cleanup** - Auto-cleanup setelah processing

## 🔧 Konfigurasi

### People Detection
Dalam `modules/detection/people_detector.py`:
```python
detection_interval = 4        # Proses setiap 4 frame
min_track_validation = 0.8    # Track valid minimum 0.8 detik
target_resolution = (640, 360) # Resolusi untuk deteksi
```

### Eye Tracking
Dalam `modules/detection/eye_tracking.py`:
```python
smoothing_window = 7          # Window untuk smoothing
threshold_duration = 0.5      # Durasi minimum untuk flag (detik)
left_threshold = 0.25         # Threshold pandangan kiri
right_threshold = 0.75        # Threshold pandangan kanan
```

### Whisper Model
Dalam `modules/stt/stt_utils.py`:
```python
model_size = "small"          # Options: tiny, base, small, medium, large
language = "english"          # Bahasa transkripsi
```

## 📝 API Endpoints

### POST `/analyze`
Endpoint utama untuk analisis video.

**Request:**
```json
{
  "videos": [File],           // Array of video files
  "questions": ["Question"]   // Array of questions (optional)
}
```

**Response:**
```json
{
  "results": [
    {
      "video_name": "interview.mp4",
      "question": "Explain TensorFlow",
      "transcript": "...",
      "evaluation": {
        "score": 3,
        "reasoning": "...",
        "feedback": "...",
        "cheating_detected": false
      },
      "people_detected": 1,
      "eye_tracking_status": "OK",
      "confidence": {
        "overall": 0.85,
        "acoustic": 0.92,
        "people": 1.0,
        "eye": 0.78
      },
      "processing_time": "15.3 seconds"
    }
  ],
  "total_time": "15.3 seconds"
}
```

## 🐛 Troubleshooting

### Video tidak bisa diproses
- Pastikan format video didukung (MP4, AVI, MOV)
- Pastikan FFmpeg terinstall dengan benar
- Cek ukuran file tidak terlalu besar

### Error: "GOOGLE_API_KEY not found"
- Pastikan file `.env` ada di root directory
- Pastikan `GOOGLE_API_KEY` sudah di-set dengan benar

### Model YOLO tidak ditemukan
- Pastikan file `yolov12n-face.pt` ada di root directory
- Download dari repository jika hilang

### Transcription gagal
- Cek audio dalam video ada dan jelas
- Pastikan OpenAI Whisper terinstall dengan benar
- Coba gunakan model size yang lebih kecil (tiny/base)

## 🤝 Kontribusi

Kontribusi selalu welcome! Silakan:
1. Fork repository
2. Buat branch fitur (`git checkout -b feature/AmazingFeature`)
3. Commit perubahan (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request

## 📄 License

Project ini untuk keperluan akademis dan pembelajaran.

## 👥 Tim Pengembang

Dikembangkan oleh **A25-CS368**
- Akhlaqul Muhammad Fadwa - M308D5Y0131: [https://github.com/zennn08](https://github.com/zennn08)
- Aprizal - M559D5Y0250: [https://github.com/aprizal543](https://github.com/aprizal543)
- M. Sohibbal - M308D5Y1039: [https://github.com/Sohibbal](https://github.com/Sohibbal)

## 📞 Kontak & Support

Untuk pertanyaan atau dukungan:
- Buat issue di [GitHub Issues](https://github.com/zennn08/intelview/issues)

## 🙏 Acknowledgments

- OpenAI untuk Whisper model
- Google untuk Gemini AI
- Ultralytics untuk YOLO framework
- MediaPipe untuk face mesh technology
- Flask community untuk dokumentasi yang excellent

---

**INTELVIEW** - Transforming Interview Assessment with AI
