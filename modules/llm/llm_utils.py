import json
import logging
import time
import google.generativeai as genai

logger = logging.getLogger(__name__)

genai.configure(api_key="AIzaSyDExQLOSOp9OBEkRW3NL71PfnL5cHHzVPo")
gemini = genai.GenerativeModel("gemini-2.5-flash")

def clean_json(text):
    if text.startswith("```"):
        text = text.strip().strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    return text

def evaluate_exam(transcript, people_data, eye_data=None):
    prompt = f"""
    You are an AI exam evaluator for a video-based interview assessment.
    Your task is to evaluate the candidate’s transcript strictly using the scoring rubric below.
    You must follow the rubric EXACTLY.

    GENERAL INSTRUCTIONS
    - Score each question from 0–4.
    - Never give half points.
    - Use the definition of each score exactly as stated.
    - If the candidate misunderstands the question, deduct points accordingly.
    - Provide explanations based only on the transcript content.
    - Consider cheating indicators (people detector & eye tracking) only for 'cheating_indication'.
    - Output must be **valid JSON only**.

    RUBRIC SUMMARY
    QUESTION 1 — Specific Challenges During Certification
    4 = Detailed challenges + clear explanation of how they were overcome  
    3 = Mentions one specific challenge + basic solution  
    2 = Mentions general challenge without details  
    1 = Minimal, vague response  
    0 = No answer or irrelevant answer  

    QUESTION 2 — Transfer Learning Experience
    4 = Detailed personal experience + specific examples + clear benefits + strong understanding  
    3 = Describes experience + examples + explains benefits basically  
    2 = Mentions transfer learning but with minimal details  
    1 = Very vague personal experience  
    0 = No answer  

    QUESTION 3 — Complex TensorFlow Model & Ensuring Accuracy/Efficiency
    4 = Detailed architecture + specific steps (preprocessing, optimization, regularization, tuning)  
    3 = Model described with some details + explains steps but shallow  
    2 = Only mentions TensorFlow model with minimal details  
    1 = Very vague explanation  
    0 = No answer  

    QUESTION 4 — Dropout Implementation & Its Effect
    4 = Explains how to implement dropout + gives examples + clearly explains training effect + strong ML understanding  
    3 = Explains dropout but lacks depth  
    2 = General mention of dropout or overfitting only  
    1 = Very vague  
    0 = No answer

    QUESTION 5 — Building a Convolutional Neural Network (CNN) in TensorFlow for Image Classification
    4 = Provides a detailed, step-by-step explanation; covers all key components such as data loading, preprocessing, convolutional layers, pooling, activation functions, compilation (loss function & optimizer), training process, and performance evaluation; may include examples or specific TensorFlow functions; demonstrates strong understanding.  
    3 = Describes the CNN building process with some specifics; includes key steps such as preprocessing, defining architecture, compiling, and training; may omit some details but shows reasonable understanding.  
    2 = Gives a general response with limited details; may mention main steps but lacks depth or key components.  
    1 = Minimal or vague response; unclear steps or very superficial.  
    0 = No answer or completely irrelevant answer.

    INPUTS

    Transcript:
    {transcript}

    Cheating Events (People Detector):
    {json.dumps(people_data, indent=2)}

    Cheating Events (Eye Tracking):
    {json.dumps(eye_data or {}, indent=2)}

    OUTPUT FORMAT (STRICT JSON)
    Return a JSON with:
    "score": integer 0-4,
    "reason": "Explain why this score was given based on the rubric.",
    "cheating_indication": true/false,
    "cheating_reason": "If cheating_indication true, describe reason of cheating and when the cheating indication occurs, if cheating_indication false return teks no cheating indicated with variant style"
    "feedback": "Constructive feedback to help improve the answer, based on transcript relevance and cheating behavior if detected."

    DO NOT RETURN MARKDOWN.
    DO NOT RETURN ANYTHING EXCEPT PURE JSON.
    """

    try:
        time_start = time.time()
        resp = gemini.generate_content(prompt)
        text = getattr(resp, "text", resp.candidates[0].content.parts[0].text)
        cleaned = clean_json(text)
        time_end = time.time()
        execution_time = round(time_end - time_start, 3)
        print("Time execution llm : " , execution_time)
        return json.loads(cleaned)
    except:
        people_flag = people_data.get("cheating_detected", False) if isinstance(people_data, dict) else False
        eye_flag = eye_data.get("cheating_detected", False) if isinstance(eye_data, dict) else False
        return {
            "score": 0,
            "reason": "LLM evaluation error",
            "cheating_indication": people_flag or eye_flag,
            "feedback": "LLM failed"
        }