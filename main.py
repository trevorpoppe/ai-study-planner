from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise RuntimeError("OpenAI API key not found. Please set it in the .env file.")

# FastAPI app
app = FastAPI()

# Input model
class UserInput(BaseModel):
    message: str

# Fallback-aware regex parser
@app.post("/parse")
def parse_input(user_input: UserInput):
    study_duration = break_duration = cycles = None

    study_match = re.search(r'study(?:\sfor)?\s*(\d+)\s*(?:minutes|min)', user_input.message, re.IGNORECASE)
    break_match = re.search(r'(?:breaks?|rest(?:\stime)?)\s*(?:for|of|:)?\s*(\d+)\s*(?:minutes|min)', user_input.message, re.IGNORECASE)
    cycle_match = re.search(r'(\d+)\s*(?:sessions?|cycles?)', user_input.message, re.IGNORECASE)

    if study_match:
        study_duration = int(study_match.group(1))
    if break_match:
        break_duration = int(break_match.group(1))
    if cycle_match:
        cycles = int(cycle_match.group(1))

    # Collect missing fields
    missing = []
    if not study_duration:
        missing.append("study_duration (in minutes)")
    if not break_duration:
        missing.append("break_duration (in minutes)")
    if not cycles:
        missing.append("cycles (number of study sessions)")

    if missing:
        return {
            "status": "incomplete",
            "message": "Missing required information.",
            "missing_fields": missing
        }

    return {
        "status": "complete",
        "study_duration": study_duration,
        "break_duration": break_duration,
        "cycles": cycles
    }

# GPT-based parser
def gpt_parse_preferences(message: str) -> dict:
    prompt = f"""Extract study preferences from the message below. Return as JSON with keys:
- study_duration (in minutes)
- break_duration (in minutes)
- cycles (number of sessions)

Message: "{message}"
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You extract structured data from user study planning messages."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    content = response['choices'][0]['message']['content']

    try:
        return eval(content)  # You can use json.loads() if content is strict JSON
    except Exception:
        raise ValueError("Failed to parse response from OpenAI.")

@app.post("/gpt-parse")
def gpt_parse_input(user_input: UserInput):
    try:
        prefs = gpt_parse_preferences(user_input.message)
        return prefs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
