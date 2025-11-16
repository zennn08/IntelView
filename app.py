from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from modules.pipeline.analyzer import analyze_video_pipeline
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

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

if __name__ == "__main__":
    app.run(port=5000, debug=True, threaded=False)