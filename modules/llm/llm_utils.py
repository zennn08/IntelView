import json
import logging
import os
import time
import google.generativeai as genai
from typing import Optional

logger = logging.getLogger(__name__)

# Load API key from environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set. Please configure it in .env file.")

genai.configure(api_key=GOOGLE_API_KEY)

# Gunakan temperature rendah untuk konsistensi
gemini = genai.GenerativeModel(
    "gemini-2.5-flash",
    generation_config=genai.GenerationConfig(
        temperature=0.1,        # Lebih deterministik
        top_p=0.95,
        response_mime_type="application/json"  # Force JSON output
    )
)

# Schema untuk validasi output
EXPECTED_SCHEMA = {
    "score": int,
    "reason": str,
    "cheating_indication": bool,
    "cheating_reason": str,
    "feedback": str
}


def clean_json(text: str) -> str:
    """Bersihkan markdown wrapper dari JSON response."""
    text = text.strip()
    
    # Handle ```json ... ``` wrapper
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    
    return text.strip()


def validate_and_fix_response(data: dict) -> dict:
    """Validasi dan fix response agar sesuai schema."""
    result = {}
    
    # Score: pastikan integer 0-4
    score = data.get("score", 0)
    if isinstance(score, str):
        try:
            score = int(score)
        except:
            score = 0
    result["score"] = max(0, min(4, score))
    
    # Reason: pastikan string
    result["reason"] = str(data.get("reason", "No reason provided"))
    
    # Cheating indication: pastikan boolean
    cheating = data.get("cheating_indication", False)
    if isinstance(cheating, str):
        cheating = cheating.lower() in ("true", "yes", "1")
    result["cheating_indication"] = bool(cheating)
    
    # Cheating reason: pastikan string
    result["cheating_reason"] = str(data.get("cheating_reason", "No cheating indicated"))
    
    # Feedback: pastikan string
    result["feedback"] = str(data.get("feedback", "No feedback provided"))
    
    return result


def evaluate_exam(
    transcript: str,
    people_data: dict,
    eye_data: Optional[dict] = None,
    max_retries: int = 2
) -> dict:
    """
    Evaluasi exam dengan LLM.
    
    Args:
        transcript: Transcript dari video
        people_data: Data dari people detector
        eye_data: Data dari eye tracker (optional)
        max_retries: Jumlah retry jika gagal
    
    Returns:
        dict dengan score, reason, cheating_indication, cheating_reason, feedback
    """
    
    prompt = f"""You are an AI exam evaluator for a video-based interview assessment.
Evaluate the candidate's transcript using the scoring rubric below.

SCORING RUBRIC (0-4 points):

QUESTION 1 — Specific Challenges During Certification
4 = Detailed challenges + clear explanation of how they were overcome  
3 = Mentions one specific challenge + basic solution  
2 = Mentions general challenge without details  
1 = Minimal, vague response  
0 = No answer or irrelevant

QUESTION 2 — Transfer Learning Experience
4 = Detailed personal experience + specific examples + clear benefits
3 = Describes experience + examples + explains benefits basically  
2 = Mentions transfer learning but minimal details  
1 = Very vague  
0 = No answer

QUESTION 3 — Complex TensorFlow Model & Ensuring Accuracy/Efficiency
4 = Detailed architecture + specific steps (preprocessing, optimization, regularization, tuning)  
3 = Model described with some details + explains steps  
2 = Only mentions TensorFlow model with minimal details  
1 = Very vague  
0 = No answer

QUESTION 4 — Dropout Implementation & Its Effect
4 = Explains implementation + examples + clearly explains training effect
3 = Explains dropout but lacks depth  
2 = General mention of dropout or overfitting only  
1 = Very vague  
0 = No answer

QUESTION 5 — Building CNN in TensorFlow for Image Classification
4 = Step-by-step: data loading, preprocessing, conv layers, pooling, activation, compilation, training, evaluation
3 = Describes process with key steps but may omit some details
2 = General response with limited details  
1 = Minimal or vague  
0 = No answer

INPUTS:

<transcript>
{transcript}
</transcript>

<people_detector>
{json.dumps(people_data, indent=2)}
</people_detector>

<eye_tracking>
{json.dumps(eye_data or {}, indent=2)}
</eye_tracking>

INSTRUCTIONS:
1. Score the transcript 0-4 based on rubric
2. Check cheating_detected from people_detector and eye_tracking
3. Return ONLY valid JSON with this exact structure:

{{"score": <0-4>, "reason": "<why this score>", "cheating_indication": <true/false>, "cheating_reason": "<if cheating, explain when and why; otherwise say no cheating indicated>", "feedback": "<constructive feedback>"}}"""

    # Fallback response
    people_flag = people_data.get("cheating_detected", False) if isinstance(people_data, dict) else False
    eye_flag = eye_data.get("cheating_detected", False) if isinstance(eye_data, dict) else False
    
    fallback = {
        "score": 0,
        "reason": "LLM evaluation failed",
        "cheating_indication": people_flag or eye_flag,
        "cheating_reason": "Unable to evaluate cheating via LLM" if (people_flag or eye_flag) else "No cheating indicated",
        "feedback": "Evaluation failed, please retry"
    }

    for attempt in range(max_retries + 1):
        try:
            time_start = time.time()
            
            resp = gemini.generate_content(prompt)
            text = getattr(resp, "text", resp.candidates[0].content.parts[0].text)
            cleaned = clean_json(text)
            
            time_end = time.time()
            execution_time = round(time_end - time_start, 3)
            print(f"LLM execution time (attempt {attempt + 1}): {execution_time}s")
            
            # Parse JSON
            data = json.loads(cleaned)
            
            # Validate dan fix
            result = validate_and_fix_response(data)
            result["execution_time"] = execution_time
            
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
            if attempt < max_retries:
                continue
                
        except Exception as e:
            logger.error(f"LLM error (attempt {attempt + 1}): {e}")
            if attempt < max_retries:
                continue
    
    return fallback