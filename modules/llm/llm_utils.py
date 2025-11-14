import json
import logging
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

def evaluate_exam(transcript, people_data):
    prompt = f"""
You are an AI exam evaluator.

Transcript:
{transcript}

Cheating Events:
{json.dumps(people_data, indent=2)}

Return JSON:
- score
- reason
- cheating_indication
- feedback
"""

    try:
        resp = gemini.generate_content(prompt)
        text = getattr(resp, "text", resp.candidates[0].content.parts[0].text)
        cleaned = clean_json(text)
        return json.loads(cleaned)
    except:
        return {
            "score": 0,
            "reason": "LLM evaluation error",
            "cheating_indication": people_data.get("cheating_detected", False),
            "feedback": "LLM failed"
        }
