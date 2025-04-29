from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from timer import SessionTimer
from dotenv import load_dotenv
import openai
import json

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# FastAPI app
app = FastAPI()

# Allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static HTML
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_home():
    return FileResponse(os.path.join("static", "study-timer.html"))

# Data model
class UserInput(BaseModel):
    message: str

# Global timer instance
global_timer = None

def extract_preferences(message: str):
    prompt = f"""
Extract the following values from this natural language prompt:
- study_duration in minutes (number only)
- break_duration in minutes (number only)
- cycles (number of sessions, just a number)

Respond with raw JSON only, like:
{{
  "study_duration": 25,
  "break_duration": 5,
  "cycles": 4
}}

Do not include any explanation, markdown, or extra formatting.

Prompt: "{message}"
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You extract structured data from natural language prompts. Respond with JSON only and no formatting or explanation."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        content = response.choices[0].message['content'].strip()
        data = json.loads(content)

        study_duration = data.get("study_duration")
        break_duration = data.get("break_duration")
        cycles = data.get("cycles")

        missing = []
        if not study_duration:
            missing.append("study_duration")
        if not break_duration:
            missing.append("break_duration")
        if not cycles:
            missing.append("cycles")

        return {
            "status": "complete" if not missing else "incomplete",
            "study_duration": study_duration,
            "break_duration": break_duration,
            "cycles": cycles,
            "missing_fields": missing
        }

    except Exception as e:
        print("OpenAI extraction error:", e)
        return {
            "status": "incomplete",
            "study_duration": None,
            "break_duration": None,
            "cycles": None,
            "missing_fields": ["study_duration", "break_duration", "cycles"],
            "error": str(e)
        }

# Build the session schedule
def build_schedule(study_duration, break_duration, cycles):
    schedule = []
    for i in range(cycles):
        schedule.append(("study", study_duration))
        if i < cycles - 1:
            schedule.append(("break", break_duration))
    return schedule

@app.post("/start-timer")
def start_timer(user_input: UserInput, background_tasks: BackgroundTasks):
    global global_timer
    try:
        prefs = extract_preferences(user_input.message)
        if prefs["status"] == "incomplete":
            return {
                "status": "incomplete",
                "message": "Missing required fields",
                "missing_fields": prefs["missing_fields"]
            }

        schedule = build_schedule(
            prefs["study_duration"],
            prefs["break_duration"],
            prefs["cycles"]
        )
        global_timer = SessionTimer(schedule)
        print("Schedule loaded:", schedule)
        global_timer.start()
        return {"message": "Timer started", "schedule": schedule}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/stop-timer")
def stop_timer():
    global global_timer
    if global_timer:
        global_timer.stop()
        return {"message": "Timer stopped"}
    raise HTTPException(status_code=404, detail="No active timer")

@app.get("/status")
def get_status():
    if global_timer:
        return global_timer.status()
    return {"message": "No timer running"}
