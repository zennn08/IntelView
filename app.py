from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from modules.pipeline.analyzer import analyze_video_pipeline

import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['MEDIAPIPE_DISABLE_LOG'] = '1'

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU")
warnings.filterwarnings("ignore", message="SymbolDatabase.GetPrototype")
warnings.filterwarnings("ignore", category=UserWarning)

import absl.logging
absl.logging.set_verbosity(absl.logging.ERROR)

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')
CORS(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
async def analyze():
    # Support both single and multiple video uploads
    video_files = request.files.getlist("video")
    questions = request.form.getlist("question")

    if not video_files or len(video_files) == 0:
        return jsonify({"error": "no_video_uploaded"}), 400

    # If single video, return single result (backward compatibility)
    if len(video_files) == 1:
        question = questions[0] if questions else ""
        result = await analyze_video_pipeline(video_files[0], question)
        return jsonify(result), 200

    # If multiple videos, process all and return array
    import asyncio
    results = []
    for i, video_file in enumerate(video_files):
        question = questions[i] if i < len(questions) else ""
        result = await analyze_video_pipeline(video_file, question)
        result["video_index"] = i
        result["video_name"] = video_file.filename
        result["question"] = question
        results.append(result)

    return jsonify({
        "multiple": True,
        "count": len(results),
        "results": results
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
