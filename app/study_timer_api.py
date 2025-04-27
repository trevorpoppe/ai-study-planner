from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.core import parse_study_preferences, build_schedule
from app.timer import SessionTimer
from app.config import openai

from pydantic import BaseModel

router = APIRouter()

global_timer = None

class UserInput(BaseModel):
    message: str

@router.post("/parse")
def parse_input(user_input: UserInput):
    return parse_study_preferences(user_input.message)

@router.post("/start-timer")
def start_timer(user_input: UserInput, background_tasks: BackgroundTasks):
    global global_timer
    prefs = parse_study_preferences(user_input.message)
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

@router.post("/stop-timer")
def stop_timer():
    if global_timer:
        global_timer.stop()
        return {"message": "Timer stopped"}
    raise HTTPException(status_code=404, detail="No active timer")

@router.get("/status")
def get_status():
    if global_timer:
        return global_timer.status()
    return {"message": "No timer running"}
