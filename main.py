from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import re
import os
import openai
from dotenv import load_dotenv
from timer import SessionTimer

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ TEMPORARY: Check if key loaded
print("OPENAI API KEY:", openai.api_key)  # Remove this line after confirming!

if not openai.api_key:
    raise RuntimeError("OpenAI API key not found. Please set it in the .env file.")

# FastAPI app
app = FastAPI()

# Input model
class UserInput(BaseModel):
    message: str

# In-memory timer instance
global_timer = None

# Build session schedule from prefs
def build_schedule(study_duration, break_duration, cycles):
    schedule = []
    for i in range(cycles):
        schedule.append(("study", study_duration))
        if i < cycles - 1:
            schedule.append(("break", break_duration))
    return schedule

# Regex parsing with fallback for missing fields
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
        cycles = int(c
