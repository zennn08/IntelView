"""
LLM Evaluation Module menggunakan Google Gemini

Module ini menghandle evaluasi transcript wawancara menggunakan Gemini 2.5 Flash.
Fitur utama:
1. Question Bank: 5 pertanyaan pre-defined dengan rubrik spesifik
2. Intelligent Question Matching: Cocokkan pertanyaan user dengan question bank
3. Rubric-based Scoring: System penilaian 0-4 berdasarkan rubrik
4. Cheating Assessment: Pertimbangkan hasil people & eye detection
5. Constructive Feedback: Saran perbaikan yang actionable

Konfigurasi:
- Model: gemini-2.5-flash (fast & cost-effective)
- Temperature: 0.1 (lebih deterministik, less creative)
- Output: JSON-only mode untuk parsing lebih reliable
"""

import json
import logging
import os
import time
import google.generativeai as genai
from typing import Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Load Google API Key dari environment variable
# Key ini diperlukan untuk authenticate dengan Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set. Please configure it in .env file.")

# Configure Gemini SDK dengan API key
genai.configure(api_key=GOOGLE_API_KEY)

# ============================================
# QUESTION BANK dengan Rubrik Spesifik
# ============================================
# Bank berisi 5 pertanyaan terkait TensorFlow certification
# Setiap pertanyaan memiliki rubrik detail untuk scoring 0-4

QUESTION_BANK = {
    "q1": {
        "question": "Can you share any specific challenges you faced while working on certification and how you overcame them?",
        "rubric": """4 = Detailed challenges + clear explanation of how they were overcome
3 = Mentions one specific challenge + basic solution
2 = Mentions general challenge without details
1 = Minimal, vague response
0 = No answer or irrelevant"""
    },
    "q2": {
        "question": "Can you describe your experience with transfer learning in TensorFlow? How did it benefit your projects?",
        "rubric": """4 = Detailed personal experience + specific examples + clear benefits
3 = Describes experience + examples + explains benefits basically
2 = Mentions transfer learning but minimal details
1 = Very vague
0 = No answer"""
    },
    "q3": {
        "question": "Describe a complex TensorFlow model you have built and the steps you took to ensure its accuracy and efficiency.",
        "rubric": """4 = Detailed architecture + specific steps (preprocessing, optimization, regularization, tuning)
3 = Model described with some details + explains steps
2 = Only mentions TensorFlow model with minimal details
1 = Very vague
0 = No answer"""
    },
    "q4": {
        "question": "Explain how to implement dropout in a TensorFlow model and the effect it has on training.",
        "rubric": """4 = Explains implementation + examples + clearly explains training effect
3 = Explains dropout but lacks depth
2 = General mention of dropout or overfitting only
1 = Very vague
0 = No answer
0 = Unanswered or irrelevant response"""
    },
    "q5": {
        "question": "Describe the process of building a convolutional neural network (CNN) using TensorFlow for image classification.",
        "rubric": """4 = Step-by-step: data loading, preprocessing, conv layers, pooling, activation, compilation, training, evaluation
3 = Describes process with key steps but may omit some details
2 = General response with limited details
1 = Minimal or vague
0 = No answer"""
    }
}


def find_matching_question(user_question: str) -> Optional[dict]:
    """
    Cari pertanyaan yang cocok dari question bank berdasarkan text similarity.

    Menggunakan SequenceMatcher untuk menghitung similarity ratio antara
    pertanyaan user dengan setiap pertanyaan dalam question bank.

    Args:
        user_question (str): Pertanyaan yang diinput user

    Returns:
        Optional[dict]: Dictionary dengan data pertanyaan yang match, atau None jika
                       tidak ada yang match dengan threshold >= 65%
                       Struktur return:
                       {
                           "id": str,              # Question ID (q1-q5)
                           "question": str,        # Full question text
                           "rubric": str,          # Scoring rubric
                           "match_score": float    # Similarity score 0-1
                       }

    Example:
        >>> match = find_matching_question("Explain dropout in TensorFlow")
        >>> print(match["id"])
        q4
        >>> print(match["match_score"])
        0.78
    """
    # Validasi input
    if not user_question or not user_question.strip():
        return None

    user_question_lower = user_question.lower().strip()
    best_match = None
    best_score = 0.0
    threshold = 0.65  # Minimum similarity threshold (65%)

    # Iterate semua questions dalam bank
    for q_id, q_data in QUESTION_BANK.items():
        # Calculate text similarity menggunakan SequenceMatcher
        # Ratio berkisar 0-1, dimana 1 = exact match
        text_similarity = SequenceMatcher(None, user_question_lower, q_data["question"].lower()).ratio()

        # Update best match jika similarity lebih tinggi dan >= threshold
        if text_similarity > best_score and text_similarity >= threshold:
            best_score = text_similarity
            best_match = {
                "id": q_id,
                "question": q_data["question"],
                "rubric": q_data["rubric"],
                "match_score": text_similarity
            }

    return best_match


# ============================================
# Gemini Model Configuration
# ============================================
# Temperature rendah (0.1) untuk output yang lebih konsisten dan deterministik
# response_mime_type="application/json" memaksa output dalam format JSON
gemini = genai.GenerativeModel(
    "gemini-2.5-flash",
    generation_config=genai.GenerationConfig(
        temperature=0.1,        # Lower = more deterministic
        top_p=0.95,
        response_mime_type="application/json"  # Force JSON output
    )
)

# Expected JSON schema untuk validasi
EXPECTED_SCHEMA = {
    "score": int,
    "reason": str,
    "cheating_indication": bool,
    "cheating_reason": str,
    "feedback": str
}


def clean_json(text: str) -> str:
    """
    Bersihkan markdown code block wrapper dari JSON response.

    Kadang LLM mengembalikan JSON dalam markdown code block seperti:
    ```json
    {"key": "value"}
    ```

    Fungsi ini menghapus wrapper tersebut untuk parsing yang lebih bersih.

    Args:
        text (str): Raw response text dari LLM

    Returns:
        str: Cleaned JSON text tanpa markdown wrapper
    """
    text = text.strip()

    # Handle ```json ... ``` wrapper
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove lines yang mengandung ``` marker
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    return text.strip()


def validate_and_fix_response(data: dict) -> dict:
    """
    Validasi dan perbaiki response LLM agar sesuai expected schema.

    Fungsi ini ensure bahwa setiap field memiliki tipe data yang benar
    dan nilai yang valid, bahkan jika LLM mengembalikan format yang sedikit berbeda.

    Args:
        data (dict): Raw parsed JSON dari LLM response

    Returns:
        dict: Validated dan fixed response dengan struktur:
            {
                "score": int (0-4),
                "reason": str,
                "cheating_indication": bool,
                "cheating_reason": str,
                "feedback": str
            }
    """
    result = {}

    # Score: pastikan integer 0-4
    score = data.get("score", 0)
    if isinstance(score, str):
        try:
            score = int(score)
        except:
            score = 0
    # Clamp ke range 0-4
    result["score"] = max(0, min(4, score))

    # Reason: pastikan string, fallback jika tidak ada
    result["reason"] = str(data.get("reason", "No reason provided"))

    # Cheating indication: pastikan boolean
    cheating = data.get("cheating_indication", False)
    if isinstance(cheating, str):
        # Parse string representation of boolean
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
    question: str = "",
    max_retries: int = 2
) -> dict:
    """
    Evaluasi exam transcript menggunakan Gemini LLM dengan rubric-based scoring.

    Workflow:
    1. Match user question dengan question bank (jika ada)
    2. Build prompt dengan rubrik yang sesuai
    3. Kirim ke Gemini untuk evaluasi
    4. Parse dan validate response
    5. Retry jika gagal (max 2 retries)

    Scoring Logic:
    - Jika question match dengan bank → gunakan rubrik spesifik
    - Jika question provided tapi tidak match → gunakan generic rubric
    - Jika tidak ada question → evaluate berdasarkan semua 5 questions

    Args:
        transcript (str): Full transcript dari speech-to-text
        people_data (dict): Results dari people detector (cheating flags, dll)
        eye_data (Optional[dict]): Results dari eye tracker (cheating flags, dll)
        question (str): Pertanyaan yang diajukan dalam interview (optional)
        max_retries (int): Maximum retry attempts jika LLM call gagal

    Returns:
        dict: Evaluation result dengan struktur:
            {
                "score": int (0-4),
                "reason": str,
                "cheating_indication": bool,
                "cheating_reason": str,
                "feedback": str,
                "execution_time": float,
                "question_match": dict (jika question provided)
            }

    Example:
        >>> result = evaluate_exam(
        ...     transcript="TensorFlow is a framework...",
        ...     people_data={"cheating_detected": False},
        ...     question="Explain TensorFlow"
        ... )
        >>> print(result["score"])
        3
    """

    # ============================================
    # Step 1: Question Matching
    # ============================================
    # Try to find matching question dari question bank
    matched_question = find_matching_question(question) if question else None

    # ============================================
    # Step 2: Build Rubric Section
    # ============================================
    # Rubric section berbeda tergantung apakah question match atau tidak

    if matched_question:
        # Case 1: Question matched dengan question bank
        # Gunakan rubrik spesifik dari question yang match
        logger.info(f"Question matched with {matched_question['id']} (score: {matched_question['match_score']:.2f})")

        rubric_section = f"""INTERVIEW QUESTION ASKED:
"{question}"

STANDARD QUESTION (for reference):
"{matched_question['question']}"

SCORING RUBRIC (0-4 points):
{matched_question['rubric']}

IMPORTANT: Evaluate the candidate's response to the INTERVIEW QUESTION ASKED above, using the rubric criteria.
The standard question is provided for context to help you understand the expected topic and depth of the answer."""

    else:
        # Case 2: User provided question tapi tidak match dengan bank
        # Gunakan generic rubrik yang universal
        logger.info("No matching question found, using generic rubric")
        rubric_section = f"""INTERVIEW QUESTION:
{question}

SCORING RUBRIC (0-4 points):
4 = Comprehensive and very clear response with detailed explanation, specific examples, and demonstrates strong understanding
3 = Specific explanation with basic understanding, includes some examples but may lack depth
2 = General response with limited details, shows basic understanding but lacks specificity
1 = Minimal or vague response, very limited details
0 = No answer or completely irrelevant response"""

    # ============================================
    # Step 3: Build Complete Prompt
    # ============================================
    prompt = f"""You are an AI exam evaluator for a video-based interview assessment.
Evaluate the candidate's transcript using the scoring rubric below.

{rubric_section}

INPUTS:

<candidate_transcript>
{transcript}
</candidate_transcript>

<people_detector_results>
{json.dumps(people_data, indent=2)}
</people_detector_results>

<eye_tracking_results>
{json.dumps(eye_data or {}, indent=2)}
</eye_tracking_results>

EVALUATION INSTRUCTIONS:
1. Carefully read the candidate's transcript and understand what they are trying to communicate
2. Score the transcript 0-4 based on the rubric criteria above
3. Ensure your scoring is fair and unbiased - focus on the content quality, not the delivery style
4. Check cheating_detected flags from people_detector and eye_tracking results
5. Provide detailed reasoning for your score
6. Give constructive, actionable feedback for improvement
7. Return ONLY valid JSON with this exact structure:

{{"score": <0-4>, "reason": "<detailed explanation of why you gave this score, referencing specific parts of the transcript>", "cheating_indication": <true/false>, "cheating_reason": "<if cheating detected, explain when (you MUST state the specific timestamp/moment (e.g., 'at 00:30') AND the specific behavior detected (e.g., 'multiple people detected')) and why; otherwise say 'No cheating indicated'>", "feedback": "<constructive, specific feedback on how the candidate can improve their response>"}}"""

    # ============================================
    # Fallback Response (jika LLM gagal)
    # ============================================
    # Prepare fallback response dengan cheating flags dari detectors
    people_flag = people_data.get("cheating_detected", False) if isinstance(people_data, dict) else False
    eye_flag = eye_data.get("cheating_detected", False) if isinstance(eye_data, dict) else False

    fallback = {
        "score": 0,
        "reason": "LLM evaluation failed",
        "cheating_indication": people_flag or eye_flag,
        "cheating_reason": "Unable to evaluate cheating via LLM" if (people_flag or eye_flag) else "No cheating indicated",
        "feedback": "Evaluation failed, please retry"
    }

    # ============================================
    # Step 4: Call Gemini API dengan Retry Logic
    # ============================================
    for attempt in range(max_retries + 1):
        try:
            time_start = time.time()

            # Call Gemini API
            resp = gemini.generate_content(prompt)
            print(prompt)
            text = getattr(resp, "text", resp.candidates[0].content.parts[0].text)
            cleaned = clean_json(text)

            # Track execution time
            time_end = time.time()
            execution_time = round(time_end - time_start, 3)
            print(f"LLM execution time (attempt {attempt + 1}): {execution_time}s")

            # Parse JSON response
            data = json.loads(cleaned)

            # Validate dan fix response untuk ensure schema compliance
            result = validate_and_fix_response(data)
            result["execution_time"] = execution_time

            # ============================================
            # Add Question Matching Metadata
            # ============================================
            if matched_question:
                result["question_match"] = {
                    "matched": True,
                    "question_id": matched_question["id"],
                    "standard_question": matched_question["question"],
                    "match_score": round(matched_question["match_score"], 2)
                }
            elif question:
                result["question_match"] = {
                    "matched": False,
                    "reason": "No matching question found in question bank"
                }

            return result

        except json.JSONDecodeError as e:
            # JSON parsing failed - retry jika masih ada attempt
            logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
            if attempt < max_retries:
                continue

        except Exception as e:
            # General error - retry jika masih ada attempt
            logger.error(f"LLM error (attempt {attempt + 1}): {e}")
            if attempt < max_retries:
                continue

    # Semua retry gagal - return fallback response
    return fallback
