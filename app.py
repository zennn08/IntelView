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
    if "video" not in request.files:
        return jsonify({"error": "no_video_uploaded"}), 400

    result = await analyze_video_pipeline(request.files["video"])
    return jsonify(result), 200


port = int(os.getenv("PORT", 5000))
app.run(host="127.0.0.1", port=port, debug=True, threaded=False)