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
You are an AI exam evaluator.

Transcript:
{transcript}

Cheating Events (People Detector):
{json.dumps(people_data, indent=2)}

Cheating Events (Eye Tracking):
{json.dumps(eye_data or {}, indent=2)}

Return JSON:
- score
- reason
- cheating_indication
- feedback
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