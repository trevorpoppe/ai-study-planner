from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
import os
import json
from timer import SessionTimer
from dotenv import load_dotenv
from database import get_db
import openai
import csv
from io import StringIO

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_home():
    return FileResponse(os.path.join("static", "study-timer.html"))

class UserInput(BaseModel):
    message: str

global_timer = None

def extract_preferences(message: str):
    prompt = f"""
You are a natural language interpreter for study plans. Extract the following:
- "study_duration" in seconds
- "break_duration" in seconds
- "cycles" (number of sessions)

Only include the number of seconds (always convert minutes to seconds).
Only assign values based on their associated label — e.g. "study", "break", or "session".

For example:
- "Study 25 minutes with 5 min breaks for 4 sessions" → study_duration: 1500, break_duration: 300, cycles: 4
- "Study for 1 minute, 10 second break, 2 sessions" → study_duration: 60, break_duration: 10, cycles: 2

**If both “1 minute” and “10 second” are mentioned, treat them as separate values. Do not add them together unless clearly part of the same label.**

Output raw JSON only like this:
{{
  "study_duration": 1500,
  "break_duration": 300,
  "cycles": 4
}}

Do not include any explanation or formatting.

Prompt: "{message}"
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You extract structured data from natural language prompts. Respond with JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        content = response.choices[0].message['content'].strip()
        data = json.loads(content)

        return {
            "status": "complete",
            "study_duration": data["study_duration"],
            "break_duration": data["break_duration"],
            "cycles": data["cycles"]
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

def build_schedule(study_duration, break_duration, cycles):
    schedule = []
    for i in range(cycles):
        schedule.append(("study", study_duration))
        if i < cycles - 1:
            schedule.append(("break", break_duration))
    return schedule

@app.post("/start-timer")
def start_timer(user_input: UserInput):
    global global_timer

    if global_timer and global_timer.paused:
        global_timer.resume()
        return {"message": "Resumed"}

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
    global_timer.start()
    return {"message": "Timer started", "schedule": schedule}

@app.post("/stop-timer")
def stop_timer():
    global global_timer
    if global_timer:
        global_timer.stop()
        return {"message": "Timer stopped"}
    raise HTTPException(status_code=404, detail="No active timer")

@app.post("/pause-timer")
def pause_timer():
    global global_timer
    if global_timer and global_timer.running:
        global_timer.pause()
        return {"message": "Timer paused"}
    raise HTTPException(status_code=400, detail="No active timer")

@app.get("/status")
def get_status():
    global global_timer
    if global_timer and global_timer.running:
        return global_timer.status()
    return {"message": "No timer running"}

@app.get("/export")
def export_study_log():
    try:
        db = get_db()
        cursor = db.execute("SELECT * FROM study_logs")
        logs = cursor.fetchall()

        if not logs:
            return Response("No logs available.", media_type="text/plain")

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([col[0] for col in cursor.description])  # headers
        for row in logs:
            writer.writerow(row)
        output.seek(0)

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=study_log.csv"}
        )

    except Exception as e:
        print("Export error:", e)
        return Response(
            content=f"Internal Server Error\n\n{str(e)}",
            media_type="text/plain",
            status_code=500
        )
