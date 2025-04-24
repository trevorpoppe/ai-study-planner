from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import re
import os
import openai
from dotenv import load_dotenv
from timer import SessionTimer

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# FastAPI app
app = FastAPI()

# Allow frontend to call API (for local testing with HTML)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to ["http://localhost:5500"] later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (e.g., study-timer.html)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_home():
    return FileResponse(os.path.join("static", "study-timer.html"))

# Request body model
class UserInput(BaseModel):
    message: str

# In-memory timer instance
global_timer = None

# Schedule generator
def build_schedule(study_duration, break_duration, cycles):
    schedule = []
    for i in range(cycles):
        schedule.append(("study", study_duration))
        if i < cycles - 1:
            schedule.append(("break", break_duration))
    return schedule

# Regex-based fallback parser
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

# GPT-powered parser (optional)
def gpt_parse_preferences(message: str) -> dict:
    prompt = f"""Extract study preferences from the message below. Return as JSON with keys:
- study_duration (in minutes)
- break_duration (in minutes)
- cycles (number of sessions)

Message: \"{message}\"
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
        return eval(content)  # Replace with json.loads() if needed
    except Exception:
        raise ValueError("Failed to parse response from OpenAI.")

@app.post("/gpt-parse")
def gpt_parse_input(user_input: UserInput):
    try:
        prefs = gpt_parse_preferences(user_input.message)
        return prefs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Timer control endpoints
@app.post("/start-timer")
def start_timer(user_input: UserInput, background_tasks: BackgroundTasks):
    global global_timer
    try:
        prefs = parse_input(user_input)
        if prefs["status"] == "incomplete":
            return prefs
        schedule = build_schedule(
            prefs["study_duration"],
            prefs["break_duration"],
            prefs["cycles"]
        )
        global_timer = SessionTimer(schedule)
        background_tasks.add_task(global_timer.start)
        return {"message": "Timer started", "schedule": schedule}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/stop-timer")
def stop_timer():
    if global_timer:
        global_timer.stop()
        return {"message": "Timer stopped"}
    raise HTTPException(status_code=404, detail="No active timer")

@app.get("/status")
def get_status():
    if global_timer:
        return global_timer.status()
    return {"message": "No timer running"}
