from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import re
import os
from dotenv import load_dotenv
from timer import SessionTimer

# Load environment variables
load_dotenv()

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

# Extract preferences using regex
def extract_preferences(message: str):
    study_match = re.search(r'study(?:\sfor)?\s*(\d+)\s*(?:minutes|min)', message, re.IGNORECASE)
    break_match = re.search(r'(?:breaks?|rest(?:\stime)?)\s*(?:for|of|:)?\s*(\d+)\s*(?:minutes|min)', message, re.IGNORECASE)
    cycle_match = re.search(r'(\d+)\s*(?:sessions?|cycles?)', message, re.IGNORECASE)

    study_duration = int(study_match.group(1)) if study_match else None
    break_duration = int(break_match.group(1)) if break_match else None
    cycles = int(cycle_match.group(1)) if cycle_match else None

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
        background_tasks.add_task(global_timer.start)
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
